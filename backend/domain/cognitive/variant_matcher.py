"""
backend/domain/cognitive/variant_matcher.py — Weryfikacja trafienia cytatu w wariant dźwigni (V22 §2B, DEC-043).

Reguła 2B:
Ekstrakcja prowadzona jest osobno dla każdej pary (wariant, kryterium). Wskazane zdanie
musi wymieniać dany wariant albo jego jednoznaczny synonim (np. „model budżetowy",
„finansowanie z budżetu państwa" dla public_tax). Jeżeli zdanie nie zawiera nazwy wariantu
ani jego synonimu — komórka zostaje pusta, a licznik design_cells_rejected_off_topic rośnie.
"""
from __future__ import annotations

import re
from typing import Optional, List, Dict

POLISH_STOPWORDS = {
    "oraz", "albo", "przez", "dla", "jego", "jest", "było", "będzie",
    "tego", "tych", "może", "jako", "który", "która", "które", "tylko", "więc",
    "przy", "przed", "poza", "przede", "wszystkim", "także", "również", "jednak"
}

# Rejestr znanych synonimów domenowych dla popularnych wariantów reform systemowych
KNOWN_VARIANT_SYNONYMS: Dict[str, List[str]] = {
    # Finansowanie ochrony zdrowia
    "public_tax": [
        "model budżetow", "finansowanie z budżetu", "budżet państwa", "podatk",
        "single payer", "beveridge", "jednolity płatnik", "public_tax"
    ],
    "opt_fin_jednolity": [
        "model budżetow", "finansowanie z budżetu", "budżet państwa", "podatk",
        "single payer", "beveridge", "jednolity płatnik", "public_tax"
    ],
    "social_insurance": [
        "ubezpieczeni", "bismarck", "składk", "kas chorych", "kasy chorych",
        "nfz", "fundusz zdrowia", "ubezpieczenie zdrowotne", "social_insurance", "konkurencja kas"
    ],
    "opt_fin_konkurencja": [
        "ubezpieczeni", "bismarck", "składk", "kas chorych", "kasy chorych",
        "nfz", "fundusz zdrowia", "ubezpieczenie zdrowotne", "social_insurance", "konkurencja kas"
    ],
    "mixed_insurance": [
        "model mieszan", "współpłaceni", "wielofilarow", "dodatkow ubezpieczen",
        "prywatn ubezpieczen", "mixed_insurance", "wielopłatnik", "filary"
    ],
    "opt_fin_mieszany": [
        "model mieszan", "współpłaceni", "wielofilarow", "dodatkow ubezpieczen",
        "prywatn ubezpieczen", "mixed_insurance", "wielopłatnik", "filary"
    ],
    # Struktura szpitalnictwa
    "hospital_ownership": [
        "szpital", "szpitalnictw", "placówk", "spzoz", "konsolidac", "powiat"
    ],
    # Cyfryzacja
    "digitalization": [
        "cyfryzacj", "e-zdrowi", "p1", "e-rejestracj", "telemedycyn"
    ],
}


def _stem_simple(word: str) -> str:
    """Proste odcięcie polskich końcówek fleksyjnych."""
    w = word.lower().strip()
    for suffix in ("owych", "owej", "owym", "owej", "nych", "nym", "nej", "ach", "ami", "ego", "emu", "ów", "om", "em", "ie", "ce", "ek", "ka", "ki", "ku", "y", "a", "e", "u", "i"):
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def get_variant_keywords(
    option_title: str,
    option_id: str = "",
    extra_synonyms: Optional[List[str]] = None,
) -> List[str]:
    """Zwraca listę fraz i rdzeni słów identyfikujących dany wariant."""
    keywords: set[str] = set()

    # 1. Sprawdzenie rejestru synonimów po option_id
    clean_opt_id = option_id.lower().strip()
    if clean_opt_id in KNOWN_VARIANT_SYNONYMS:
        for syn in KNOWN_VARIANT_SYNONYMS[clean_opt_id]:
            keywords.add(syn.lower())

    for key, syns in KNOWN_VARIANT_SYNONYMS.items():
        if key in clean_opt_id:
            for s in syns:
                keywords.add(s.lower())

    # 2. Dodatkowe synonimy przekazane jawnie
    if extra_synonyms:
        for s in extra_synonyms:
            if s and len(s.strip()) >= 3:
                keywords.add(s.strip().lower())

    # 3. Ekstrakcja z tytułu wariantu
    clean_title = re.sub(r"[^\w\s-]", " ", option_title).strip()
    words = [w.lower() for w in clean_title.split() if len(w) >= 4 and w.lower() not in POLISH_STOPWORDS]

    for w in words:
        stem = _stem_simple(w)
        if len(stem) >= 3:
            keywords.add(stem)

    # Dodaj pełne 2-słowne frazy z tytułu
    if len(words) >= 2:
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            keywords.add(phrase)

    return sorted(keywords)


def verify_variant_in_quote(
    quote: str,
    option_title: str,
    option_id: str = "",
    lever_name: str = "",
    extra_synonyms: Optional[List[str]] = None,
) -> bool:
    """
    Weryfikuje, czy zdanie/cytat z dokumentu rzeczywiście dotyczy wskazanego wariantu (V22 §2B).
    Zwraca True wtedy i tylko wtedy, gdy w tekście cytatu występuje co najmniej jedno
    jednoznaczne odniesienie do nazwy wariantu, jego rdzenia lub zarejestrowanego synonimu.
    """
    if not quote or not quote.strip():
        return False

    q_lower = quote.lower()
    keywords = get_variant_keywords(option_title, option_id=option_id, extra_synonyms=extra_synonyms)

    for kw in keywords:
        if kw in q_lower:
            return True

    return False
