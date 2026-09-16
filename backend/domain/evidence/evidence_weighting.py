"""
backend/domain/evidence/evidence_weighting.py

Deterministyczne wyliczanie wag przesłanek empirycznych (web_sourced) z udokumentowanych
właściwości dowodów, bez udziału modelu językowego (V12 §2, DEC-036).

WAGA KOŃCOWA I JEJ CZTERY SKŁADOWE:
----------------------------------
Waga przesłanki W in [0.0, 1.0] wyliczana jest jako ważona kombinacja liniowa czterech
udokumentowanych składowych odczytywanych z dowodu Evidence lub jego metadanych:

    W = 0.30 * S_corroboration + 0.30 * S_source_class + 0.20 * S_recency + 0.20 * S_specificity

Współczynniki wagowe [0.30, 0.30, 0.20, 0.20] (suma = 1.0) są jawną decyzją projektową (DEC-036),
a nie pomiarem fizycznym. Każda składowa S_* przyjmuje znormalizowaną wartość w przedziale [0.0, 1.0]:

1. S_corroboration (potwierdzenie międzyźródłowe):
   Liczba różnych domen rejestrowalnych wśród pobranych dokumentów, które potwierdzają ten sam fakt.
   - 1 domena: 0.50
   - 2 domeny: 0.80
   - >=3 domeny: 1.00
   - Gdy nie da się ustalić: 0.50 (status: neutralna/jedno źródło).

2. S_source_class (klasa źródła):
   Odczytywana z wersjonowanego pliku konfiguracyjnego `config/source_classes.json`.
   - tier_1 (instytucje państwowe, międzynarodowe, wiodące ośrodki analityczne): 1.00
   - tier_2 (wiodące agencje informacyjne, prasa referencyjna): 0.80
   - tier_3 (renomowane portale informacyjne, prasa codzienna i branżowa): 0.60
   - tier_4 (pozostałe domeny sieciowe, blogi, niesklasyfikowane): 0.40
   - Domena spoza rejestru dostaje zawsze klasę najniższą (tier_4 -> 0.40). Nigdy w górę.

3. S_recency (świeżość publikacji):
   Odstęp Evidence.published_at od dziś (retrieved_at lub now), odniesiony do horyzontu analizy:
   - <= 30 dni: 1.00
   - <= 90 dni: 0.85
   - <= 180 dni: 0.70
   - <= 365 dni: 0.55
   - > 365 dni: 0.40
   - Gdy published_at jest nieznana: 0.50 (status: nieustalona, wartość neutralna).

4. S_specificity (konkretność i mierzalność cytatu):
   Czy Evidence.quote zawiera konkretne liczby, procenty, kwoty lub daty:
   - Cytat mierzalny (zawiera liczbę/procent/datę): 1.00
   - Cytat wyłącznie jakościowy: 0.50
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from backend.domain.evidence.models import Evidence

logger = logging.getLogger(__name__)

SOURCE_CLASSES_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "config", "source_classes.json"
)

# Cache rejestru klas domen
_SOURCE_CLASSES_CACHE: Optional[Dict[str, Any]] = None


def load_source_classes_registry() -> Dict[str, Any]:
    global _SOURCE_CLASSES_CACHE
    if _SOURCE_CLASSES_CACHE is not None:
        return _SOURCE_CLASSES_CACHE

    config_path = os.path.abspath(SOURCE_CLASSES_CONFIG_PATH)
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                _SOURCE_CLASSES_CACHE = json.load(f)
                return _SOURCE_CLASSES_CACHE
        except Exception as err:
            logger.warning("Failed to load source_classes.json from %s: %s", config_path, err)

    _SOURCE_CLASSES_CACHE = {
        "version": "fallback-1.0",
        "tiers": {
            "tier_1": {"score": 1.0, "name": "Instytucje państwowe / badawcze"},
            "tier_2": {"score": 0.8, "name": "Agencje informacyjne"},
            "tier_3": {"score": 0.6, "name": "Media informacyjne"},
            "tier_4": {"score": 0.4, "name": "Domeny niesklasyfikowane"},
        },
        "domains": {},
    }
    return _SOURCE_CLASSES_CACHE


def extract_registrable_domain(url_or_domain: str) -> str:
    """Ekstrahuje domenę rejestrowalną (np. https://stat.gov.pl/foo -> stat.gov.pl)."""
    if not url_or_domain:
        return ""
    text = url_or_domain.strip().lower()
    if "://" in text:
        try:
            netloc = urlparse(text).netloc
            text = netloc.split(":")[0]
        except Exception:
            pass
    text = text.split("/")[0].split(":")[0]
    if text.startswith("www."):
        text = text[4:]
    return text


class WeightBreakdown(BaseModel):
    """Szczegółowe, audytowalne rozbicie wyliczonej wagi przesłanki (V12 §2)."""
    corroboration_domains_count: int
    corroboration_score: float
    corroboration_details: str

    source_domain: str
    source_tier: str
    source_tier_name: str
    source_class_score: float

    published_date_str: Optional[str] = None
    age_days: Optional[int] = None
    recency_score: float
    recency_is_unknown: bool
    recency_details: str

    quote_has_metrics: bool
    specificity_score: float
    specificity_details: str

    final_weight: float
    formula_explanation: str
    justification_summary: str


def check_quote_specificity(quote: str) -> Tuple[bool, float, str]:
    """Weryfikuje, czy cytat zawiera dane liczbowe, procenty lub daty."""
    if not quote:
        return False, 0.50, "Cytat jakościowy bez mierzalnych danych liczbowych"

    # Wzorce: liczby arabskie, procenty, lata (19xx, 20xx), kwoty
    has_number = bool(re.search(r"\b\d+([.,]\d+)?\b", quote))
    has_percent = bool(re.search(r"(\%|procent\w*|pb\b|punkt\w*\s+bazow\w*)", quote, re.IGNORECASE))
    has_year = bool(re.search(r"\b(20\d\d|19\d\d)\b", quote))

    if has_number or has_percent or has_year:
        return True, 1.00, "Cytat zawiera konkretne dane liczbowe lub daty"
    return False, 0.50, "Cytat wyłącznie jakościowy"


def compute_recency_score(
    published_at: Optional[datetime | str],
    reference_date: Optional[datetime] = None,
) -> Tuple[float, Optional[int], Optional[str], bool, str]:
    """Wylicza składową świeżości dokumentu."""
    ref_dt = reference_date or datetime.now(timezone.utc)
    if ref_dt.tzinfo is None:
        ref_dt = ref_dt.replace(tzinfo=timezone.utc)

    if not published_at:
        return 0.50, None, None, True, "Data publikacji nieznana (przyjęto wartość neutralną 0,50)"

    pub_dt: Optional[datetime] = None
    pub_str: Optional[str] = None

    if isinstance(published_at, datetime):
        pub_dt = published_at
        pub_str = published_at.isoformat()
    elif isinstance(published_at, str):
        pub_str = published_at.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                pub_dt = datetime.strptime(pub_str[:19], fmt[:19])
                break
            except Exception:
                continue

    if pub_dt is None:
        return 0.50, None, pub_str, True, "Nie udało się sparsować daty publikacji (wartość neutralna 0,50)"

    if pub_dt.tzinfo is None:
        pub_dt = pub_dt.replace(tzinfo=timezone.utc)

    age_days = max(0, (ref_dt - pub_dt).days)

    if age_days <= 30:
        score = 1.00
        desc = f"Publikacja sprzed {age_days} dni (bardzo świeża)"
    elif age_days <= 90:
        score = 0.85
        desc = f"Publikacja sprzed {age_days} dni (ostatni kwartał)"
    elif age_days <= 180:
        score = 0.70
        desc = f"Publikacja sprzed {age_days} dni (ostatnie półrocze)"
    elif age_days <= 365:
        score = 0.55
        desc = f"Publikacja sprzed {age_days} dni (ostatni rok)"
    else:
        score = 0.40
        desc = f"Publikacja archiwalna (sprzed {age_days} dni)"

    return score, age_days, pub_str, False, desc


def compute_evidence_weight(
    evidence: Evidence,
    all_evidences: Optional[List[Evidence]] = None,
    reference_date: Optional[datetime] = None,
) -> WeightBreakdown:
    """
    Deterministycznie wylicza wagę przesłanki empirycznej na podstawie jej udokumentowanych właściwości.
    """
    registry = load_source_classes_registry()
    domains_map = registry.get("domains", {})
    tiers_map = registry.get("tiers", {})

    # 1. Corroboration: unikalne domeny potwierdzające dowód
    doc_evidences = all_evidences or [evidence]
    ev_domain = extract_registrable_domain(evidence.source_url or evidence.publisher or "")
    unique_domains: set[str] = set()

    for other_ev in doc_evidences:
        other_dom = extract_registrable_domain(other_ev.source_url or other_ev.publisher or "")
        if other_dom:
            unique_domains.add(other_dom)

    domains_count = len(unique_domains) if unique_domains else 1

    if domains_count >= 3:
        corroboration_score = 1.00
        corroboration_desc = f"{domains_count} niezależne domeny potwierdzające"
    elif domains_count == 2:
        corroboration_score = 0.80
        corroboration_desc = "2 niezależne domeny źródłowe"
    else:
        corroboration_score = 0.50
        corroboration_desc = "1 domena źródłowa (pojedyncze potwierdzenie)"

    # 2. Source class: z wersjonowanego config/source_classes.json
    tier_id = domains_map.get(ev_domain, "tier_4")
    tier_info = tiers_map.get(tier_id, {"score": 0.4, "name": "Domeny niesklasyfikowane"})
    source_class_score = float(tier_info.get("score", 0.4))
    source_tier_name = str(tier_info.get("name", "Domeny niesklasyfikowane"))

    # 3. Recency: data publikacji odniesiona do daty referencyjnej
    recency_score, age_days, pub_str, recency_is_unknown, recency_desc = compute_recency_score(
        evidence.published_at, reference_date=reference_date
    )

    # 4. Specificity: mierzalność cytatu (liczba, data, procent)
    has_metrics, specificity_score, specificity_desc = check_quote_specificity(evidence.quote)

    # Wzór deterministyczny (DEC-036)
    # W = 0.30 * S_corroboration + 0.30 * S_source_class + 0.20 * S_recency + 0.20 * S_specificity
    raw_weight = (
        0.30 * corroboration_score +
        0.30 * source_class_score +
        0.20 * recency_score +
        0.20 * specificity_score
    )
    final_weight = round(max(0.05, min(1.0, raw_weight)), 2)

    formula_exp = (
        f"0.30*corroboration({corroboration_score:.2f}) + "
        f"0.30*source_class({source_class_score:.2f}) + "
        f"0.20*recency({recency_score:.2f}) + "
        f"0.20*specificity({specificity_score:.2f}) = {final_weight:.2f}"
    )

    # Uzasadnienie widoczne w interfejsie użytkownika
    justification_parts = [
        corroboration_desc,
        f"klasa źródła: {source_tier_name} ({ev_domain or 'nieznana domena'})",
        recency_desc,
        "cytat zawiera dane mierzalne/liczbowe" if has_metrics else "cytat jakościowy",
    ]
    justification_summary = f"Waga {final_weight:.2f} — " + ", ".join(justification_parts) + "."

    return WeightBreakdown(
        corroboration_domains_count=domains_count,
        corroboration_score=corroboration_score,
        corroboration_details=corroboration_desc,
        source_domain=ev_domain,
        source_tier=tier_id,
        source_tier_name=source_tier_name,
        source_class_score=source_class_score,
        published_date_str=pub_str,
        age_days=age_days,
        recency_score=recency_score,
        recency_is_unknown=recency_is_unknown,
        recency_details=recency_desc,
        quote_has_metrics=has_metrics,
        specificity_score=specificity_score,
        specificity_details=specificity_desc,
        final_weight=final_weight,
        formula_explanation=formula_exp,
        justification_summary=justification_summary,
    )
