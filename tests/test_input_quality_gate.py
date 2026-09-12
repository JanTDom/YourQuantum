import pytest

from backend.domain.llm_advisor import LLMAdvisor


def test_input_quality_assessment():
    advisor = LLMAdvisor()

    # 1. Too short / vague
    q_vague = advisor._assess_input_quality("Kupić czy nie?")
    assert q_vague.level == "too_vague"
    assert len(q_vague.suggestions) > 0

    # 2. Needs options (long enough, but no options or choices)
    q_no_opt = advisor._assess_input_quality("Bardzo chciałbym w przyszłości podróżować po całym świecie i zwiedzać egzotyczne kraje.")
    assert q_no_opt.level == "needs_options"

    # 3. Needs numbers in financial context
    q_no_num = advisor._assess_input_quality("Zastanawiam się czy wziąć kredyt na inwestycję w nieruchomości czy zachować oszczędności na lokacie.")
    assert q_no_num.level == "needs_numbers"

    # 4. Sufficient specific dilemma
    q_ok = advisor._assess_input_quality(
        "Mam budżet 50000 zł i zastanawiam się czy zainwestować w projekt A czy projekt B na 12 miesięcy."
    )
    assert q_ok.level == "sufficient"
    assert q_ok.reason == ""
