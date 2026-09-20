from typing import Callable

from .store import EmbeddingStore

NO_DOCUMENTS = "Cơ sở tri thức chưa có tài liệu nào, không thể trả lời câu hỏi."
NO_MATCH = "Không tìm thấy tài liệu liên quan trong cơ sở tri thức."


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def build_prompt(self, question: str, results: list[dict]) -> str:
        """Lay the retrieved chunks out as numbered, attributable context blocks."""
        blocks = []
        for rank, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("doc_id") or result.get("id", "?")
            blocks.append(f"[{rank}] (nguồn: {source})\n{result.get('content', '').strip()}")

        return (
            "Bạn là trợ lý tra cứu quy định và dịch vụ thư viện.\n"
            "Chỉ trả lời dựa trên NGỮ CẢNH bên dưới, trích dẫn số nguồn [1], [2]... cho mỗi ý.\n"
            "Nếu ngữ cảnh không đủ thông tin, hãy nói rõ là không tìm thấy trong tài liệu, "
            "tuyệt đối không suy đoán quy định.\n"
            "Nếu một con số chỉ áp dụng cho một đối tượng (sinh viên / cán bộ, giảng viên), "
            "hãy nêu rõ đối tượng đó kèm con số.\n\n"
            f"--- NGỮ CẢNH ---\n{chr(10).join(blocks)}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- TRẢ LỜI ---"
        )

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return NO_DOCUMENTS

        results = self.store.search(question, top_k=top_k)
        if not results:
            return NO_MATCH

        return self.llm_fn(self.build_prompt(question, results))
