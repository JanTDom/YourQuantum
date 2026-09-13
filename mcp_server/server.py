"""
YourQuantum MCP Server
Exposes YourQuantum decision optimization engines as Model Context Protocol (MCP) tools.
Compatible with Claude Desktop, Claude Code, and Cowork.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, List, Literal, Optional

from mcp.server.mcpserver import MCPServer
from mcp_server.client import YourQuantumApiClient, YourQuantumApiError

# Configure structured logging to stderr so it does not interfere with stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("yourquantum-mcp-server")

# Initialize MCP Server instance
server = MCPServer("yourquantum")
api_client = YourQuantumApiClient()


# ---------------------------------------------------------------------------
# Tool 1: Multi-criteria Decision & Option Optimization
# ---------------------------------------------------------------------------

@server.tool(
    name="yq_optimize_options",
    description=(
        "Matematyczna optymalizacja wyboru podzbioru opcji/wariantów pod zadaną funkcją celu i ograniczeniami. "
        "WAŻNE — UCZCIWOŚĆ WYNIKU: Narzędzie zwraca optimum matematyczne ŚCIŚLE względem jawnie podanych kryteriów, "
        "wag i ograniczeń. NIE jest to 'obiektywnie najlepsza opcja'. Wymaga jawnego określenia wskaźnika celu i wag "
        "— brakujące parametry nie są domyślnie zgadywane, lecz zgłaszane jako błąd."
    ),
)
async def optimize_options(
    title: str,
    options: List[Dict[str, Any]],
    objective_direction: Literal["maximize", "minimize"],
    objective_attribute: Optional[str] = None,
    objective_coefficients: Optional[Dict[str, float]] = None,
    budget_limit: Optional[float] = None,
    budget_attribute: Optional[str] = None,
    exact_count: Optional[int] = None,
    min_options: Optional[int] = None,
    max_options: Optional[int] = None,
    incompatible_pairs: Optional[List[List[str]]] = None,
    solver: Literal["auto", "hybrid_benders", "qaoa", "cpsat"] = "auto",
    domain: str = "general",
    criteria_matrix: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Kompiluje i rozwiązuje problem decyzyjny z pełną weryfikacją matematyczną.
    """
    # 1. Walidacja obecności tytułu
    if not title or not title.strip():
        return (
            "BŁĄD WALIDACJI: Brak tytułu dylematu (`title`). "
            "Podaj zwięzły opis lub nazwę problemu decyzyjnego, który analizujesz."
        )

    # 2. Walidacja liczby opcji
    if not options or len(options) < 2:
        return (
            f"BŁĄD WALIDACJI: Do porównania i optymalizacji wymagane są co najmniej 2 warianty (`options`). "
            f"Otrzymano: {len(options) if options else 0}."
        )

    # 3. Walidacja struktury opcji
    formatted_variables: List[Dict[str, Any]] = []
    for idx, opt in enumerate(options):
        opt_id = str(opt.get("id") or f"opt_{idx + 1}").strip()
        opt_name = str(opt.get("name") or opt.get("title") or opt_id).strip()
        if not opt_name:
            return f"BŁĄD WALIDACJI: Opcja o indeksie {idx} nie posiada czytelnej nazwy (`name`)."

        # Wydobądź atrybuty
        attrs = dict(opt.get("attributes") or {})
        for k, v in opt.items():
            if k not in ("id", "name", "title", "attributes", "cost", "value"):
                attrs[k] = v

        cost_val = opt.get("cost")
        value_val = opt.get("value")

        formatted_variables.append({
            "id": opt_id,
            "name": opt_name,
            "cost": float(cost_val) if cost_val is not None else None,
            "value": float(value_val) if value_val is not None else None,
            "attributes": attrs,
        })

    # 4. Sprawdzenie kryterium funkcji celu (zero cichych domyślności)
    if not objective_attribute and not objective_coefficients:
        return (
            "BŁĄD METRYKI CELU: Nie określono kryterium optymalizacji. "
            "Musisz jawnie wskazać `objective_attribute` (np. 'value', 'cost', 'score', 'expected_roi') "
            "LUB przekazać słownik wag `objective_coefficients`. "
            "Silnik YourQuantum nie podstawia domyślnych założeń bez Twojej wiedzy."
        )

    if objective_attribute:
        # Sprawdź, czy każda opcja ma zdefiniowaną wartość tego atrybutu
        for var in formatted_variables:
            has_attr = (
                (objective_attribute == "cost" and var["cost"] is not None) or
                (objective_attribute == "value" and var["value"] is not None) or
                (objective_attribute in var["attributes"])
            )
            if not has_attr:
                return (
                    f"BŁĄD BRAKUJĄCEJ WARTOŚCI: Opcja '{var['name']}' (ID: {var['id']}) nie posiada "
                    f"określonej wartości atrybutu celu '{objective_attribute}'. "
                    f"Uzupełnij tę metrykę dla wszystkich wariantów przed uruchomieniem optymalizacji."
                )

    # 5. Sprawdzenie ograniczeń budżetowych
    constraints: List[Dict[str, Any]] = []
    if budget_limit is not None:
        if not budget_attribute:
            return (
                f"BŁĄD OGRANICZENIA: Podano limit zasobu (`budget_limit = {budget_limit}`), "
                f"ale nie wskazano podlegającego mu atrybutu (`budget_attribute`, np. 'cost', 'weight', 'time_hours'). "
                f"Wskaż, który atrybut opcji ma być ograniczony tym limitem."
            )
        # Sprawdź obecność atrybutu budżetowego w opcjach
        for var in formatted_variables:
            has_b_attr = (
                (budget_attribute == "cost" and var["cost"] is not None) or
                (budget_attribute in var["attributes"])
            )
            if not has_b_attr:
                return (
                    f"BŁĄD OGRANICZENIA: Opcja '{var['name']}' (ID: {var['id']}) nie posiada zdefiniowanego "
                    f"atrybutu budżetowego '{budget_attribute}'. Uzupełnij dane kosztowe/zasobowe."
                )
        constraints.append({
            "name": f"Limit zasobu: {budget_attribute} <= {budget_limit}",
            "type": "budget",
            "attribute": budget_attribute,
            "limit": float(budget_limit),
        })

    # 6. Ograniczenia liczności (kardynalności)
    if exact_count is not None:
        constraints.append({
            "name": f"Wybór dokładnie {exact_count} opcji",
            "type": "cardinality_exact",
            "count": int(exact_count),
        })
    else:
        if min_options is not None:
            constraints.append({
                "name": f"Minimalna liczba opcji: {min_options}",
                "type": "cardinality_min",
                "count": int(min_options),
            })
        if max_options is not None:
            constraints.append({
                "name": f"Maksymalna liczba opcji: {max_options}",
                "type": "cardinality_max",
                "count": int(max_options),
            })

    # 7. Wykluczenia wzajemne (incompatible pairs)
    if incompatible_pairs:
        for idx, pair in enumerate(incompatible_pairs):
            if len(pair) == 2:
                constraints.append({
                    "name": f"Wykluczenie wzajemne: {pair[0]} vs {pair[1]}",
                    "type": "incompatible",
                    "var_ids": pair,
                })

    # 8. Przygotowanie żądania do silnika
    payload = {
        "title": title.strip(),
        "domain": domain,
        "variables": formatted_variables,
        "objective_direction": objective_direction,
        "objective_attribute": objective_attribute,
        "objective_coefficients": objective_coefficients or {},
        "constraints": constraints,
        "solver": solver,
        "include_stress_test": True,
    }

    try:
        res = await api_client.universal_compute(payload)
    except YourQuantumApiError as e:
        return f"BŁĄD PODCZAS OBLICZEŃ YOURQUANTUM: {e.message}"
    except Exception as e:
        return f"BŁĄD SERWERA MCP: {str(e)}"

    # 9. Formatowanie czytelnego, uczciwego podsumowania
    selected_items = res.get("optimal_selection", [])
    total_obj = res.get("total_objective_value", 0.0)
    solver_used = res.get("solver_used", "unknown")
    proven = res.get("optimality_proven", False)
    sha_passport = res.get("sha256_passport", "n/a")
    sensitivity = res.get("sensitivity_report") or {}
    optimality_gap = res.get("optimality_gap_percent")

    selected_ids = {item["id"] for item in selected_items}
    unselected_items = [v for v in formatted_variables if v["id"] not in selected_ids]

    summary_lines = [
        "## 🔬 WYNIK OPTYMALIZACJI DECYZYJNEJ YOURQUANTUM",
        "",
        "> ⚠️ **UCZCIWOŚĆ I INTERPRETACJA WYNIKU:**",
        "> Przedstawione rozwiązanie stanowi matematyczne optimum wyznaczone **ŚCIŚLE względem poniższych kryteriów i założeń** podanych na wejściu.",
        "> Narzędzie nie określa „obiektywnie najlepszej opcji w sensie absolutnym” — oblicza matematycznie najlepszy zbiór dla zdefiniowanej funkcji celu w ramach dopuszczalnych ograniczeń.",
        "",
        "### 1. Przyjęte założenia i kryteria wejściowe:",
        f"- **Kierunek celu**: `{objective_direction.upper()}`",
        f"- **Atrybut optymalizowany**: `{objective_attribute or 'współczynniki wagowe'}`",
    ]

    if budget_limit is not None:
        summary_lines.append(f"- **Limit budżetowy**: `{budget_attribute}` ≤ `{budget_limit}`")
    if exact_count is not None:
        summary_lines.append(f"- **Warunek liczności**: dokładnie `{exact_count}` wariantów")
    if incompatible_pairs:
        summary_lines.append(f"- **Wzajemne wykluczenia**: `{len(incompatible_pairs)}` par")

    summary_lines.extend([
        "",
        f"### 2. Wybór optymalny ({len(selected_items)} z {len(formatted_variables)} wariantów):",
    ])

    for item in selected_items:
        details = []
        if item.get("cost") is not None:
            details.append(f"koszt: {item['cost']}")
        if item.get("value") is not None:
            details.append(f"wartość: {item['value']}")
        for ak, av in (item.get("attributes") or {}).items():
            details.append(f"{ak}: {av}")
        details_str = f" ({', '.join(details)})" if details else ""
        summary_lines.append(f"- ✅ **{item['name']}** (ID: `{item['id']}`){details_str}")

    if unselected_items:
        summary_lines.extend([
            "",
            "### 3. Odrzucone warianty alternatywne:",
        ])
        for item in unselected_items:
            summary_lines.append(f"- ❌ {item['name']} (ID: `{item['id']}`)")

    summary_lines.extend([
        "",
        "### 4. Metryki i audyt obliczeniowy:",
        f"- **Wartość funkcji celu**: `{total_obj:,.2f}`",
        f"- **Rzeczywiste źródło obliczeń**: `{res.get('source', res.get('compute_source', 'KLASYCZNY_SOLVER'))}`",
        f"- **Zastosowany silnik**: `{solver_used}`",
        f"- **Dowód optymalności**: `{'TAK (Globalne Optimum Udowodnione)' if proven else 'Przybliżone (Heurystyka)'}`"
        + (f" (Luka optymalności: `{optimality_gap:.2f}%`)" if optimality_gap is not None else ""),
        f"- **Paszport integralności SHA-256**: `{sha_passport}`",
    ])

    routing_record = res.get("routing_record") or (res.get("metadata") or {}).get("routing_record")
    if routing_record:
        rec_solver = routing_record.get("recommended_solver", solver_used)
        comparisons = routing_record.get("comparison_solvers", [])
        summary_lines.append(f"- **Rekomendacja routera**: `{rec_solver}`" + (f" (porównano z: {', '.join(comparisons)})" if comparisons else ""))

    if sensitivity:
        summary_lines.extend([
            f"- **Odporność na wstrząsy (Stress-Testing ±25%)**: `{sensitivity.get('verdict', 'N/A')}` (Wynik: `{sensitivity.get('robustness_score', 0):.1f}/100`)",
            f"- **Wnioski ze stabilności**: {sensitivity.get('summary_pl', '')}",
        ])

    return "\n".join(summary_lines)


# ---------------------------------------------------------------------------
# Tool 2: Portfolio & Capital Allocation
# ---------------------------------------------------------------------------

@server.tool(
    name="yq_solve_portfolio",
    description=(
        "Optymalizacja alokacji kapitału i doboru projektów inwestycyjnych pod zadanym nieprzekraczalnym budżetem. "
        "Maksymalizuje łączną wartość (lub zwrot z inwestycji ROI) przy spełnieniu ograniczenia kosztowego. "
        "Wymaga jawnego podania budżetu oraz kosztu i wartości dla każdego projektu."
    ),
)
async def solve_portfolio(
    projects: List[Dict[str, Any]],
    budget_limit: float,
    budget_attribute: str = "cost",
    objective_attribute: str = "value",
    title: str = "Optymalizacja Portfela Projektów",
) -> str:
    """
    Wyspecjalizowana alokacja portfela zadań/projektów pod kątem budżetu.
    """
    if budget_limit is None or float(budget_limit) <= 0:
        return "BŁĄD WALIDACJI: Wymagane jest podanie dodatniego limitu budżetowego (`budget_limit > 0`)."

    if not projects or len(projects) < 2:
        return f"BŁĄD WALIDACJI: Wymagane są co najmniej 2 projekty do wyboru. Otrzymano: {len(projects) if projects else 0}."

    for p in projects:
        p_name = p.get("name") or p.get("id") or "Bez nazwy"
        if budget_attribute not in p and "cost" not in p:
            return (
                f"BŁĄD DANYCH: Projekt '{p_name}' nie posiada określonego kosztu/nakładu "
                f"w polu '{budget_attribute}' ani 'cost'. Uzupełnij tę liczbę."
            )
        if objective_attribute not in p and "value" not in p:
            return (
                f"BŁĄD DANYCH: Projekt '{p_name}' nie posiada określonej wartości/zysku "
                f"w polu '{objective_attribute}' ani 'value'. Uzupełnij tę liczbę."
            )

    return await optimize_options(
        title=title,
        options=projects,
        objective_direction="maximize",
        objective_attribute=objective_attribute,
        budget_limit=float(budget_limit),
        budget_attribute=budget_attribute,
        domain="finance",
    )


# ---------------------------------------------------------------------------
# Tool 3: Input Quality Gate & Dilemma Analysis
# ---------------------------------------------------------------------------

@server.tool(
    name="yq_analyze_dilemma",
    description=(
        "Weryfikacja jakości sformułowania dylematu decyzyjnego za pomocą Input Quality Gate YourQuantum. "
        "Bada, czy dylemat zawiera wystarczającą liczbę wariantów, danych liczbowych (budżety, zyski, ryzyka) "
        "i jasnych ograniczeń. Wskazuje luki informacyjne i precyzyjne pytania, które należy zadać użytkownikowi."
    ),
)
async def analyze_dilemma(description: str) -> str:
    """
    Analizuje dylemat użytkownika i sprawdza jakość danych przed przystąpieniem do optymalizacji.
    """
    if not description or len(description.strip()) < 5:
        return "BŁĄD WALIDACJI: Treść dylematu (`description`) musi mieć co najmniej 5 znaków."

    try:
        res = await api_client.analyze_dilemma(description)
    except YourQuantumApiError as e:
        return f"BŁĄD PODCZAS ANALIZY DYLEMATU: {e.message}"
    except Exception as e:
        return f"BŁĄD SERWERA MCP: {str(e)}"

    input_quality_data = res.get("input_quality") or {}
    if isinstance(input_quality_data, dict):
        quality_level = str(input_quality_data.get("level", "unknown"))
        reason = input_quality_data.get("reason", "")
        suggestions = input_quality_data.get("suggestions", [])
    else:
        quality_level = str(input_quality_data)
        reason = ""
        suggestions = []

    title = res.get("title", "Analiza dylematu")
    options = res.get("options", [])
    criteria = res.get("criteria", [])
    unknowns = res.get("unknowns", [])

    lines = [
        f"## 🔍 ANALIZA DYLEMATU DECYZYJNEGO: {title}",
        f"- **Ocena kompletności danych (Input Quality Gate)**: `{quality_level.upper()}`",
    ]
    if reason:
        lines.append(f"- **Uzasadnienie oceny**: {reason}")
    lines.append("")

    if quality_level == "too_vague":
        lines.append(
            "⚠️ **Dylemat jest zbyt ogólnikowy.** "
            "Użytkownik nie podał konkretnych opcji ani kryteriów oceny. Należy zebrać więcej szczegółów przed uruchomieniem solvera."
        )
    elif quality_level == "needs_options":
        lines.append(
            "⚠️ **Brakuje zdefiniowanych alternatyw.** "
            "Problem opisuje sytuację, ale nie definiuje konkretnych wariantów do wyboru (minimum 2)."
        )
    elif quality_level == "needs_numbers":
        lines.append(
            "⚠️ **Brakuje danych liczbowych.** "
            "Zidentyfikowano opcje, ale brak kosztów, budżetów lub wag numerycznych niezbędnych do rzetelnej optymalizacji."
        )
    else:
        lines.append("✅ **Dane są kompletne (`SUFFICIENT`).** Dylemat nadaje się do bezpośredniej optymalizacji.")

    if suggestions:
        lines.extend(["", "### Sugestie uzupełnienia danych:"])
        for s in suggestions:
            lines.append(f"- 💡 {s}")

    if options:
        lines.extend(["", "### Zidentyfikowane warianty:"])
        for opt in options:
            opt_title = opt.get("title") or opt.get("name") or "Wariant"
            lines.append(f"- **{opt_title}**: {opt.get('description', '')}")

    if criteria:
        lines.extend(["", "### Zidentyfikowane kryteria:"])
        for c in criteria:
            lines.append(f"- **{c.get('name')}** (kierunek: `{c.get('direction', 'maximize')}`, waga: {c.get('weight', 1.0)})")

    if unknowns:
        lines.extend(["", "### Pytania doprecyzowujące dla użytkownika:"])
        for unk in unknowns:
            lines.append(f"- ❓ {unk.get('question', '')} ({unk.get('impact_description', '')})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: Engine Status & Available Solvers
# ---------------------------------------------------------------------------

@server.tool(
    name="yq_get_engine_status",
    description=(
        "Sprawdza status serwisu YourQuantum API oraz raportuje dostępne silniki obliczeniowe "
        "(klasyczne np. CP-SAT oraz kwantowe np. QAOA i Hybrid Benders)."
    ),
)
async def get_engine_status() -> str:
    """
    Zwraca diagnostykę łączności i listę solverów.
    """
    try:
        res = await api_client.get_solvers_health()
    except YourQuantumApiError as e:
        return f"BŁĄD POŁĄCZENIA Z YOURQUANTUM: {e.message}"
    except Exception as e:
        return f"BŁĄD SERWERA MCP: {str(e)}"

    solvers = res.get("solvers", [])
    lines = [
        "## ⚡ STATUS SILNIKA YOURQUANTUM",
        f"- **Adres bazowy API**: `{api_client.base_url}`",
        f"- **Autoryzacja YQ_API_KEY**: `{'Zdefiniowany w środowisku' if api_client.api_key else 'Brak zmiennej YQ_API_KEY'}`",
        "",
        "### Dostępne adaptery solverów:",
    ]
    for s in solvers:
        lines.append(f"- 🔹 **{s.get('name')}** (wersja: `{s.get('version', '1.0')}`)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5: Brain-Inspired Cognitive Formalization & Intake
# ---------------------------------------------------------------------------

@server.tool(
    name="yq_cognitive_intake",
    description=(
        "Kognitywna formalizacja problemu decyzyjnego za pomocą architektury inspirowanej neurobiologią "
        "(Prefrontal Cortex Working Memory, Hippocampal Episodic Recall, Active Inference błędu predykcji). "
        "Przekształca surowy opis użytkownika w zwalidowany model ProblemIR, eliminuje sprzeczności i halucynacje "
        "oraz przygotowuje dylemat do natychmiastowego rozwiązania przez silniki kwantowe i klasyczne."
    ),
)
async def cognitive_intake(query: str) -> str:
    """
    Uruchamia orkiestrację kognitywną YourQuantum na zadanym dylemacie.
    """
    if not query or len(query.strip()) < 3:
        return "BŁĄD WALIDACJI: Treść problemu (`query`) musi mieć co najmniej 3 znaki."

    try:
        res = await api_client.cognitive_intake(query)
    except YourQuantumApiError as e:
        return f"BŁĄD ORKIESTRACJI KOGNITYWNEJ: {e.message}"
    except Exception as e:
        return f"BŁĄD SERWERA MCP: {str(e)}"

    status = res.get("status", "unknown")
    explanation = res.get("explanation", "")
    questions = res.get("questions", [])
    confidence = res.get("confidence", 1.0)
    ir = res.get("problem_ir")

    lines = [
        "## 🧠 KOGNITYWNY MÓZG DECYZYJNY YOURQUANTUM",
        f"- **Status formalizacji**: `{status.upper()}`",
        f"- **Pewność modelu (Confidence)**: `{confidence * 100:.0f}%`",
        f"- **Wyjaśnienie**: {explanation}",
    ]

    if questions:
        lines.extend(["", "### Pytania doprecyzowujące (Active Inference):"])
        for q in questions:
            lines.append(f"- ❓ {q}")

    if ir:
        vars_list = ir.get("variables", [])
        cons_list = ir.get("constraints", [])
        objs_list = ir.get("objectives", [])
        lines.extend([
            "",
            "### Wygenerowany model ProblemIR:",
            f"- **Liczba zmiennych decyzyjnych**: {len(vars_list)}",
            f"- **Liczba twardych ograniczeń**: {len(cons_list)}",
            f"- **Kierunek funkcji celu**: {objs_list[0].get('direction', 'minimize') if objs_list else 'brak'}",
            "",
            "Model jest zweryfikowany pod kątem spójności dziedzin i gotowy do rozwiązania solverem `yq_optimize_options` lub `yq_solve_portfolio`.",
        ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server over stdio transport."""
    logger.info("Uruchamianie serwera YourQuantum MCP (transport: stdio)...")
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
