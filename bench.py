"""
bench.py — Đo chất lượng truy xuất + câu trả lời của RAG agent trên corpus Thư viện UTH.

Nhóm RAUMAMIENTAY — Lab 7 (K4-L3A).
Thành viên: Nguyễn Đăng Thực (2A202603014) — vai R1 · Data.
Chiến lược cá nhân: FixedSizeChunker(chunk_size=400, overlap=80).

Chạy:  python bench.py          (đọc cấu hình embedding/LLM từ .env)
Kết quả ghi ra: ket_qua_benchmark.txt
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

# Console Windows mặc định là cp1252, không in được tiếng Việt có dấu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
# Mỗi thành viên chỉ đổi đúng dòng này khi chạy trong repo cá nhân của mình.
STRATEGY = "fixed"
DATA_DIR = Path("data/thu-vien-uth")
TOP_K = 3
OUTPUT_FILE = Path("ket_qua_benchmark.txt")

STUDENT = "NGUYỄN ĐĂNG THỰC (2A202603014)"

# 5 câu hỏi đánh giá THỐNG NHẤT CỦA NHÓM (xem REPORT_NHOM.md mục 3).
#
# `gold_snippets` dùng để chấm "theo nội dung": chunk được tính là chứa đáp án khi
# có ÍT NHẤT MỘT chuỗi trong danh sách xuất hiện nguyên văn trong chunk.
# Phải là danh sách vì cùng một đáp án được hai trang nguồn viết hai kiểu khác nhau:
# Nội quy ghi "1.000đ/cuốn/ngày", trang Phục vụ ghi "1000 đồng/1 cuốn/1 ngày".
# `gold_docs` cũng là danh sách vì đáp án Q1 và Q4 nằm ở hai tài liệu (xem cột
# "Chunk nào chứa thông tin?" trong bảng câu hỏi của REPORT_NHOM.md).
QUERIES = [
    {
        "id": 1,
        "query": "Trả sách quá hạn thì bị phạt bao nhiêu tiền?",
        "gold_docs": ["phuc-vu-muon-tra-tai-lieu", "noi-quy-thu-vien"],
        "gold_snippets": ["1000 đồng", "1.000đ/cuốn/ngày"],
        "filter": None,
    },
    {
        "id": 2,
        "query": "Sách mượn về nhà được gia hạn mấy lần, mỗi lần bao lâu?",
        "gold_docs": ["phuc-vu-muon-tra-tai-lieu"],
        "gold_snippets": ["01 lần với thời gian 45 ngày"],
        "filter": None,
    },
    {
        "id": 3,
        "query": "Mỗi bạn đọc được mượn tối đa bao nhiêu tài liệu về nhà?",
        "gold_docs": ["quy-dinh-muon-tra-sinh-vien"],
        "gold_snippets": ["05 tài liệu"],
        "filter": {"audience": "student"},
    },
    {
        "id": 4,
        "query": "Khi vào phòng đọc được mang theo những gì?",
        "gold_docs": ["noi-quy-thu-vien", "phuc-vu-phong-doc"],
        "gold_snippets": ["Máy tính cá nhân"],
        "filter": None,
    },
    {
        "id": 5,
        "query": "Muốn kiểm tra tỉ lệ trùng lặp cho khóa luận, đồ án thì dùng dịch vụ nào?",
        "gold_docs": ["dich-vu-quet-trung-lap"],
        "gold_snippets": ["Turnitin"],
        "filter": None,
    },
]

# 5 cặp câu của RIÊNG Nguyễn Đăng Thực (Bài tập 3.3).
# Phần tử 3 là DỰ ĐOÁN, ghi trước khi chạy; phần tử 4 là giả thuyết muốn kiểm chứng.
SIMILARITY_PAIRS = [
    (
        "Sinh viên được mượn tối đa bao nhiêu tài liệu về nhà?",
        "Hạn mức mang tài liệu thư viện ra ngoài của người học là bao nhiêu?",
        "cao",
        "Diễn đạt lại cùng một ý bằng từ vựng khác hẳn",
    ),
    (
        "Thời hạn mượn tài liệu về nhà là bao lâu?",
        "Mức phạt khi trả tài liệu trễ hạn là bao nhiêu?",
        "cao",
        "Cùng chủ đề mượn - trả nhưng hỏi hai thông tin khác nhau",
    ),
    (
        "Cán bộ, giảng viên được mượn 10 tài liệu.",
        "Sinh viên được mượn 05 tài liệu tiếng Việt.",
        "cao",
        "Bẫy audience: điểm càng cao thì embedding càng không tách được đối tượng, buộc phải dùng metadata filter",
    ),
    (
        "Quy định sử dụng máy tính và Internet trong thư viện.",
        "Rules for using library computers and the Internet.",
        "cao",
        "Kiểm tra khả năng đa ngữ (Việt - Anh) của mô hình embedding",
    ),
    (
        "Dịch vụ quét trùng lặp Turnitin cho khóa luận tốt nghiệp.",
        "Lịch thi đấu vòng 5 giải bóng đá ngoại hạng Anh.",
        "thấp",
        "Hai miền chủ đề tách rời, dùng làm mốc dưới",
    ),
]


# ==============================================================================
# NẠP DỮ LIỆU
# ==============================================================================
def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Tách frontmatter YAML đơn giản (key: value) khỏi phần thân tài liệu."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, parts[2].strip()


def get_chunker(strategy: str):
    chunkers = {
        "fixed": lambda: FixedSizeChunker(chunk_size=400, overlap=80),
        "recursive": lambda: RecursiveChunker(chunk_size=400),
        "sentence": lambda: SentenceChunker(max_sentences_per_chunk=3),
    }
    if strategy not in chunkers:
        raise ValueError(f"Chiến lược không hợp lệ: {strategy!r} (chọn: {sorted(chunkers)})")
    return chunkers[strategy]()


def build_store(embedder) -> tuple[EmbeddingStore, int, float]:
    """Chunk toàn bộ corpus rồi nạp vào store; metadata tài liệu trải xuống mọi chunk."""
    store = EmbeddingStore(collection_name="thu_vien_uth", embedding_fn=embedder)
    chunker = get_chunker(STRATEGY)

    chunk_docs: list[Document] = []
    lengths: list[int] = []

    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_markdown(path)
        metadata["doc_id"] = metadata.get("doc_id", path.stem)

        for index, chunk_text in enumerate(chunker.chunk(body)):
            lengths.append(len(chunk_text))
            chunk_docs.append(
                Document(
                    id=f"{metadata['doc_id']}#{index}",
                    content=chunk_text,
                    metadata=dict(metadata),
                )
            )

    store.add_documents(chunk_docs)
    avg_length = sum(lengths) / len(lengths) if lengths else 0.0
    return store, len(chunk_docs), avg_length


# ==============================================================================
# BACKEND EMBEDDING / LLM
# ==============================================================================
def make_embedder():
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    builders = {
        "gemini": lambda: GeminiEmbedder(
            model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
        ),
        "openai": lambda: OpenAIEmbedder(
            model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
        ),
        "local": LocalEmbedder,
    }
    if provider in builders:
        try:
            embedder = builders[provider]()
            return embedder, getattr(embedder, "_backend_name", provider)
        except Exception as exc:  # thiếu key / thiếu package -> không làm hỏng cả lượt chạy
            print(f"[!] Không khởi tạo được backend {provider!r} ({exc}). Quay về MockEmbedder.")
    return _mock_embed, "mock embeddings fallback"


def extractive_llm(prompt: str) -> str:
    """LLM dự phòng khi không có API key: trả lại nguyên văn khối ngữ cảnh hạng 1."""
    body = prompt.split("--- NGỮ CẢNH ---", 1)[-1].split("--- CÂU HỎI ---", 1)[0].strip()
    first_block = body.split("\n\n[2]", 1)[0].strip()
    return f"[trích xuất, không gọi LLM] {' '.join(first_block.split())[:400]}"


def make_llm() -> tuple[Callable[[str], str], str]:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_LLM_MODEL", "gemini-3.6-flash")
    if not api_key:
        return extractive_llm, "extractive fallback (chưa có GEMINI_API_KEY)"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        def gemini_llm(prompt: str, attempts: int = 4) -> str:
            # Model free-tier hay trả 503 khi quá tải; thử lại có giãn cách thay vì
            # để hỏng cả lượt benchmark ở câu thứ ba.
            for attempt in range(1, attempts + 1):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.0),
                    )
                    return (response.text or "").strip()
                except Exception as exc:
                    if attempt == attempts:
                        print(f"[!] LLM lỗi sau {attempts} lần thử ({exc}). Dùng bản trích xuất.")
                        return extractive_llm(prompt)
                    time.sleep(5 * attempt)
            return extractive_llm(prompt)

        gemini_llm("ping")  # thử sớm, tránh hỏng giữa lượt chạy
        return gemini_llm, model_name
    except Exception as exc:
        print(f"[!] Không gọi được LLM Gemini ({exc}). Dùng bản trích xuất.")
        return extractive_llm, "extractive fallback"


# ==============================================================================
# CHẤM ĐIỂM
# ==============================================================================
def has_answer(content: str, snippets: list[str]) -> bool:
    lowered = content.lower()
    return any(snippet.lower() in lowered for snippet in snippets)


def score_results(item: dict, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Chấm 2 mức: theo doc_id (ngây thơ) và theo nội dung (đáp án nằm trong chunk)."""
    snippets = item["gold_snippets"]
    doc_hit = any(r["metadata"].get("doc_id") in item["gold_docs"] for r in results)
    top1_has_answer = bool(results) and has_answer(results[0]["content"], snippets)
    top3_has_answer = any(has_answer(r["content"], snippets) for r in results)

    return {
        "doc_id_score": 2 if doc_hit else 0,
        "content_score": 2 if top1_has_answer else (1 if top3_has_answer else 0),
        "top3_has_answer": top3_has_answer,
    }


def format_results(results: list[dict[str, Any]]) -> list[str]:
    lines = []
    for rank, result in enumerate(results, start=1):
        preview = " ".join(result["content"].split())[:90]
        lines.append(
            f"    [{rank}] {result['metadata'].get('doc_id')} ({result['score']:.3f}): {preview}..."
        )
    return lines


# ==============================================================================
# MAIN
# ==============================================================================
def main() -> None:
    load_dotenv(override=False)

    embedder, embedder_name = make_embedder()
    llm_fn, llm_name = make_llm()

    store, total_chunks, avg_length = build_store(embedder)
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)

    out: list[str] = []

    def emit(line: str = "") -> None:
        print(line)
        out.append(line)

    emit(f"BENCHMARK — {STUDENT}")
    emit(f"Chiến lược: {STRATEGY} (FixedSizeChunker 400/80)")
    emit(f"Embedding: {embedder_name} | LLM: {llm_name} | top_k={TOP_K}")
    emit(f"Chunks: {total_chunks} | Độ dài trung bình: {avg_length:.1f} ký tự")
    emit("=" * 78)

    doc_id_total = 0
    content_total = 0
    top3_hits = 0

    for item in QUERIES:
        results = store.search_with_filter(
            item["query"], top_k=TOP_K, metadata_filter=item["filter"]
        )
        scored = score_results(item, results)
        doc_id_total += scored["doc_id_score"]
        content_total += scored["content_score"]
        top3_hits += int(scored["top3_has_answer"])

        emit(f"Q{item['id']}: {item['query']}")
        emit(f"  Filter: {item['filter']}")
        emit(
            f"  Điểm: theo doc_id={scored['doc_id_score']}/2"
            f" · theo nội dung={scored['content_score']}/2"
        )
        for line in format_results(results):
            emit(line)
        # Dùng lại đúng `results` vừa chấm (agent.answer sẽ search lại và bỏ mất filter),
        # để câu trả lời của agent khớp 1-1 với top-3 in ra ở trên.
        answer = agent.llm_fn(agent.build_prompt(item["query"], results))
        emit(f"  Agent: {' '.join(answer.split())}")
        emit("-" * 78)

    emit(
        f"TỔNG: theo doc_id={doc_id_total}/10 · theo nội dung={content_total}/10"
        f" · top-3 có đáp án: {top3_hits}/5"
    )
    emit()

    # --- A/B: câu cần lọc metadata, chạy có và không có filter -------------------
    ab_item = next(q for q in QUERIES if q["filter"])
    emit(f"A/B METADATA FILTER — Q{ab_item['id']}: {ab_item['query']}")
    variants = (("KHÔNG filter", None), (f"CÓ filter {ab_item['filter']}", ab_item["filter"]))
    for label, metadata_filter in variants:
        results = store.search_with_filter(
            ab_item["query"], top_k=TOP_K, metadata_filter=metadata_filter
        )
        scored = score_results(ab_item, results)
        emit(f"  {label} -> điểm nội dung {scored['content_score']}/2")
        for line in format_results(results):
            emit(line)
        answer = agent.llm_fn(agent.build_prompt(ab_item["query"], results))
        emit(f"    Agent: {' '.join(answer.split())}")
    emit("-" * 78)
    emit()

    # --- 5 cặp câu đo cosine (Bài tập 3.3) --------------------------------------
    emit("ĐỘ TƯƠNG TỰ COSINE — 5 CẶP CÂU (dự đoán ghi trước khi chạy)")
    for index, (sent_a, sent_b, prediction, hypothesis) in enumerate(SIMILARITY_PAIRS, start=1):
        similarity = compute_similarity(embedder(sent_a), embedder(sent_b))
        emit(f"Cặp {index}: sim = {similarity:.3f} | dự đoán: {prediction} | {hypothesis}")
        emit(f"    A: {sent_a}")
        emit(f"    B: {sent_b}")

    OUTPUT_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nĐã ghi kết quả vào {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
