"""
YourQuantum — Safe HTML to Text Extractor
Deterministic, dependency-free text extractor using standard library html.parser.
Strips scripts, styles, navigations, and normalises whitespace.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser


class _TextExtractingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.result: list[str] = []
        self.title: str = ""
        self._in_title = False
        self._ignore_stack: list[str] = []
        self._ignored_tags = {
            "script", "style", "nav", "header", "footer",
            "aside", "noscript", "svg", "button", "form",
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self._ignored_tags:
            self._ignore_stack.append(tag_lower)
        elif tag_lower == "title":
            self._in_title = True
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br"):
            if not self._ignore_stack:
                self.result.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self._ignored_tags and self._ignore_stack:
            self._ignore_stack.pop()
        elif tag_lower == "title":
            self._in_title = False
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            if not self._ignore_stack:
                self.result.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._ignore_stack:
            text = data.strip()
            if text:
                self.result.append(data)


def extract_clean_text_from_html(html_content: str) -> tuple[str, str]:
    """
    Parses HTML content safely into (clean_text, title).
    Collapses excess whitespace while preserving paragraph boundaries.
    """
    parser = _TextExtractingParser()
    try:
        parser.feed(html_content)
        parser.close()
    except Exception:
        # Fallback to pure regex if malformed HTML causes parser crash
        clean = re.sub(r"<[^>]+>", " ", html_content)
        return re.sub(r"\s+", " ", clean).strip(), ""

    raw_text = "".join(parser.result)
    # Normalize multiple newlines and spaces
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    clean_text = "\n\n".join(lines)
    return clean_text, parser.title.strip()
