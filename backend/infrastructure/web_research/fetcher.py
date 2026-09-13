"""
YourQuantum — Safe Web Fetcher (Phase C5)
Hardened HTTP document fetcher with strict SSRF defenses, size bounds, and SHA-256 content hashing.
"""
from __future__ import annotations

import hashlib
import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse
import httpx

from backend.domain.evidence.models import EvidenceDocument
from backend.infrastructure.web_research.html_text import extract_clean_text_from_html

logger = logging.getLogger(__name__)

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024  # 2 MB limit
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_REDIRECTS = 3
USER_AGENT = "YourQuantumResearchBot/1.0 (+https://yourquantum.pl; verification-bot)"


def validate_url_security(url: str) -> tuple[bool, str]:
    """
    Strict SSRF validation:
    1. Only https (and explicitly verified http).
    2. No loopback, private, link-local, carrier-grade NAT, or cloud metadata IPs.
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL syntax: {e}"

    if parsed.scheme.lower() not in ("https", "http"):
        return False, f"Scheme '{parsed.scheme}' not allowed. Only HTTPS/HTTP supported."

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL"

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "::1", "169.254.169.254", "metadata.google.internal"):
        return False, f"Forbidden host: {hostname}"

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal") or hostname_lower.endswith(".onion"):
        return False, f"Internal domain name forbidden: {hostname}"

    # Resolve IP addresses to prevent DNS rebinding to private networks
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        return False, f"DNS resolution failed for {hostname}: {e}"

    for entry in addr_info:
        ip_str = entry[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid resolved IP address: {ip_str}"

        if ip.is_loopback:
            return False, f"Loopback address rejected: {ip_str}"
        if ip.is_private:
            return False, f"Private address rejected (SSRF protection): {ip_str}"
        if ip.is_link_local:
            return False, f"Link-local address rejected (SSRF protection): {ip_str}"
        if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False, f"Reserved/multicast address rejected: {ip_str}"
        # Cloud metadata address explicit check
        if str(ip).startswith("169.254."):
            return False, f"Cloud metadata link-local address rejected: {ip_str}"

    return True, "URL is safe"


class SafeWebFetcher:
    """
    Hardened HTTP client for retrieving and sanitizing public web documents.
    Enforces SSRF prevention, max byte streaming, and SHA-256 integrity hashing.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_bytes: int = MAX_DOCUMENT_BYTES,
        mock_documents: dict[str, str] | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes
        self._cache: dict[str, EvidenceDocument] = {}
        self._mock_documents: dict[str, str] = dict(mock_documents) if mock_documents is not None else {}

        if not self._mock_documents and os.getenv("YQ_MOCK_SEARCH_FIXTURES"):
            fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests", "fixtures", "web")
            doc1_path = os.path.join(fixtures_dir, "poland_health_spending.html")
            doc2_path = os.path.join(fixtures_dir, "poland_health_spending_alt.html")
            if os.path.exists(doc1_path):
                try:
                    with open(doc1_path, "r", encoding="utf-8") as f:
                        self._mock_documents["https://stat.gov.pl/zdrowie/raport-2025.html"] = f.read()
                except Exception:
                    pass
            if os.path.exists(doc2_path):
                try:
                    with open(doc2_path, "r", encoding="utf-8") as f:
                        self._mock_documents["https://nos.org.pl/zdrowie-naklady.html"] = f.read()
                except Exception:
                    pass

    async def fetch(self, url: str) -> EvidenceDocument | None:
        """
        Fetch a document from the web safely. Returns EvidenceDocument with SHA-256 hash or None.
        """
        # 0. Check mock fixtures
        if url in self._mock_documents:
            raw_html = self._mock_documents[url]
            clean_text, title = extract_clean_text_from_html(raw_html)
            h = hashlib.sha256(raw_html.encode("utf-8")).hexdigest()
            doc = EvidenceDocument(
                url=url,
                content_hash=h,
                page_text=clean_text,
                title=title or "Raport Testowy",
                status_code=200,
                mime_type="text/html",
            )
            self._cache[url] = doc
            return doc

        # 1. Check local cache
        if url in self._cache:
            return self._cache[url]

        # 2. SSRF Security Check
        is_safe, reason = validate_url_security(url)
        if not is_safe:
            logger.warning("SSRF blocked URL '%s': %s", url, reason)
            return None

        current_url = url
        redirect_count = 0

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            while redirect_count <= MAX_REDIRECTS:
                try:
                    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain"}
                    response = await client.get(current_url, headers=headers)
                except Exception as e:
                    logger.warning("Failed to fetch %s: %s", current_url, e)
                    return None

                # Handle redirects manually to re-verify SSRF on each jump
                if response.is_redirect and "location" in response.headers:
                    redirect_count += 1
                    next_url = response.headers["location"]
                    if next_url.startswith("/"):
                        parsed_cur = urlparse(current_url)
                        next_url = f"{parsed_cur.scheme}://{parsed_cur.netloc}{next_url}"

                    is_safe, reason = validate_url_security(next_url)
                    if not is_safe:
                        logger.warning("SSRF blocked redirect from '%s' to '%s': %s", current_url, next_url, reason)
                        return None
                    current_url = next_url
                    continue

                if response.status_code != 200:
                    logger.warning("HTTP %d when fetching %s", response.status_code, current_url)
                    return None

                # Check content length
                raw_bytes = response.content
                if len(raw_bytes) > self.max_bytes:
                    logger.warning("Document exceeded max byte limit (%d > %d) at %s", len(raw_bytes), self.max_bytes, current_url)
                    return None

                content_hash = hashlib.sha256(raw_bytes).hexdigest()
                content_type = response.headers.get("content-type", "text/html").lower()

                # Text/HTML extraction
                try:
                    text_body = raw_bytes.decode("utf-8", errors="replace")
                except Exception:
                    text_body = ""

                clean_text, title = extract_clean_text_from_html(text_body)

                doc = EvidenceDocument(
                    url=current_url,
                    content_hash=content_hash,
                    page_text=clean_text,
                    title=title or urlparse(current_url).netloc,
                    publisher=urlparse(current_url).netloc,
                    status_code=response.status_code,
                    mime_type=content_type,
                )
                self._cache[url] = doc
                self._cache[current_url] = doc
                return doc

        return None
