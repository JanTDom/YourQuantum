# RAPORT Z WDROŻENIA V21: DANE Z SIECI TAKŻE W KLASIE DESIGN (DEC-042)

**Data:** 2026-09-19  
**Autor wdrożenia:** Antigravity  
**Zlecenie:** Prompt V21 (Jan Domaniewski)  
**Środowisko:** Produkcja `https://yourquantum.pl` (Vercel deployment `macieto`)  
**Commity docelowe:** `5bcacac`, `5c760fd`, `d4fb63c` (origin/main)

---

## 1. Cel i zakres wdrożenia V21

Podczas zadawania pytań o wybór wariantów architektonicznych i systemowych w klasie `DESIGN` (np. *„Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?”*), dotychczasowy silnik zwracał pustą tabelę macierzy ocen do manualnego uzupełnienia, a w kodzie figurowały sztuczne wartości (`7.0` / `3.0`, `provenance="assumed"`).

Wdrożenie V21 zrealizowało 5 kluczowych postulatów:
1. **Całkowite wyeliminowanie zmyślonych liczb modelu (DEC-042 / Fable 5.1):**
   - Usunięto sztuczne domyślne oceny `7.0` i `3.0` oraz status `provenance="assumed"`.
   - Komórka macierzy ocen (`score_matrix`), dla której w dokumentach sieciowych nie znaleziono zweryfikowanej wartości, pozostaje pusta (`value=None`, `provenance="unverified"`).
   - Wartość może pochodzić wyłącznie ze zweryfikowanego źródła (`web_sourced`) albo z bezpośredniego wpisu decydenta (`user_supplied`).
2. **Podpięcie klasy DESIGN pod rurociąg dowodowy z sieci www:**
   - Wykorzystano ten sam, zweryfikowany rurociąg dowodowy co dla prognoz: wyszukiwanie w sieci, ochrona SSRF w `SafeWebFetcher` oraz ekstrakcja z dosłowną weryfikacją cytatów w tekście źródłowym (`EvidenceExtractor._verify_quote_in_text`).
   - W fazie intake system wyszukuje i pobiera dokumenty, po czym ekstrahuje parametry dla dźwigni i opcji (z limitem budżetowym do 6 kluczowych parametrów).
3. **Ocena Pareto na udokumentowanym podzbiorze kryteriów:**
   - Brak danych w komórkach nie jest zastępowany zerami ani średnimi (co zafałszowałoby relacje dominacji).
   - Kryteria, dla których nie ma ani jednej udokumentowanej wartości w żadnej opcji, są wykluczane z kalkulacji Pareto i jawnie raportowane decydentowi w liście `design_criteria_excluded`.
   - Obliczanie frontu Pareto (`compute_design_pareto_frontier`) odbywa się wyłącznie na aktywnych kryteriach posiadających ugruntowane dane.
4. **Uczciwy fallback przy braku danych (`insufficient_data`):**
   - Jeżeli macierz nie zawiera żadnych udokumentowanych komórek (`documented_cells == 0`), silnik nie zgaduje konfiguracji optymalnej, lecz zwraca `insufficient_data=True` z uczciwym komunikatem: *„Nie znalazłem wystarczających danych, żeby porównać te warianty.”*
5. **Modernizacja interfejsu `DesignWorkspace.tsx`:**
   - Usunięto jednostkowe przyciski „oznacz jako założenie”.
   - Dodano zbiorczy przycisk `🌐 Dociągnij dane z sieci` z limitem do 6 brakujących komórek per kliknięcie.
   - Dodano odznakę telemetryczną liczby komórek ugruntowanych i pustych: `Dane: X ugruntowanych / Y pustych`.
   - Umożliwiono decydentowi ręczne wprowadzanie własnych wartości (`user_supplied`) oraz odblokowano syntezę natychmiast po udokumentowaniu co najmniej 1 kryterium.

---

## 2. Wyniki 10-biegowego pomiaru produkcyjnego (`https://yourquantum.pl`)

Pomiar zrealizowano na żywej produkcji skryptem `scripts/measure_design_v21.py`:
- **Zapytanie testowe:** *„Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?”*
- **Liczba biegów:** 10
- **Środowisko:** Produkcja `https://yourquantum.pl/api/v1/cognitive/intake`

### Tabela pomiaru produkcyjnego

| Bieg | Status | Czas całkowity | Klasa problemu | Dźwignie / Kryteria | Komórki udokumentowane (`web_sourced`) | Komórki zmyślone (`assumed`) | Liczba unikalnych źródeł | Przykładowe zweryfikowane źródła sieciowe |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | 200 OK | 107,05 s | DESIGN | 3 / 3 | 0 (brak danych w budżecie) | **0** | 0 | Uczciwy fallback: brak liczb w znalezionych stronach |
| 2 | 200 OK | 102,13 s | DESIGN | 3 / 3 | 4 | **0** | 1 | poradnikzdrowie.pl (budżet na zdrowie 2027) |
| 3 | 200 OK | 101,41 s | DESIGN | 3 / 3 | 4 | **0** | 1 | rp.pl (Forum Ekonomiczne: koszty ochrony zdrowia) |
| 4 | 200 OK | 99,06 s | DESIGN | 3 / 3 | 0 (brak danych w budżecie) | **0** | 0 | Uczciwy fallback: brak liczb w znalezionych stronach |
| 5 | 200 OK | 114,82 s | DESIGN | 3 / 3 | 4 | **0** | 2 | alertmedyczny.pl (Plan transformacji MZ 2027-2031), remedium.md |
| 6 | 200 OK | 117,65 s | DESIGN | 3 / 3 | 5 | **0** | 2 | krytykapolityczna.pl (analiza wydatków NFZ), rp.pl |
| 7 | 200 OK | 104,70 s | DESIGN | 3 / 3 | 0 (brak danych w budżecie) | **0** | 0 | Uczciwy fallback: brak liczb w znalezionych stronach |
| 8 | 200 OK | 115,76 s | DESIGN | 3 / 3 | 4 | **0** | 2 | wei.org.pl (analiza systemu opieki), statista.com |
| 9 | 200 OK | 119,01 s | DESIGN | 3 / 3 | 2 | **0** | 1 | speyside-group.com (raport ochrony zdrowia) |
| 10 | 200 OK | 111,26 s | DESIGN | 3 / 3 | 2 | **0** | 1 | aip-group.pl (analiza systemu opieki zdrowotnej w Polsce) |

### Statystyki zbiorcze:
- **Skuteczność endpointu:** 10 z 10 biegów zakończonych statusem 200 OK (100%).
- **Czas całkowity odpowiedzi:**
  - **Mediana:** 109,16 s
  - **Średnia:** 109,28 s
  - **Najszybszy bieg (Min):** 99,06 s
  - **Najwolniejszy bieg (Max):** 119,01 s
- **Liczba komórek ze statusem `assumed`:** **0 we wszystkich 10 biegach (100% czystości faktograficznej)**.
- **Ugruntowanie empiryczne:** W 7 na 10 biegów silnik pozyskał od 2 do 5 zweryfikowanych wartości liczbowych z polskich portali branżowych, rządowych i ekonomicznych. W 3 biegach, w których wyszukiwanie nie zwróciło jednoznacznych statystyk liczbowych, silnik zwrócił uczciwe 0 komórek bez zmyślania ani jednej cyfry.

---

## 3. Zgodność z bramkami mechanicznymi (scripts/check_v4.sh)

Wszystkie mechaniczne bramki weryfikacyjne zakończyły się statusem **PASS**:
- `G-R1a` – `PASS` (0 trafień zakazanych domen w kodzie frontendu)
- `G-R1b` – `PASS` (brak fixture w RecommendationView)
- `G-R1c` – `PASS` (syntetyczne dane testowe)
- `G-R2` / `G-R3` – `PASS` (bezpieczeństwo sekretów)
- `G-R4` – `PASS` (wszystkie ścieżki w dokumentacji istnieją na dysku)
- `G-R5` / `G-R6` – `PASS` (brak zmyślonych domyślnych wartości i czysty search_adapter)
- `G-TESTS` – `PASS` (262 testy pytest zakończone sukcesem w 320 s; kompilacja Vite/TypeScript 0 błędów)
- **WYNIK KOŃCOWY:** 25 BRAMEK ZIELONYCH (PASS).

---

## 4. Status podsumowujący

Wdrożenie V21 w pełni zintegrowało klasę DESIGN z realnym światem faktów sieciowych:
- Zamiast pustej tabeli decydent otrzymuje ugruntowane wskaźniki z sieci (m.in. koszty, wydatki, nakłady na ochronę zdrowia).
- Żadna cyfra nie jest generowana przez model jako halucynacja.
- Obliczenia Pareto i synteza opierają się wyłącznie na udokumentowanym podzbiorze faktów.
