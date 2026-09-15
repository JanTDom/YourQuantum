# YOURQUANTUM – POMIARY EMPIRYCZNE I BENCHMARKI
**Wersja:** 2026-09-15  
**Projekt:** YourQuantum  
**Środowisko:** Darwin 25.6.0 (x86_64), Intel(R) Core(TM) i9-9980HK CPU @ 2.40GHz, Python 3.12.14  

---

## 1. Benchmark progu niezależnej enumeracji małego N (`scripts/bench_enumeration.py`)

### 1.1. Metodologia pomiaru
- **Cel:** Empiryczne wyznaczenie progu `MAX_ENUMERATION_VARS` dla metody `_independent_small_n_enumeration` w `backend/verifier/verifier.py`.
- **Budżet czasowy:** Maksymalnie 2,0 sekundy mediany czasu ściankowego na jedno wywołanie certyfikacji optymalności.
- **Struktura zadania testowego:** Syntetyczny problem plecakowy o $n$ zmiennych binarnych $x_i \in \{0, 1\}$, funkcji celu $\min \sum_{i=0}^{n-1} c_i x_i$, realistycznym ograniczeniu pojemności $\sum_{i=0}^{n-1} w_i x_i \ge W$ oraz kardynalności $\sum x_i \ge 1$.
- **Liczba powtórzeń per rozmiar:** 3 przebiegi (z wyznaczeniem mediany, minimum i maksimum).

### 1.2. Surowe wyniki pomiarów (2026-09-15T18:12:29Z)

| $n$ (liczba zmiennych binarnych) | Mediana czasu [s] | Czas min [s] | Czas max [s] | Liczba prób | W budżecie ($\le 2,0$ s) |
|---|---|---|---|---|---|
| **16** | **3,6476** | 3,1581 | 3,8292 | 3 | **NIE** (przekracza budżet 2,0 s) |
| **18** | **15,9091** | 15,6858 | 17,3063 | 3 | **NIE** ($7,9\times$ ponad budżet) |
| **20** | *Pominięto ($O(2^n)$)* | — | — | — | **NIE** (szacowany czas $\sim 64$ s) |
| **22** | *Pominięto ($O(2^n)$)* | — | — | — | **NIE** (szacowany czas $\sim 256$ s) |
| **24** | *Pominięto ($O(2^n)$)* | — | — | — | **NIE** (szacowany czas $> 1000$ s) |

### 1.3. Wnioski i decyzja
Zgodnie z zasadą Promptu V9:
> *Budżet czasu: 2,0 sekundy mediany na jedno wywołanie enumeracji. Nowym progiem jest największe n z przebadanych, dla którego mediana mieści się w budżecie. Jeżeli wyjdzie 16 – zostawiasz 16 i tak piszesz w raporcie.*

Mediana dla $n=16$ wyniosła 3,65 s, a dla $n=18$ aż 15,91 s. Żadna wartość $n > 16$ nie mieści się w budżecie 2,0 s.
W związku z tym próg pozostaje na dotychczasowym konserwatywnym poziomie:
$$\text{MAX\_ENUMERATION\_VARS} = 16$$
Próg ten został skonsolidowany do pojedynczej nazwanej stałej na górze `backend/verifier/verifier.py` i podstawiony we wszystkich trzech dotychczasowych wystąpieniach literału 16.
