# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đăng Thực
**MSSV:** 2A202603014
**Nhóm:** RAUMAMIENTAY
**Vai trong nhóm:** R1 · Data (chốt chủ đề, crawl và làm sạch corpus, tách file theo `audience`, giữ `sources.csv`)
**Chiến lược chunking cá nhân:** `FixedSizeChunker(chunk_size=400, overlap=80)`
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding chỉ về gần cùng một hướng trong không gian nhiều chiều, nghĩa là hai đoạn văn bản nói về cùng một chủ đề / cùng một ý, dù dùng từ ngữ khác nhau và dài ngắn khác nhau. Điểm tiệm cận 1.0 là "gần như cùng nghĩa", quanh 0 là "không liên quan", âm là "ngược hướng".

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên được mượn tối đa bao nhiêu tài liệu về nhà?
- Câu B: Hạn mức mang tài liệu thư viện ra ngoài của người học là bao nhiêu?
- Tại sao tương đồng: Hai câu gần như không dùng chung từ nào ("sinh viên" ↔ "người học", "mượn về nhà" ↔ "mang ra ngoài", "tối đa bao nhiêu" ↔ "hạn mức") nhưng cùng hỏi đúng một con số trong quy định mượn – trả. Đây chính là trường hợp mà tìm kiếm theo từ khóa sẽ trượt còn embedding thì bắt được.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Dịch vụ quét trùng lặp Turnitin cho khóa luận tốt nghiệp.
- Câu B: Lịch thi đấu vòng 5 giải bóng đá ngoại hạng Anh.
- Tại sao khác: Hai miền chủ đề tách rời hoàn toàn (dịch vụ học thuật ↔ thể thao), không chung khái niệm, không chung ngữ cảnh sử dụng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid chịu ảnh hưởng của **độ lớn** vector, mà độ lớn lại thay đổi theo độ dài văn bản: một chunk 400 ký tự và một câu hỏi 10 từ cùng nói một ý vẫn bị coi là "xa nhau". Cosine chuẩn hóa độ dài và chỉ đo góc, nên so được câu hỏi ngắn với chunk dài. Thêm nữa, các mô hình embedding hiện nay (kể cả `MockEmbedder` trong repo) đã trả về vector chuẩn hóa sẵn, nên cosine rút gọn thành tích vô hướng — đúng cách `EmbeddingStore.search` đang xếp hạng, rẻ hơn hẳn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy giữa hai chunk liên tiếp: `step = chunk_size − overlap = 500 − 50 = 450`.
> Áp công thức: `số chunk = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = 23`.
> Kiểm chứng bằng chính code trong repo (`FixedSizeChunker(chunk_size=500, overlap=50).chunk("a" * 10000)`) → **23 chunks**, khớp công thức. Chunk cuối chỉ dài 100 ký tự (bắt đầu tại vị trí 9900).
> *Đáp án:* **23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `step` giảm còn 400 nên số chunk tăng lên `ceil(9900 / 400) = 25` (kiểm chứng bằng code: **25 chunks**, tăng 2). Muốn overlap lớn hơn vì thông tin nằm ngay chỗ cắt sẽ có **hai cơ hội** lọt vào top-k: trong corpus của nhóm, mức phạt "500đ/ngày/1 cuốn sách" nằm sát ngay dưới tiêu đề "4.1 Trường hợp mượn tài liệu quá hạn", nếu nhát cắt rơi vào giữa thì chunk chứa con số mất luôn ngữ cảnh "quá hạn". Cái giá phải trả là số chunk nhiều hơn (tốn token embedding) và nhiều chunk gần trùng nhau cạnh tranh nhau trong top-3.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách câu bằng regex `(?<=[.!?])\s+` biên dịch sẵn ở cấp lớp. Lookbehind giúp dấu kết câu **ở lại** với câu của nó, còn `\s+` nuốt trọn cả khoảng trắng lẫn xuống dòng nên `". "`, `"! "`, `"? "` và `".\n"` đều tách đúng mà không mất ký tự nào. Sau đó `strip` từng câu, bỏ câu rỗng, rồi gom `max_sentences_per_chunk` câu liền kề bằng một list comprehension chạy theo bước nhảy. Edge case: chuỗi rỗng hoặc chỉ toàn khoảng trắng trả `[]`; `max(1, ...)` trong `__init__` chặn tham số 0/âm gây chia nhóm vô hạn. Điểm yếu tôi biết trước và có nêu khi so sánh nhóm: văn bản quy định tiếng Việt dùng gạch đầu dòng `–` và hiếm dấu chấm, nên một "câu" theo regex có thể ôm cả tiêu đề lẫn nhiều dòng bullet.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` đệ quy theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]` với hai base case: (1) mảnh đã ngắn hơn `chunk_size` thì giữ nguyên, (2) hết separator hoặc gặp separator rỗng `""` thì cắt cứng theo độ dài qua helper `_hard_split`. Nếu separator hiện tại không có trong văn bản thì bỏ qua, xuống cấp thấp hơn ngay. Phần quan trọng là bước **gom (merge)**: sau khi `split`, tôi dồn các mảnh nhỏ liên tiếp vào một buffer cho tới sát `chunk_size` rồi mới `flush`, nhờ vậy tài liệu nhiều dòng ngắn không sinh ra hàng chục chunk vụn; mảnh nào tự nó đã dài hơn `chunk_size` thì flush buffer trước rồi đệ quy xuống separator kế tiếp. Chốt chặn cuối `return chunks or self._hard_split(current_text)` đảm bảo không bao giờ trả danh sách rỗng cho văn bản khác rỗng (trường hợp text toàn separator).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi chốt dùng **in-memory** (list các dict), không bật ChromaDB: kết quả tất định, không cần server, chạy giống nhau trên mọi máy chấm bài — ChromaDB để là extra tùy chọn nên thiếu package cũng không lỗi. `_make_record` chuẩn hóa mỗi `Document`: copy metadata (không sửa dict của caller), `setdefault("doc_id", doc.id)` để mọi chunk đều mang `doc_id` — đây là khóa mà `delete_document` và cách chấm điểm trong `bench.py` dựa vào — rồi embed nội dung đúng **một lần** lúc nạp. `search` embed câu hỏi rồi tính tích vô hướng với toàn bộ vector đã lưu; vì vector đã chuẩn hóa nên tích vô hướng chính là cosine. Tôi sắp xếp theo khóa `(-score, index)`: `index` là số thứ tự lúc nạp, dùng làm tie-break để hai chunk trùng điểm luôn ra cùng một thứ hạng giữa các lần chạy (corpus của nhóm có phần chung bị nhân đôi khi tách file theo `audience`, nên chuyện trùng điểm là có thật).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước (pre-filtering)**: quét `self._store` lấy các record khớp toàn bộ điều kiện rồi mới xếp hạng, nên tài liệu sai đối tượng bị loại *trước khi* tranh chỗ trong top-k — nếu lọc sau thì top-3 đã bị chunk giảng viên chiếm rồi mới lọc, còn lại chẳng bao nhiêu. Helper `_matches` cho phép giá trị là list/tuple/set với nghĩa "một trong các giá trị này", để chạy được đề xuất `{"audience": ["student", "all"]}` mà nhóm rút ra ở mục 3 báo cáo nhóm (filter cứng `student` làm mất đáp án nằm ở tài liệu `audience=all`). Không truyền filter thì đi thẳng vào tìm kiếm trên toàn store. `delete_document` lọc bỏ mọi record có `metadata["doc_id"]` **hoặc** `id` trùng `doc_id` (id của chunk có dạng `doc_id#i` nên vẫn xóa sạch theo metadata), và trả `True/False` bằng cách so số phần tử trước – sau.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` chặn hai trường hợp rỗng (store chưa có tài liệu / không tìm được chunk nào) rồi mới gọi LLM, tránh đốt token vô ích. Tôi tách riêng `build_prompt(question, results)` thành method công khai vì `bench.py` cần **dựng prompt từ đúng bộ kết quả đã lọc metadata** — nếu để `answer` tự search lại thì câu Q3 sẽ trả lời trên top-3 *không* filter, không khớp với bảng điểm in ra. Prompt đánh số khối ngữ cảnh `[1] (nguồn: <source_url>)` để câu trả lời truy vết được về trang gốc, yêu cầu chỉ dựa vào ngữ cảnh và nói rõ khi không đủ thông tin (chống bịa quy định), và có thêm một dòng đặc thù cho corpus này: *"nếu một con số chỉ áp dụng cho một đối tượng (sinh viên / cán bộ, giảng viên), hãy nêu rõ đối tượng đó kèm con số"* — vì lỗi hay gặp nhất của nhóm là LLM gán nhầm con số cho sai đối tượng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\Vin_AI_THUC_CHIEN\K4-L3A-Data-Foundations-2A202603014\K4-DAY07-NguyenDangThuc-2A202603014
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Dự đoán ghi trong `SIMILARITY_PAIRS` của `bench.py` **trước khi** chạy; điểm thực tế đo bằng `compute_similarity()` với `gemini-embedding-001` (log: `ket_qua_benchmark.txt`).

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được mượn tối đa bao nhiêu tài liệu về nhà? | Hạn mức mang tài liệu thư viện ra ngoài của người học là bao nhiêu? | cao | 0.918 | Đúng |
| 2 | Thời hạn mượn tài liệu về nhà là bao lâu? | Mức phạt khi trả tài liệu trễ hạn là bao nhiêu? | cao | 0.743 | Đúng |
| 3 | Cán bộ, giảng viên được mượn 10 tài liệu. | Sinh viên được mượn 05 tài liệu tiếng Việt. | cao | 0.834 | Đúng |
| 4 | Quy định sử dụng máy tính và Internet trong thư viện. | Rules for using library computers and the Internet. | cao | 0.854 | Đúng |
| 5 | Dịch vụ quét trùng lặp Turnitin cho khóa luận tốt nghiệp. | Lịch thi đấu vòng 5 giải bóng đá ngoại hạng Anh. | thấp | 0.501 | Đúng |

5/5 dự đoán đúng về hướng, nhưng thứ hạng giữa chúng mới là phần đáng nói.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 3 đạt 0.834, cao hơn cặp 2 (0.743)** — tức là hai câu nói về **hai đối tượng khác nhau với hai con số khác nhau** lại "giống nhau" hơn hai câu hỏi cùng chủ đề mượn – trả. Lý do: embedding mã hóa *chủ đề và khuôn câu*, mà cặp 3 gần như cùng một khuôn ("<đối tượng> được mượn <số> tài liệu"), chỉ khác đúng chỗ quan trọng nhất. Đây chính là bằng chứng định lượng cho việc **không thể trông chờ embedding tự tách `audience`**, phải dùng `metadata_filter` — đúng vai R1 · Data của tôi khi quyết định tách trang quy định gốc thành hai file `student` / `faculty` thay vì để chung một file. Bất ngờ thứ hai theo hướng tích cực: cặp 4 (Việt – Anh) đạt 0.854, xác nhận `gemini-embedding-001` là mô hình đa ngữ thật, nên corpus tiếng Việt vẫn trả lời được câu hỏi tiếng Anh. Cũng cần lưu ý mốc dưới: hai câu hoàn toàn khác miền vẫn được 0.501, nghĩa là với mô hình này **không có ngưỡng tuyệt đối** kiểu "dưới 0.5 là không liên quan" — chỉ so sánh tương đối trong cùng một lần xếp hạng mới có ý nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong gói `src`. **5 câu hỏi này trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md` mục 3).

Cấu hình lần chạy này: `FixedSizeChunker(400, 80)` → **30 chunks, độ dài trung bình 365.8 ký tự**; embedding `gemini-embedding-001` (3072 chiều); LLM `gemini-3.6-flash` (temperature 0); top-3. Lệnh: `python bench.py`, log đầy đủ: `ket_qua_benchmark.txt`.

> **Lưu ý về cấu hình:** bảng tổng hợp trong `REPORT_NHOM.md` được chạy với `text-embedding-3-small` + `gpt-4.1-nano`. Tôi không còn quota OpenAI nên chạy lại bằng Gemini (free tier). Số chunk và độ dài trung bình khớp y nguyên (30 / 366) vì chunking không phụ thuộc backend; điểm số và thứ hạng thì khác, chi tiết ở phần nhận xét bên dưới.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Trả sách quá hạn thì bị phạt bao nhiêu tiền? | `noi-quy-thu-vien`: "Quá hạn phải nộp phạt 1.000đ/cuốn/ngày. – Phạt 10.000đ/trang nếu viết, vẽ vào tài liệu…" | 0.812 | Có (hạng 1) | Nêu **1.000đ/cuốn/ngày** [1] và nói thêm quy định khác ghi **500đ/ngày/cuốn** [2][3], kèm lưu ý ngữ cảnh không nêu rõ đối tượng áp dụng — đúng đáp án chuẩn, đồng thời tự phát hiện nguồn mâu thuẫn (2đ) |
| 2 | Sách mượn về nhà được gia hạn mấy lần, mỗi lần bao lâu? | `phuc-vu-muon-tra-tai-lieu`: "…Thời gian mượn về nhà: 45 ngày. Số lần được gia hạn: 01 lần…" | 0.833 | Có (hạng 1) | "gia hạn **01 lần** với thời gian **45 ngày** [1]" — đúng (2đ) |
| 3 | Mỗi bạn đọc được mượn tối đa bao nhiêu tài liệu về nhà? *(filter `audience: student`)* | `quy-dinh-muon-tra-sinh-vien` mục 2.1: "## 2. Số lượng tài liệu được mượn ### 2.1 Tài liệu mượn về nhà – Đối với bạn đọc…" | 0.847 | Có (hạng 1; cả top-3 đều là tài liệu sinh viên) | "Sinh viên: Tiếng Việt **05**, Tiếng Anh tham khảo **03** [1]"; nói rõ nhóm học viên cao học/NCS chỉ quy định đặt cọc, **không** gán nhầm con số — đúng (2đ) |
| 4 | Khi vào phòng đọc được mang theo những gì? | `phuc-vu-phong-doc`: "# Phục vụ phòng đọc… Chỉ được mang vào phòng đọc: Máy tính cá nhân, Sách, tập vở…" | 0.809 | Có (hạng 1) | "Máy tính cá nhân [1][2]; Sách, tập vở và dụng cụ học tập [1][2]" — đúng, đủ 4 mục (2đ) |
| 5 | Muốn kiểm tra tỉ lệ trùng lặp cho khóa luận, đồ án thì dùng dịch vụ nào? | `dich-vu-quet-trung-lap`: "# Dịch vụ quét trùng lặp ## Dịch vụ Xác định tỉ lệ trùng lắp nội dung…" | 0.852 | Có (hạng 1) | "**Dịch vụ quét trùng lặp**, dùng phần mềm chống đạo văn **Turnitin** [1]" — đúng (2đ) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** — và cả 5 đều ở **hạng 1**.
Dòng `TỔNG` trong `ket_qua_benchmark.txt`: `theo doc_id=10/10 · theo nội dung=10/10 · top-3 có đáp án: 5/5`.

**Một chi tiết về cách chấm mà tôi phải sửa trong `bench.py`:** lần chạy đầu Q1 bị chấm **0/2** dù top-1 chính là chunk chứa đáp án. Nguyên nhân nằm ở tầng dữ liệu chứ không phải retrieval: cùng một mức phạt nhưng Nội quy viết `1.000đ/cuốn/ngày` còn trang Phục vụ viết `1000 đồng/1 cuốn/1 ngày`, mà `gold_snippet` chỉ có đúng một chuỗi. Tôi đổi `gold_snippet`/`gold_doc` thành danh sách `gold_snippets`/`gold_docs` (chấp nhận mọi cách viết của cùng một đáp án, và cả hai tài liệu cùng chứa đáp án ở Q1/Q4). Bài học: **thước đo tự động cũng cần được kiểm tra**, nếu không sẽ báo lỗi retrieval trong khi retrieval hoàn toàn đúng.

**A/B Test câu 3 — lọc metadata `audience`:**
- **CÓ filter `{"audience": "student"}`:** cả top-3 đều là `quy-dinh-muon-tra-sinh-vien` (0.847 / 0.818 / 0.814); agent trả lời gọn trong phạm vi sinh viên: 05 tiếng Việt + 03 tiếng Anh.
- **KHÔNG filter:** top-1 vẫn là chunk sinh viên (0.847) nhưng hạng 2–3 là trang chung `phuc-vu-muon-tra-tai-lieu` (0.842) và `quy-dinh-muon-tra-can-bo-giang-vien` (0.832); agent trả lời **cả ba đối tượng**: sinh viên 8 cuốn (5 TV + 3 ngoại văn), cán bộ – giảng viên 10 tài liệu, học viên cao học phải đặt cọc.
- **Nhận xét:** ở lần chạy này, không filter **vẫn không sai** — khác với bản `gpt-4.1-nano` trong báo cáo nhóm, nơi Fixed gán nhầm "03 tài liệu cho học viên cao học" còn Sentence trả lời hẳn "10 tài liệu" (sai đối tượng). Nhưng khoảng cách điểm giữa chunk sinh viên và chunk giảng viên chỉ **0.015** (0.847 vs 0.832), tức là retrieval gần như không phân biệt được hai đối tượng — đúng như cặp câu số 3 ở mục 4 đo được (0.834). Chỉ cần đổi cách diễn đạt câu hỏi là thứ hạng có thể lật. Vậy nên filter vẫn là **bắt buộc** nếu muốn bảo đảm đúng đối tượng: nó biến một kết quả *may mắn đúng* thành một kết quả *chắc chắn đúng*, và làm câu trả lời ngắn lại, không bắt người hỏi tự lọc thông tin của đối tượng khác.

**So với bảng của tôi trong `REPORT_NHOM.md` (cấu hình OpenAI):** ở đó Fixed được 9/10 vì Q3 chỉ đạt 1/2 (nano gán nhầm "03 tài liệu" cho học viên cao học). Với `gemini-3.6-flash`, đúng chunk đó lại cho câu trả lời chuẩn, nên điểm lên 10/10. Retrieval hai lần chạy đều đưa chunk đáp án lên hạng 1 ở cả 5 câu — **phần thay đổi nằm ở LLM, không phải ở chunker**. Điều này củng cố insight số 4 của nhóm: khi retrieval đã tốt, nút thắt chuyển sang model sinh câu trả lời.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Từ `HeadingChunker` của bạn Tài: sau khi cắt một mục dài thành nhiều mảnh, **gắn lại đường dẫn tiêu đề** ("Nội quy Thư viện > Điều 7. Quy định xử phạt") vào đầu *từng mảnh con*. Chiến lược Fixed của tôi thắng về điểm số nhưng thua hẳn ở khoản này: chunk của tôi cắt giữa từ (có chunk bắt đầu bằng "ả hết tài liệu của học kỳ trước…"), đọc log rất khó và khi trích dẫn thì không biết con số đang nằm ở Điều nào. Nếu làm lại, tôi sẽ giữ cửa sổ trượt nhưng thêm một dòng tiêu đề mục vào đầu mỗi chunk — gần như không tốn gì mà chunk tự truy vết được. Bài học thứ hai, từ chính vai Data của tôi: việc tách file theo `audience` đã **nhân đôi** phần quy định chung, khiến hai chunk "500đ" giống hệt nhau cùng lọt top-3 ở Q1; lần sau chỉ nên tách phần khác biệt, phần chung để `audience: all`.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
