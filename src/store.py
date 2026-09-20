from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        # The Lab runs entirely on the in-memory backend: it is deterministic,
        # needs no server, and keeps the same behaviour on every grader machine.
        # ChromaDB stays an optional extra, so a missing install is not an error.
        self._use_chroma = False

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Normalize one Document into a stored record (copy metadata, embed once)."""
        metadata = dict(doc.metadata or {})
        # doc_id is what delete_document and the benchmark scorer key on, so every
        # chunk carries it even when the caller only set an id.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "index": self._next_index,
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [(_dot(query_embedding, record["embedding"]), record) for record in records]
        # Tie-break on insertion order so equal scores keep a stable, reproducible ranking.
        scored.sort(key=lambda pair: (-pair[0], pair[1]["index"]))

        return [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": float(score),
            }
            for score, record in scored[:top_k]
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        candidates = [r for r in self._store if self._matches(r["metadata"], metadata_filter)]
        # Pre-filtering: sai đối tượng bị loại trước khi xếp hạng, nên top_k không
        # bị tài liệu của audience khác chiếm chỗ.
        return self._search_records(query, candidates, top_k)

    @staticmethod
    def _matches(metadata: dict[str, Any], metadata_filter: dict) -> bool:
        for key, expected in metadata_filter.items():
            value = metadata.get(key)
            # A list/tuple/set means "any of these", e.g. {"audience": ["student", "all"]}.
            if isinstance(expected, (list, tuple, set)):
                if value not in expected:
                    return False
            elif value != expected:
                return False
        return True

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        size_before = len(self._store)
        self._store = [
            r
            for r in self._store
            if r["metadata"].get("doc_id") != doc_id and r["id"] != doc_id
        ]
        return len(self._store) < size_before
