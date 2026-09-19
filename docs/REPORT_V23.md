# RAPORT V23 — SYNTEZA DESIGN W ŚCIEŻCE INTAKE

Data: 2026-09-19 · Gałąź: `main` · Autor pomiarów: Claude (audyt niezależny)

Raport domyka zlecenie rozpoczęte commitem `1e5259b`, który nie został zamknięty raportem ani pomiarem.

---

## 1. Co zostało wdrożone

Commit `1e5259b` wpiął `compute_design_synthesis` w ścieżkę `cognitive/intake` dla klasy DESIGN i przeniósł do `metadata` pola `ranking_withheld`, `ranking_withheld_reason`, `coverage_percentage`, `indistinguishable_variants` oraz `insufficient_data`. Decyzja zapisana jako DEC-044.

To zamyka usterkę opisaną w `docs/REPORT_V22.md`: logika wstrzymywania rankingu istniała, ale nie była wywoływana w tej ścieżce, więc endpoint zawsze zwracał `ranking_withheld=False`.

Poza kodem commit nie pozostawił raportu, wpisu w stanie bieżącym ani pomiaru. Niniejszy dokument uzupełnia te trzy braki.

---

## 2. Pomiar na żywej produkcji

Pięć wywołań `POST https://yourquantum.pl/api/v1/cognitive/intake`, zapytanie „Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?". Surowe wyniki: `docs/measurement_v23_raw.jsonl`.

| Bieg | HTTP | Czas | Komórki ogółem | Udokumentowane | Odrzucone off-topic | Odrzucone duplikat | Pokrycie | Ranking wstrzymany |
|---|---|---|---|---|---|---|---|---|
| 1 | 200 | 67,1 s | 48 | 0 | 0 | 0 | 0,0% | tak |
| 2 | 200 | 113,0 s | 18 | 0 | 5 | 0 | 0,0% | tak |
| 3 | — | 165,3 s | — | — | — | — | — | przerwany timeoutem po stronie klienta |
| 4 | 200 | 112,7 s | 18 | 1 | 1 | 1 | 5,6% | tak |
| 5 | 200 | 160,4 s | 18 | 2 | 4 | 0 | 11,1% | tak |

Statystyki z czterech udanych biegów: mediana czasu 112,8 s, najkrótszy 67,1 s, najdłuższy 160,4 s. Pokrycie większe od zera w dwóch biegach na cztery. Ranking wstrzymany w czterech na cztery. Łącznie dziesięć komórek odrzuconych jako niedotyczące wariantu i jedna jako duplikat dowodu.

---

## 3. Co z tego wynika

### Działa zgodnie z zamówieniem

1. **Zero komórek zmyślonych** we wszystkich biegach. Zakaz z DEC-043 utrzymany.
2. **Reguła trafienia w wariant działa** — dziesięć odrzuceń oznacza, że ekstraktor znajdował liczby, ale odrzucał te, których zdanie nie dotyczyło danego wariantu.
3. **Deduplikacja działa** — jedno odrzucenie duplikatu w biegu czwartym.
4. **Wstrzymanie rankingu działa i podaje powód** — w biegach czwartym i piątym powodem były całkowicie puste dźwignie wymienione z nazwy, a nie ogólnikowy komunikat.

### Nie działa jako produkt

Pokrycie macierzy wynosi od 0% do 11,1%. W trzech biegach na cztery użytkownik nie dostaje żadnego porównania wariantów, tylko komunikat o braku danych.

Przyczyna nie jest błędem w kodzie. Artykuły prasowe i strony instytucji opisujące reformę systemu ochrony zdrowia **nie zawierają liczb mierzących pojedyncze kryterium dla pojedynczego wariantu finansowania**. Macierz ocen wymaga danych o strukturze, której źródła sieciowe nie mają. Diagnoza na próbce dokumentów pobranych przez silnik: ekstraktor zwraca dowody z poprawnym cytatem, ale z polem wartości pustym, a kod pomija komórki bez liczby.

Wybór między zaniżeniem rygoru a brakiem wyniku został rozstrzygnięty na korzyść braku wyniku i tak ma pozostać. Zmiana wymaga decyzji o tym, **co ścieżka DESIGN ma zwracać**, a nie o tym, jak mocno filtrować.

### Czas odpowiedzi

Mediana 112,8 s i jeden bieg przerwany po 165 s to wartości, przy których użytkownik zamyka kartę. Limit funkcji wynosi 300 s, więc nie grozi to błędem serwera, ale wymaga decyzji produktowej.

---

## 4. Stan bramek

`bash scripts/check_v4.sh` wskazał czerwoną bramkę G-R4: pięć ścieżek zapisanych w dokumentacji jako same nazwy plików bez katalogu, w `docs/memory/CURRENT_STATE.md` i `docs/memory/DECISIONS.md`. Ścieżki poprawiono na pełne względne w ramach niniejszego domknięcia.

Bramka G-TESTS pozostaje czerwona wyłącznie w środowisku audytora: `.venv/bin/pytest` ma interpreter wskazujący na ścieżkę lokalną autora, a `frontend/node_modules` zawiera binarium rollupa dla innej platformy. Nie jest to defekt kodu.

---

## 5. Co pozostaje do decyzji właściciela

1. Czy ścieżka DESIGN ma nadal dążyć do liczbowej macierzy ocen, czy zwracać udokumentowany przegląd wariantów z cytatami bez wymuszania liczb.
2. Czy akceptowalna jest mediana czasu odpowiedzi powyżej stu sekund, czy potrzebne jest ograniczenie zakresu badania.

Do czasu tej decyzji zachowanie aplikacji jest uczciwe: brak danych jest nazywany brakiem danych.
