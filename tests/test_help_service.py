"""
Unit tests for the dynamic Help & Knowledge Service.
"""
import pytest
from backend.api.help_service import generate_help_knowledge_base, get_dynamic_engine_snapshot


def test_get_dynamic_engine_snapshot():
    snapshot = get_dynamic_engine_snapshot()
    assert snapshot.engine_version.startswith("0.3") or snapshot.engine_version.startswith("0.2")
    assert snapshot.active_solvers_count >= 1
    assert len(snapshot.solvers) >= 1
    assert any("cp_sat" in s["name"] for s in snapshot.solvers)
    assert len(snapshot.supported_dilemma_types) >= 3


def test_generate_help_knowledge_base():
    kb = generate_help_knowledge_base()
    assert len(kb.topics) >= 5
    assert len(kb.categories) >= 4
    assert len(kb.faq) >= 4
    assert len(kb.glossary) >= 3

    # Check that topics cover essential layperson guidance
    topic_ids = [t.id for t in kb.topics]
    assert "jak-zadawac-dylematy" in topic_ids
    assert "dlaczego-system-dopytuje" in topic_ids
    assert "suwaki-i-wagi" in topic_ids
    assert "kwantowa-optymalizacja" in topic_ids or "optymalizacja-kwantowa-dla-laika" in topic_ids
    assert "gwarancja-weryfikacji" in topic_ids
