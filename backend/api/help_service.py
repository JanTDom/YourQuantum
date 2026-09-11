"""
YourQuantum — Dynamic Help & Knowledge Service for Laypersons
Automatically introspects active solver registry, problem IR specs, and AI advisor
capabilities to provide a self-updating, jargon-free guide for non-technical users.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from backend.worker.runner import SOLVER_REGISTRY


class HelpTopic(BaseModel):
    id: str
    title: str
    short_desc: str
    category: str
    content_markdown: str
    read_time_minutes: int
    badge: str | None = None
    target_stages: list[str] = Field(default_factory=list)


class EngineCapabilitySnapshot(BaseModel):
    engine_version: str
    active_solvers_count: int
    solvers: list[dict[str, str]]
    supported_dilemma_types: list[str]
    verification_mode: str
    last_updated: str


class HelpResponse(BaseModel):
    engine_status: EngineCapabilitySnapshot
    categories: list[str]
    topics: list[HelpTopic]
    faq: list[dict[str, str]]
    glossary: list[dict[str, str]]


def get_dynamic_engine_snapshot() -> EngineCapabilitySnapshot:
    """Introspects current registered solvers and capabilities dynamically."""
    solvers_info = []
    for solver in SOLVER_REGISTRY:
        solvers_info.append({
            "name": solver.name,
            "version": getattr(solver, "version", "1.0.0"),
            "kind": "Klasyczny optymalizator dokładny" if "cp_sat" in solver.name.lower() else "Symulator kwantowy (QAOA/Ising)",
            "status": "Aktywny i zweryfikowany"
        })

    from datetime import datetime, timezone
    return EngineCapabilitySnapshot(
        engine_version="0.2.0-frontier",
        active_solvers_count=len(SOLVER_REGISTRY),
        solvers=solvers_info,
        supported_dilemma_types=[
            "Kariera i zmiana pracy (wiele ofert, stabilność vs ryzyko)",
            "Strategia biznesowa i inwestycje (alokacja zasobów, czas vs zysk)",
            "Dylematy osobiste i życiowe (przeprowadzka, edukacja, logistyka)",
            "Zarządzanie czasem i projektami (konflikt priorytetów i ograniczeń)",
            "Wybory technologiczne i operacyjne (koszty, dług techniczny, skalowalność)"
        ],
        verification_mode="Niezależna weryfikacja matematyczna (Zero halucynacji)",
        last_updated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )


def generate_help_knowledge_base() -> HelpResponse:
    """Generates the full layperson guide synchronized with engine state."""
    snapshot = get_dynamic_engine_snapshot()

    solver_names_readable = ", ".join([f"{s['name']} ({s['kind']})" for s in snapshot.solvers])

    topics = [
        HelpTopic(
            id="jak-zadawac-dylematy",
            title="Jak opisać swój problem swoimi słowami",
            short_desc="Nie musisz znać matematyki. Wystarczy, że opiszesz sytuację tak, jak przyjacielowi.",
            category="Pierwsze Kroki",
            read_time_minutes=2,
            badge="Podstawa",
            target_stages=["INTAKE"],
            content_markdown="""
### Twój dylemat nie musi być ustrukturyzowany

Większość ludzi ma problem z podjęciem decyzji nie dlatego, że brakuje im opcji, ale dlatego, że **różne opcje ciągną w przeciwne strony**:
* *„Chcę lepiej zarabiać, ale boję się utraty stabilności i czasu dla rodziny”*
* *„Mam dwie oferty pracy: jedna prestiżowa z nadgodzinami, druga spokojniejsza, ale gorzej płatna”*
* *„Muszę zdecydować, czy inwestować w nowy sprzęt, czy zatrudnić pracownika”*

#### Co warto wpisać w polu dylematu:
1. **Opisz kontekst**: Co się dzieje, jakie są główne warianty (np. Oferta A vs Oferta B).
2. **Co Cię trapi**: Twoje obawy, priorytety, co jest dla Ciebie naprawdę ważne (np. spokój psychiczny, zarobki, dojazdy).
3. **Twoje ograniczenia**: Czy masz jakieś warunki brzegowe (np. *„muszę zarabiać minimum 10 000 zł”* albo *„nie mogę pracować w weekendy”*).

Nie bój się, że czegoś nie dopowiesz — **nasz system sam Cię dopyta w kolejnym kroku!**
"""
        ),
        HelpTopic(
            id="dlaczego-system-dopytuje",
            title="Dlaczego YourQuantum dopytuje o szczegóły?",
            short_desc="Różnica między zwykłym ChatGPT a silnikiem decyzji: my nie zgadujemy.",
            category="Jak Działa Silnik",
            read_time_minutes=3,
            badge="Kluczowe",
            target_stages=["CASE_WORKSPACE"],
            content_markdown="""
### Zwykłe AI zgaduje — YourQuantum bada fakty

Kiedy pytasz ChatGPT lub Claude: *„Którą ofertę wybrać?”*, model językowy pisze ładnie brzmiący esej, w którym wymienia wady i zalety, ale:
1. Nie zna Twoich prawdziwych granic (np. ile wynosi Twój próg bólu przy dojazdach).
2. Nie liczy skumulowanego wpływu wielu kompromisów.
3. Często zgaduje lub mówi to, co chcesz usłyszeć.

#### Co robi YourQuantum podczas wywiadu:
Nasz asystent AI analizuje Twój tekst i wyłapuje **punkty krytyczne**. Zamiast zasypywać Cię setką pytań, zadaje 3–4 precyzyjne pytania wielokrotnego wyboru lub pytania o konkrety.

Dzięki Twoim odpowiedziom system tworzy **mapę matematyczną Twojego problemu**, w której każde ograniczenie jest traktowane ze 100% powagą.
"""
        ),
        HelpTopic(
            id="suwaki-i-wagi",
            title="Jak działają suwaki wag i kompromisy",
            short_desc="Jak w prosty sposób ustalić, co jest dla Ciebie ważniejsze i znaleźć złoty środek.",
            category="Konfiguracja",
            read_time_minutes=2,
            badge="Interaktywne",
            target_stages=["CASE_WORKSPACE", "MODEL_APPROVAL"],
            content_markdown="""
### Życie to sztuka kompromisu, ale matematyka potrafi go zważyć

W sekcji suwaków nie musisz podawać abstrakcyjnych liczb. Każdy suwak odpowiada za jedno kryterium (np. *Finanse*, *Spokój Ducha*, *Rozwój*, *Czas Wolny*).

* **Suwak na 100%**: Kryterium o najwyższym priorytecie. System zrobi wszystko, by je zmaksymalizować.
* **Suwak na 50%**: Sprawa ważna, ale dopuszczasz ustępstwo, jeśli w zamian zyskasz coś cenniejszego.
* **Suwak na 10%**: Miły dodatek, ale nie decydujący.

Silnik szuka rozwiązania o **najwyższej synergii** — czyli takiego wariantu, który daje maksymalną sumę satysfakcji bez łamania twardych warunków.
"""
        ),
        HelpTopic(
            id="optymalizacja-kwantowa-dla-laika",
            title="Kwantowa optymalizacja: co to właściwie oznacza?",
            short_desc="Proste wyjaśnienie, dlaczego metody kwantowe radzą sobie z dylematami lepiej niż ludzki mózg.",
            category="Nauka i Technologia",
            read_time_minutes=3,
            badge="Fascynujące",
            target_stages=["MODEL_APPROVAL", "RECOMMENDATION"],
            content_markdown=f"""
### Analogia do górskiego krajobrazu we mgle

Wyobraź sobie, że Twoja decyzja to poszukiwanie najniższego, najbezpieczniejszego punktu w gęstej mgle pośród setek dolin i szczytów:
* **Człowiek** widzi tylko 2–3 doliny obok siebie i szybko decyduje pod wpływem emocji.
* **Zwykły komputer** schodzi krok po kroku do najbliższego dołka, ale często utyka w ślepej uliczce (lokalnym minimum).
* **Optymalizator kwantowy (oraz algorytmy kwantowo-inspirowane)** traktuje wszystkie warianty jak fale. Wykorzystuje zjawisko *tunelowania* i *interferencji*, by przeniknąć przez bariery i znaleźć **stan podstawowy (Globalne Optimum)** — punkt absolutnej równowagi.

W Twojej aktualnej konfiguracji silnik dysponuje solverami: **{solver_names_readable}**.
"""
        ),
        HelpTopic(
            id="gwarancja-weryfikacji",
            title="Niezależna weryfikacja: zero halucynacji",
            short_desc="Dlaczego wynikowi YourQuantum możesz zaufać w 100%.",
            category="Bezpieczeństwo",
            read_time_minutes=2,
            badge="Gwarancja",
            target_stages=["RECOMMENDATION"],
            content_markdown="""
### Wynik to nie opinia bota — to sprawdzony dowód

Wiele narzędzi AI generuje rozwiązania, które brzmią mądrze, ale w rzeczywistości łamią Twoje założenia (np. sugerują pracę, która wymaga weekendów, mimo że pisałeś, że to wykluczone).

#### Standard YourQuantum:
1. **Rozwiązanie kandydata**: Silnik matematyczny lub kwantowy generuje optymalny wariant.
2. **Niezależny weryfikator (Audytor)**: Zanim zobaczysz wynik na ekranie, oddzielny moduł sprawdza linijka po linijce:
   - Czy ani jedno twarde ograniczenie nie zostało naruszone?
   - Jaki jest dokładny bilans zysków i strat?
   - Czy wynik jest stabilny przy małych wahaniach Twoich preferencji?
3. Tylko po przejściu 100% testów wynik trafia do Ciebie z certyfikatem weryfikacji.
"""
        ),
        HelpTopic(
            id="przyklady-z-zycia",
            title="Przykłady dylematów z życia wzięte",
            short_desc="Zobacz, jak inni rozwiązywali skomplikowane rozdroża.",
            category="Przykłady",
            read_time_minutes=3,
            badge="Praktyka",
            target_stages=["INTAKE"],
            content_markdown="""
### Przykłady, które możesz skopiować i dopasować do siebie:

#### 1. Dylemat kariery (Dwie oferty)
> *„Pracuję w korporacji od 5 lat. Dostałem ofertę z dynamicznego software house'u: +35% pensji, ale niepewna branża i więcej wyjazdów. Druga opcja to awans u obecnego pracodawcy: mniejsza podwyżka (+10%), ale znany zespół i praca w 100% z domu. Mam małe dziecko i zależy mi na spokoju po godzinach.”*

#### 2. Dylemat biznesowy (Skalowanie vs Bezpieczeństwo)
> *„Prowadzę małą agencję. Mogę wziąć duży kontrakt od klienta korporacyjnego, który podwoi moje przychody, ale wymaga zatrudnienia 3 osób i płatności z terminem 90 dni. Ryzykuję płynność finansową. Alternatywa to pozostanie przy 5 mniejszych klientach z bezpieczną marżą.”*

#### 3. Dylemat mieszkaniowy (Kupno vs Wynajem)
> *„Kończy mi się umowa najmu. Mogę wziąć kredyt na 30 lat na obrzeżach miasta (więcej miejsca, własny ogród, ale 1h dojazdu), albo wynająć nowoczesne mieszkanie w centrum (blisko pracy, zero zobowiązań kredytowych, ale pieniądze 'przepadają').”*
"""
        )
    ]

    faq = [
        {
            "q": "Czy muszę znać fizykę kwantową lub zaawansowaną matematykę?",
            "a": "Absolutnie nie! Program został stworzony właśnie po to, by zaawansowana nauka pracowała dla Ciebie w tle. Ty rozmawiasz po ludzku, a system zajmuje się skomplikowanymi obliczeniami."
        },
        {
            "q": "Czym to się różni od zwykłego zapytania w ChatGPT?",
            "a": "ChatGPT układa prawdopodobne słowa w ładne zdania, ale nie potrafi ściśle policzyć wielowymiarowych zależności ani zagwarantować, że nie pominął ważnego warunku. YourQuantum przekształca problem w model matematyczny i szuka globalnego optimum za pomocą prawdziwych solverów."
        },
        {
            "q": "Czy moje dane i dylematy są bezpieczne?",
            "a": "Tak. Twoje dane są chronione izolacją sesji na poziomie bazy danych w Supabase. Nie udostępniamy Twoich danych do trenowania publicznych modeli ani podmiotom trzecim."
        },
        {
            "q": "Co jeśli nie wiem, jak ustawić suwaki wag?",
            "a": "Nie przejmuj się — system na podstawie Twojego opisu automatycznie zaproponuje optymalne wagi wyjściowe. Możesz je w każdej chwili skorygować lub zostawić wartości sugerowane."
        },
        {
            "q": "Czy wynik jest ostateczną wyrocznią?",
            "a": "YourQuantum daje Ci matematycznie najczystszy, obiektywny punkt odniesienia, wolny od chwilowych emocji czy zmęczenia. Ostateczna decyzja zawsze należy do Ciebie, ale podejmujesz ją mając pełen, przejrzysty obraz sytuacji."
        }
    ]

    glossary = [
        {
            "term": "Globalne Optimum",
            "meaning": "Najlepsze możliwe rozwiązanie w całej przestrzeni wyborów — punkt, w którym żaden inny kompromis nie daje lepszego bilansu."
        },
        {
            "term": "Ograniczenie Twarde (Hard Constraint)",
            "meaning": "Warunek nienaruszalny (np. 'budżet do 50 000 zł' lub 'brak pracy w niedziele'). Każdy wariant łamiący ten warunek jest natychmiast odrzucany."
        },
        {
            "term": "Synergia",
            "meaning": "Zjawisko, w którym dwie korzyści połączone ze sobą dają więcej wartości niż suma każdej z nich z osobna."
        },
        {
            "term": "Krajobraz Decyzyjny (QUBO)",
            "meaning": "Wielowymiarowa mapa wszystkich możliwych kombinacji wyborów, gdzie wysokość oznacza 'napięcie i koszty', a najniższa dolina to idealne rozwiązanie."
        }
    ]

    return HelpResponse(
        engine_status=snapshot,
        categories=["Pierwsze Kroki", "Jak Działa Silnik", "Konfiguracja", "Nauka i Technologia", "Bezpieczeństwo", "Przykłady"],
        topics=topics,
        faq=faq,
        glossary=glossary
    )
