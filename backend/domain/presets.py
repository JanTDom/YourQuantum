"""
YourQuantum — Everyday Human Decision Presets
100% human language, zero academic jargon. Real-life decisions.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ProblemPreset(BaseModel):
    id: str
    title: str
    category: str
    description: str
    human_explanation: str
    human_rules: list[str] = Field(default_factory=list)
    variable_labels: dict[str, str] = Field(default_factory=dict)
    binary_variables: list[str]
    objective_coefficients: dict[str, float]
    objective_direction: str = "maximize"
    equality_constraints: list[dict[str, Any]] = Field(default_factory=list)
    time_limit: int = 15
    shots: int = 1024
    recommended_solver: str = "cp_sat"
    quantum_ready: bool = True
    tags: list[str] = Field(default_factory=list)
    image_slug: str = "quantum_chamber.jpg"


PRESETS: list[ProblemPreset] = [
    ProblemPreset(
        id="portfolio_selection",
        title="Wybór inwestycji firmowych",
        category="Finanse i rozwój",
        description="Masz 5 obiecujących pomysłów na rozwój firmy, ale budżet pozwala w tym kwartale uruchomić tylko 3. Które przyniosą największy zysk?",
        human_explanation="Algorytm sprawdza wszystkie kombinacje i wskazuje 3 projekty, które przyniosą najwyższy łączny zwrot finansowy.",
        human_rules=[
            "Wybieramy dokładnie 3 z 5 dostępnych projektów",
            "Maksymalizujemy łączny szacowany zysk dla firmy",
        ],
        variable_labels={
            "proj_AI": "Automatyzacja procesów z AI (+25 tys. zł zysku)",
            "proj_Sklep": "Nowy sklep internetowy i aplikacja (+20 tys. zł zysku)",
            "proj_Eksport": "Ekspansja na rynki zagraniczne (+18 tys. zł zysku)",
            "proj_Szkolenia": "Szkolenia i rozwój zespołu (+12 tys. zł zysku)",
            "proj_Biuro": "Nowy wystrój i sprzęt biurowy (+8 tys. zł zysku)",
        },
        binary_variables=["proj_AI", "proj_Sklep", "proj_Eksport", "proj_Szkolenia", "proj_Biuro"],
        objective_coefficients={
            "proj_AI": 25.0,
            "proj_Sklep": 20.0,
            "proj_Eksport": 18.0,
            "proj_Szkolenia": 12.0,
            "proj_Biuro": 8.0,
        },
        objective_direction="maximize",
        equality_constraints=[
            {
                "lhs": {
                    "proj_AI": 1.0,
                    "proj_Sklep": 1.0,
                    "proj_Eksport": 1.0,
                    "proj_Szkolenia": 1.0,
                    "proj_Biuro": 1.0,
                },
                "rhs": 3.0,
            }
        ],
        time_limit=15,
        shots=1024,
        recommended_solver="cp_sat",
        quantum_ready=True,
        tags=["inwestycje", "firma", "maksymalny zysk"],
        image_slug="quantum_chip.jpg",
    ),
    ProblemPreset(
        id="knapsack_01",
        title="Pakowanie bagażu na wyprawę",
        category="Życie codzienne i podróże",
        description="Szykujesz się na ważną podróż z limitem wagi. Musisz wybrać 2 najpotrzebniejsze zestawy rzeczy, które dadzą największy komfort.",
        human_explanation="System znajduje taki zestaw ekwipunku, który ma najwyższą wartość użytkową bez przekroczenia limitu.",
        human_rules=[
            "Możesz zabrać dokładnie 2 zestawy rzeczy",
            "Wybieramy opcje o najwyższej przydatności w podróży",
        ],
        variable_labels={
            "item_Aparat": "Sprzęt fotograficzny i dorn (przydatność: 10 pkt)",
            "item_Laptop": "Laptop do pracy zdalnej (przydatność: 25 pkt)",
            "item_Kurtka": "Odzież górska i buty (przydatność: 18 pkt)",
            "item_Apteczka": "Zestaw medyczny i filtry wody (przydatność: 22 pkt)",
        },
        binary_variables=["item_Aparat", "item_Laptop", "item_Kurtka", "item_Apteczka"],
        objective_coefficients={"item_Aparat": 10.0, "item_Laptop": 25.0, "item_Kurtka": 18.0, "item_Apteczka": 22.0},
        objective_direction="maximize",
        equality_constraints=[
            {"lhs": {"item_Aparat": 1.0, "item_Laptop": 1.0, "item_Kurtka": 1.0, "item_Apteczka": 1.0}, "rhs": 2.0}
        ],
        time_limit=15,
        shots=1024,
        recommended_solver="cp_sat",
        quantum_ready=True,
        tags=["bagaż", "podróże", "optymalny wybór"],
        image_slug="quantum_wave.jpg",
    ),
    ProblemPreset(
        id="maxcut_4cycle",
        title="Sprawiedliwy podział zespołu",
        category="Organizacja i ludzie",
        description="Masz 4 kluczowe osoby i musisz stworzyć 2 zbalansowane, dwuosobowe zespoły projektowe, aby kompetencje były równomiernie rozłożone.",
        human_explanation="Algorytm znajduje idealny podział ludzi na dwie grupy, unikając przewagi kompetencyjnej w jednym zespole.",
        human_rules=[
            "Każdy zespół musi liczyć dokładnie 2 osoby",
            "Maksymalizujemy synergię i zrównoważenie obu grup",
        ],
        variable_labels={
            "v0": "Anna (doświadczony analityk)",
            "v1": "Bartek (senior programista)",
            "v2": "Celina (kierownik projektu)",
            "v3": "Dawid (ekspert sprzedaży)",
        },
        binary_variables=["v0", "v1", "v2", "v3"],
        objective_coefficients={"v0": 1.0, "v1": 1.0, "v2": 1.0, "v3": 1.0},
        objective_direction="maximize",
        equality_constraints=[
            {"lhs": {"v0": 1.0, "v1": 1.0, "v2": 1.0, "v3": 1.0}, "rhs": 2.0}
        ],
        time_limit=15,
        shots=1024,
        recommended_solver="qaoa_aer",
        quantum_ready=True,
        tags=["zespół", "ludzie", "równowaga"],
        image_slug="quantum_chamber.jpg",
    ),
    ProblemPreset(
        id="job_allocation",
        title="Harmonogram ważnych zadań",
        category="Czas i efektywność",
        description="W tym tygodniu musisz obsadzić 2 kluczowe dyżury spośród 3 możliwych, minimalizując koszty i obciążenie zespołu.",
        human_explanation="System dobiera terminy tak, aby zrealizować kluczowe obowiązki przy najniższym koszcie.",
        human_rules=[
            "Trzeba obsadzić dokładnie 2 kluczowe dyżury",
            "Minimalizujemy łączny koszt realizacji",
        ],
        variable_labels={
            "task_1": "Dyżur weekendowy (koszt: 400 zł)",
            "task_2": "Wsparcie techniczne w dzień (koszt: 200 zł)",
            "task_3": "Nocny dyżur awaryjny (koszt: 500 zł)",
        },
        binary_variables=["task_1", "task_2", "task_3"],
        objective_coefficients={"task_1": 4.0, "task_2": 2.0, "task_3": 5.0},
        objective_direction="minimize",
        equality_constraints=[
            {"lhs": {"task_1": 1.0, "task_2": 1.0, "task_3": 1.0}, "rhs": 2.0}
        ],
        time_limit=15,
        shots=1024,
        recommended_solver="cp_sat",
        quantum_ready=True,
        tags=["grafik", "czas", "niskie koszty"],
        image_slug="quantum_chip.jpg",
    ),
]


def get_all_presets() -> list[ProblemPreset]:
    return PRESETS


def get_preset_by_id(preset_id: str) -> ProblemPreset | None:
    return next((p for p in PRESETS if p.id == preset_id), None)
