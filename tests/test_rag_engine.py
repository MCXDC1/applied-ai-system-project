import pytest
from pathlib import Path

from rag_engine import RAGEngine


# ---------------------------------------------------------------------------
# RAGEngine._chunk (static — no external deps)
# ---------------------------------------------------------------------------

def test_chunk_splits_on_double_newline():
    text = (
        "First paragraph with more than eighty characters of content so it passes the minimum length filter.\n\n"
        "Second paragraph with more than eighty characters of content so it passes the minimum length filter."
    )
    chunks = RAGEngine._chunk(text)
    assert len(chunks) == 2


def test_chunk_filters_short_paragraphs():
    text = (
        "Too short.\n\n"
        "This paragraph is definitely long enough to pass the eighty-character minimum length filter used here."
    )
    chunks = RAGEngine._chunk(text)
    assert len(chunks) == 1
    assert "definitely long enough" in chunks[0]


def test_chunk_strips_whitespace():
    text = "  \n  This padded paragraph is long enough to pass the eighty-character minimum length check in RAGEngine.  \n  "
    chunks = RAGEngine._chunk(text)
    assert chunks[0] == chunks[0].strip()


def test_chunk_empty_string_returns_empty():
    assert RAGEngine._chunk("") == []


def test_chunk_all_short_returns_empty():
    assert RAGEngine._chunk("Hi.\n\nBye.\n\nOk.") == []


# ---------------------------------------------------------------------------
# RAGEngine.index_documents
# ---------------------------------------------------------------------------

def test_index_documents_raises_on_missing_path(tmp_path):
    engine = RAGEngine(knowledge_base_path=tmp_path / "nonexistent")
    with pytest.raises(FileNotFoundError):
        engine.index_documents()


def test_index_documents_returns_zero_on_empty_dir(tmp_path):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    count = engine.index_documents()
    assert count == 0


def test_index_documents_indexes_md_files(tmp_path):
    (tmp_path / "guide.md").write_text(
        "Dogs need daily exercise, regular feeding, and fresh water available at all times throughout the day.\n\n"
        "Cats are independent animals that require mental enrichment, playtime, and a clean litter box daily.\n\n"
        "Senior pets may need modified activity levels, softer food, and more frequent veterinary check-ups."
    )
    engine = RAGEngine(knowledge_base_path=tmp_path)
    count = engine.index_documents()
    assert count == 3


def test_index_documents_ignores_non_md_files(tmp_path):
    (tmp_path / "notes.txt").write_text(
        "This is a text file that should not be indexed by the RAG engine at all."
    )
    engine = RAGEngine(knowledge_base_path=tmp_path)
    count = engine.index_documents()
    assert count == 0


# ---------------------------------------------------------------------------
# RAGEngine.retrieve
# ---------------------------------------------------------------------------

def test_retrieve_returns_list_of_dicts(tmp_path):
    (tmp_path / "dogs.md").write_text(
        "Dogs need regular walks and outdoor exercise every day.\n\n"
        "Feeding dogs twice a day with high-quality protein is recommended.\n\n"
        "Dogs benefit from socialization with other animals and people."
    )
    engine = RAGEngine(knowledge_base_path=tmp_path)
    engine.index_documents()
    results = engine.retrieve("dog exercise")
    assert isinstance(results, list)
    assert all("text" in r and "source" in r and "distance" in r for r in results)


def test_retrieve_empty_collection_returns_empty(tmp_path, monkeypatch):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    engine._indexed = True  # skip auto-index so we control collection state
    monkeypatch.setattr(engine._collection, "count", lambda: 0)
    assert engine.retrieve("anything") == []


def test_retrieve_n_results_respected(tmp_path):
    lines = "\n\n".join(
        [f"This is pet care guideline number {i} and has enough text to be indexed." for i in range(10)]
    )
    (tmp_path / "many.md").write_text(lines)
    engine = RAGEngine(knowledge_base_path=tmp_path)
    engine.index_documents()
    results = engine.retrieve("pet care", n_results=2)
    assert len(results) <= 2


# ---------------------------------------------------------------------------
# RAGEngine.retrieve_for_pet — query construction
# ---------------------------------------------------------------------------

def test_retrieve_for_pet_puppy_adds_young_animal_terms(tmp_path, monkeypatch):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    captured = {}

    def fake_retrieve(query, n_results=4):
        captured["query"] = query
        return []

    monkeypatch.setattr(engine, "retrieve", fake_retrieve)
    engine.retrieve_for_pet(name="Pip", species="dog", breed="Poodle", age=0)
    assert "puppy" in captured["query"] or "young" in captured["query"]


def test_retrieve_for_pet_senior_dog_adds_senior_terms(tmp_path, monkeypatch):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    captured = {}

    def fake_retrieve(query, n_results=4):
        captured["query"] = query
        return []

    monkeypatch.setattr(engine, "retrieve", fake_retrieve)
    engine.retrieve_for_pet(name="Rex", species="dog", breed="Labrador", age=8)
    assert "senior" in captured["query"]


def test_retrieve_for_pet_senior_cat_adds_senior_terms(tmp_path, monkeypatch):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    captured = {}

    def fake_retrieve(query, n_results=4):
        captured["query"] = query
        return []

    monkeypatch.setattr(engine, "retrieve", fake_retrieve)
    engine.retrieve_for_pet(name="Mittens", species="cat", breed="Siamese", age=11)
    assert "senior" in captured["query"]


def test_retrieve_for_pet_includes_medications(tmp_path, monkeypatch):
    engine = RAGEngine(knowledge_base_path=tmp_path)
    captured = {}

    def fake_retrieve(query, n_results=4):
        captured["query"] = query
        return []

    monkeypatch.setattr(engine, "retrieve", fake_retrieve)
    engine.retrieve_for_pet(name="Rex", species="dog", breed="Lab", age=4, medications=["insulin"])
    assert "insulin" in captured["query"]
