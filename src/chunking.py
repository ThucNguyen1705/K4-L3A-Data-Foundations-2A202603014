from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Lookbehind keeps the terminator attached to the sentence it closes,
        # so ". ", "! ", "? " and a newline after "." all split cleanly.
        sentences = [s.strip() for s in self.SENTENCE_BOUNDARY.split(text.strip()) if s.strip()]
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        return [
            " ".join(sentences[start : start + size])
            for start in range(0, len(sentences), size)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _hard_split(self, current_text: str) -> list[str]:
        """Last resort: cut on character count when no separator helps."""
        return [
            current_text[start : start + self.chunk_size]
            for start in range(0, len(current_text), self.chunk_size)
        ]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        # Base case: the fragment already fits, keep it whole.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case: separators exhausted (or the "" catch-all) -> cut by size.
        if not remaining_separators or remaining_separators[0] == "":
            return self._hard_split(current_text)

        separator, next_separators = remaining_separators[0], remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        buffer: list[str] = []
        buffer_len = 0

        def flush() -> None:
            nonlocal buffer, buffer_len
            if buffer:
                chunks.append(separator.join(buffer))
                buffer = []
                buffer_len = 0

        for part in current_text.split(separator):
            if not part:
                continue
            if len(part) > self.chunk_size:
                # Too big even alone: close the buffer, then recurse one level down.
                flush()
                chunks.extend(self._split(part, next_separators))
                continue

            extra = len(part) + (len(separator) if buffer else 0)
            if buffer_len + extra > self.chunk_size:
                flush()
                extra = len(part)
            buffer.append(part)
            buffer_len += extra

        flush()
        return chunks or self._hard_split(current_text)


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        runs = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }
        return {name: self._stats(chunks) for name, chunks in runs.items()}

    @staticmethod
    def _stats(chunks: list[str]) -> dict:
        total = sum(len(c) for c in chunks)
        return {
            "count": len(chunks),
            "avg_length": total / len(chunks) if chunks else 0.0,
            "chunks": chunks,
        }
