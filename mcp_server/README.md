# YourQuantum MCP Server

Oficjalny serwer MCP (**Model Context Protocol**) dla platformy [YourQuantum](https://yourquantum.pl).
Umożliwia asystentom AI (m.in. **Claude Desktop**, **Claude Code**, **Cowork**) bezpośrednie wykonywanie rygorystycznych obliczeń optymalizacyjnych z weryfikacją matematyczną i kryptograficznym certyfikatem SHA-256.

---

## ⚖️ Zasada uczciwości wyniku (Non-Negotiable)

Silnik YourQuantum **nie jest arbitralną wyrocznią** i nie zwraca „obiektywnie najlepszej opcji w sensie absolutnym”.
- Wynik stanowi **matematyczne optimum wyznaczone ŚCIŚLE względem jawnie zdefiniowanych przez użytkownika wag, kryteriów i ograniczeń**.
- Narzędzia serwera MCP **wymagają jawnego podania parametrów celu**. Jeśli brakuje kryterium lub wag — serwer zwraca błąd z prośbą o ich podanie, zamiast po cichu podstawiać domyślne założenia.
- Każda odpowiedź zawiera jawne zestawienie przyjętych założeń, status weryfikacji dopuszczalności, paszport SHA-256 oraz analizę odporności na wstrząsy (Stress-Testing ±25%).

---

## 🛠️ Dostępne narzędzia MCP

| Nazwa narzędzia | Opis | Główne parametry |
|---|---|---|
| `yq_optimize_options` | Wielokryterialna optymalizacja wyboru podzbioru wariantów pod zadaną funkcją celu i ograniczeniami. | `title`, `options` (min. 2), `objective_direction` (`maximize`/`minimize`), `objective_attribute` lub `objective_coefficients`, opcjonalnie: `budget_limit` + `budget_attribute`, `incompatible_pairs`, `exact_count`. |
| `yq_solve_portfolio` | Dobór projektów / alokacja kapitału maksymalizująca łączną wartość pod nieprzekraczalnym limitem budżetowym. | `projects` (lista z `id`, `name`, `cost`, `value`), `budget_limit` (> 0). |
| `yq_analyze_dilemma` | Weryfikacja jakości sformułowania dylematu (Input Quality Gate). Wykrywa ogólniki i brak liczb, generując pytania doprecyzowujące. | `description` (min. 5 znaków). |
| `yq_cognitive_intake` | Kognitywna formalizacja problemu decyzyjnego (Working Memory, Episodic Recall, Active Inference błędu predykcji). Przekształca język naturalny w model ProblemIR bez halucynacji. | `query` (min. 3 znaki). |
| `yq_get_engine_status` | Sprawdzenie statusu API i listy aktywnych adapterów solverów (CP-SAT, QAOA, Hybrid Benders). | Brak. |

---

## 🔑 Konfiguracja zmiennych środowiskowych

Skopiuj plik `.env.example` lub ustaw zmienne w konfiguracji klienta:

```bash
# Wymagany klucz API / hasło dostępu do YourQuantum:
YQ_API_KEY=A132a132!

# Opcjonalny adres bazowy API (domyślnie chmura produkcyjna):
YQ_API_BASE_URL=https://yourquantum.pl
```

> **Uwaga o bezpieczeństwie:** Klucz `YQ_API_KEY` jest czytany wyłącznie ze zmiennych środowiskowych procesu serwera MCP. Nigdy nie zapisuj kluczy na stałe w kodzie ani w repozytorium.

---

## 💻 Instalacja i uruchomienie lokalne

### 1. Wymagania
- Python 3.10+
- Zainstalowane zależności:
  ```bash
  pip install -r mcp_server/requirements.txt
  ```

### 2. Uruchomienie serwera (transport stdio)
```bash
python -m mcp_server
```
*(Serwer nasłuchuje na standardowym wejściu/wyjściu stdin/stdout zgodnie ze specyfikacją MCP)*

### 3. Uruchomienie smoke-testu
Aby sprawdzić działanie wszystkich narzędzi i łączność z API:
```bash
YQ_API_KEY=A132a132! python mcp_server/smoke_test.py
```

---

## 🤖 Konfiguracja konektora w Claude Desktop

Dodaj konfigurację serwera do pliku konfiguracyjnego Claude Desktop:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Wpis w `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yourquantum": {
      "command": "/Users/macbookpro/PROJEKTY/YOURQUANTUM/.venv/bin/python",
      "args": [
        "-m",
        "mcp_server"
      ],
      "env": {
        "YQ_API_KEY": "A132a132!",
        "YQ_API_BASE_URL": "https://yourquantum.pl",
        "PYTHONPATH": "/Users/macbookpro/PROJEKTY/YOURQUANTUM"
      }
    }
  }
}
```

---

## 👥 Użycie w Cowork / Claude Code / CLI

W środowiskach uruchamianych z linii poleceń serwer można zarejestrować komendą:

```bash
claude mcp add yourquantum -- /Users/macbookpro/PROJEKTY/YOURQUANTUM/.venv/bin/python -m mcp_server
```
*(z ustawioną wcześniej zmienną środowiskową `export YQ_API_KEY="A132a132!"`)*
