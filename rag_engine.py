import logging
import os
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

_KB_PATH = Path(__file__).parent / "knowledge_base"


class RAGEngine:
    """Indexes pet care guideline documents and retrieves relevant chunks via ChromaDB."""

    def __init__(self, knowledge_base_path: str | Path = _KB_PATH):
        self.kb_path = Path(knowledge_base_path)
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection("pet_care_guidelines")
        self._indexed = False

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_documents(self) -> int:
        """Load and embed all .md files in the knowledge base directory.

        Returns the number of chunks indexed.
        """
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge base path not found: {self.kb_path}")

        docs, ids, metas = [], [], []
        for fpath in sorted(self.kb_path.glob("*.md")):
            text = fpath.read_text(encoding="utf-8")
            chunks = self._chunk(text)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{fpath.stem}_{i}"
                if chunk_id not in ids:  # guard against duplicates on re-index
                    docs.append(chunk)
                    ids.append(chunk_id)
                    metas.append({"source": fpath.name, "chunk_index": i})

        if not docs:
            logger.warning("No documents found in knowledge base at %s", self.kb_path)
            return 0

        self._collection.add(documents=docs, ids=ids, metadatas=metas)
        self._indexed = True
        logger.info("Indexed %d chunks from %s", len(docs), self.kb_path)
        return len(docs)

    @staticmethod
    def _chunk(text: str, min_len: int = 80) -> list[str]:
        """Split a document into paragraph-level chunks."""
        return [p.strip() for p in text.split("\n\n") if len(p.strip()) >= min_len]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, n_results: int = 4) -> list[dict]:
        """Retrieve the top-n most relevant chunks for a query.

        Returns a list of dicts with keys: text, source, distance.
        """
        if not self._indexed:
            self.index_documents()

        if self._collection.count() == 0:
            logger.warning("Collection is empty; nothing to retrieve.")
            return []

        actual_n = min(n_results, self._collection.count())
        results = self._collection.query(query_texts=[query], n_results=actual_n)

        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            source = results["metadatas"][0][i]["source"]
            distance = results["distances"][0][i]
            chunks.append({"text": doc, "source": source, "distance": distance})
            logger.info("Retrieved chunk from '%s' (distance=%.3f)", source, distance)

        return chunks

    def retrieve_for_pet(self, name: str, species: str, breed: str, age: int,
                         dietary_restrictions: list[str] = None,
                         medications: list[str] = None,
                         notes: list[str] = None) -> list[dict]:
        """Build a contextual query for a pet and retrieve relevant guidelines."""
        parts = [f"{species} {breed} age {age}"]
        if age <= 1:
            parts.append("puppy kitten young animal care")
        elif (species.lower() == "dog" and age >= 7) or (species.lower() == "cat" and age >= 10):
            parts.append("senior pet care")
        if dietary_restrictions:
            parts.append(f"dietary restrictions {' '.join(dietary_restrictions)}")
        if medications:
            parts.append(f"medication administration {' '.join(medications)}")
        if notes:
            parts.append(" ".join(notes))

        query = " ".join(parts)
        logger.info("RAG query for %s (%s): %s", name, species, query)
        return self.retrieve(query, n_results=4)
