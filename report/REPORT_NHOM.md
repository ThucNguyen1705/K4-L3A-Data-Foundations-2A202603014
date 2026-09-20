# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** RAUMAMIENTAY
**Thành viên:** Nguyễn Văn Tài (2A202603004), Nguyễn Đăng Thực (2A202603014), Lâm Hoàng Phúc (2A202602582), Nguyễn Đức Minh (2A202602891)
**Ngày:** 2026-09-19

| Thành viên | MSSV | Vai | Phụ trách | Chiến lược chunking |
|-----------|------|-----|-----------|---------------------|
| Nguyễn Văn Tài | 2A202603004 | R3 · Strategy | Bảo đảm 4 chiến lược không trùng; viết chunker theo heading (bắt buộc với L3A); chạy baseline; viết `bench.py` (chấm 2 mức, A/B filter) | `HeadingChunker` (custom) |
| Nguyễn Đăng Thực | 2A202603014 | R1 · Data | Chốt chủ đề thư viện UTH; crawl và làm sạch 8 tài liệu; tách file theo `audience`; giữ `sources.csv`; chạy script kiểm CP2 (8/8 OK) | `FixedSizeChunker` |
| Lâm Hoàng Phúc | 2A202602582 | R2 · Benchmark | Viết 5 câu hỏi + gold answer; kiểm mỗi gold answer trích nguyên văn được từ corpus; thiết kế Q3 cần filter `audience` và chạy A/B | `RecursiveChunker` |
| Nguyễn Đức Minh | 2A202602891 | Report & Demo Lead | Gom kết quả 4 chiến lược; tổng hợp báo cáo nhóm; dẫn phần so sánh và failure case khi demo | `SentenceChunker` |

Repo cá nhân và kết quả chi tiết từng câu của mỗi thành viên: xem **Phụ lục** cuối báo cáo.

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và quy định Thư viện — Trung tâm Thông tin – Thư viện, Trường ĐH Giao thông vận tải TP.HCM (UTH), `lic.ut.edu.vn`.

**Tại sao nhóm chọn chủ đề này?**
> Quy định thư viện đúng mảng K4-L3A yêu cầu: có nhiều con số kiểm chứng được (hạn mức, thời hạn, mức phạt) và có sự khác biệt thật giữa các đối tượng. Trang "Quy định mượn – trả tài liệu" ghi sinh viên được mượn 5 tiếng Việt + 3 tiếng Anh, còn cán bộ/giảng viên được 10 tài liệu, nên `metadata_filter={"audience": "student"}` có việc thật để làm. Tất cả trang lấy từ **một** website chính thức, để corpus nhất quán và có thể đối chiếu chéo giữa các trang.

### Danh sách tài liệu (Data Inventory)

Crawl bằng `scripts/fetch_public_pages.py` ngày 2026-09-19 (robots.txt của `lic.ut.edu.vn`: `User-agent: * / Disallow:`, tức cho phép tất cả; giãn cách ≥ 1 giây). Output thô đã được **làm sạch tay**: bỏ menu, "Skip to content", tiêu đề bị lặp, danh sách "Bài viết gần đây" và footer; giữ nguyên văn điều khoản, con số và mốc thời gian. Số ký tự bên dưới là phần thân, không tính frontmatter.

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định mượn – trả tài liệu (sinh viên, học viên) | https://lic.ut.edu.vn/quy-dinh-muon-tra-tai-lieu/ | 2026-09-19 / not-stated | 1864 | audience=student, category=borrowing, department=library, language=vi |
| 2 | Quy định mượn – trả tài liệu (cán bộ, giảng viên) | https://lic.ut.edu.vn/quy-dinh-muon-tra-tai-lieu/ | 2026-09-19 / not-stated | 1325 | audience=faculty, category=borrowing, department=library, language=vi |
| 3 | Nội quy Thư viện | https://lic.ut.edu.vn/noi-quy-thu-vien/ | 2026-09-19 / 2022-11-01 | 3044 | audience=all, category=library-rules, department=library, language=vi |
| 4 | Phục vụ mượn – trả tài liệu | https://lic.ut.edu.vn/dich-vu-thu-vien/phuc-vu-muon-tra-tai-lieu/ | 2026-09-19 / not-stated | 992 | audience=all, category=borrowing, department=library, language=vi |
| 5 | Phục vụ phòng đọc | https://lic.ut.edu.vn/dich-vu-thu-vien/phuc-vu-phong-doc/ | 2026-09-19 / not-stated | 623 | audience=all, category=reading-room, department=library, language=vi |
| 6 | Sử dụng máy tính, Internet | https://lic.ut.edu.vn/dich-vu-thu-vien/su-dung-may-tinh-internet/ | 2026-09-19 / not-stated | 487 | audience=all, category=computer-room, department=library, language=vi |
| 7 | Dịch vụ quét trùng lặp (Turnitin) | https://lic.ut.edu.vn/dich-vu-cong-nghe-thong-tin/dich-vu-quet-trung-lap/ | 2026-09-19 / not-stated | 521 | audience=all, category=plagiarism-check, department=library, language=vi |
| 8 | Hỗ trợ nhanh — Liên hệ | https://lic.ut.edu.vn/dich-vu-thu-vien/ho-tro-nhanh/ | 2026-09-19 / not-stated | 358 | audience=all, category=contact, department=library, language=vi |

- Tài liệu 1 và 2 được **tách từ cùng một trang** theo `audience` (field `split_from: quy-dinh-muon-tra-tai-lieu`). Phần chung (quy định chung, thời gian mượn, xử lý vi phạm) được chép vào cả hai file. Riêng quy định mặc đồng phục chỉ áp dụng cho sinh viên nên chỉ nằm ở file sinh viên.
- `document_version` chỉ ghi khi trang nêu rõ: Nội quy ký ngày 01/11/2022. Các trang khác không nêu nên ghi `not-stated`, không bịa số hiệu.
- Đã loại khỏi corpus: `noi-quy-thu-vien-2` (trùng 100% với tài liệu 3), `hoc-tap-ca-nhan-hoc-nhom` và `khai-thac-tai-nguyen-so` (trang chỉ ghi "Chờ nội dung"), bài "mượn liên thư viện" (nội dung nằm trong file PDF đính kèm), `photo-scan`/`tra-cuu` (chỉ có link hướng dẫn). Ở trang Liên hệ, email bị Cloudflare ẩn (`[email protected]`) nên bỏ dòng đó.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. Các trang đều công khai, không cần đăng nhập, robots.txt cho phép. Chỉ giữ thông tin liên hệ của đơn vị (số điện thoại văn phòng, địa chỉ cơ sở), không có thông tin cá nhân.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata. Đã kiểm bằng script CP2: 8/8 file OK, `sources.csv` khớp 1-1, audience = {all: 6, faculty: 1, student: 1}.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `quy-dinh-muon-tra-sinh-vien` | Trùng tên file, được trải vào mọi chunk nên `delete_document` và việc chấm top-3 truy về đúng file gốc |
| `audience` | enum student/faculty/staff/all | `student` | Lọc theo đối tượng: câu hỏi hạn mức không nói ai hỏi, filter `student` loại được bản dành cho giảng viên |
| `category` | string | `borrowing`, `reading-room` | Thu hẹp theo mảng dịch vụ, ví dụ chỉ tìm trong quy định mượn–trả |
| `department` | string | `library` | Khi mở rộng corpus sang phòng đào tạo, KTX…, lọc theo đơn vị ban hành |
| `source_url` | URL | `https://lic.ut.edu.vn/noi-quy-thu-vien/` | Agent trích nguồn trong prompt `[n] (nguồn: …)`, giúp truy vết câu trả lời |
| `retrieved_at` / `document_version` | date / string | `2026-09-19` / `2022-11-01` | Biết độ mới; khi hai trang mâu thuẫn (xem mục 4) thì ưu tiên văn bản có ngày hiệu lực |
| `split_from` | string | `quy-dinh-muon-tra-tai-lieu` | Ghi lại 2 file được tách từ cùng một trang nguồn |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.
> Mọi số liệu trong mục này lấy từ `python bench.py --strategy all` (log: `ket_qua_benchmark_all.txt`). Cùng corpus, cùng 5 câu hỏi, cùng embedding `text-embedding-3-small`, cùng LLM `gpt-4.1-nano` (temperature 0), top-3; chỉ khác đúng một dòng: dòng chọn chunker.
> Mỗi thành viên chạy `bench.py` trong repo cá nhân và chỉ đổi dòng `STRATEGY` (`"heading"` / `"fixed"` / `"recursive"` / `"sentence"`). Log gộp của cả 4 chiến lược: `ket_qua_benchmark_all.txt`.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=200)` trên 3 tài liệu, đã bỏ frontmatter:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| noi-quy-thu-vien (3044 ký tự) | FixedSizeChunker (`fixed_size`) | 16 | 190.2 | Không: cắt giữa từ/câu, "Điều n" tách khỏi nội dung |
| | SentenceChunker (`by_sentences`) | 15 | 201.4 | Một phần: bullet không có dấu chấm bị dính sang câu sau, heading lẫn vào giữa chunk |
| | RecursiveChunker (`recursive`) | 26 | 115.6 | Khá: giữ trọn dòng/đoạn, nhưng chunk nhỏ và heading "## Điều 7" có thể tách khỏi danh sách bên dưới |
| quy-dinh-muon-tra-sinh-vien (1864) | `fixed_size` | 10 | 186.4 | Không, ví dụ chunk bắt đầu bằng "ệu (làm rách, ướt…" |
| | `by_sentences` | 7 | 264.0 | Một phần |
| | `recursive` | 14 | 131.5 | Khá, nhưng "4.1 … 500đ" mất tiêu đề mục "4. Xử lý vi phạm" |
| phuc-vu-muon-tra-tai-lieu (992) | `fixed_size` | 5 | 198.4 | Không |
| | `by_sentences` | 4 | 244.8 | Một phần |
| | `recursive` | 7 | 140.0 | Khá |

Nhận xét: `recursive` sinh nhiều chunk nhất và ngắn nhất (tài liệu nhiều dòng ngắn, bullet). `by_sentences` ít chunk nhất vì văn bản quy định ít dấu chấm câu: một "câu" theo regex có thể gồm cả heading lẫn nhiều dòng bullet.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Văn Tài (2A202603004)** (vai R3 · Strategy; nhận chiến lược chunk theo heading, bắt buộc với L3A)
- **Loại chiến lược:** custom `HeadingChunker(max_chars=600)`
- **Mô tả & lý do chọn cho chủ đề này:** Nội quy và quy định được người soạn chia sẵn theo "Điều"/mục, mỗi mục là một đơn vị ngữ nghĩa trọn vẹn. Chunker tách trước mỗi dòng heading Markdown, mỗi section thành một chunk, và gắn **đường dẫn tiêu đề** ("Nội quy Thư viện > Điều 7. Quy định xử phạt") vào đầu chunk. Section dài hơn 600 ký tự thì hạ xuống `RecursiveChunker` và **gắn lại đường dẫn tiêu đề vào từng mảnh con**, để mảnh thứ hai trở đi không mất ngữ cảnh.
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
    HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, max_chars: int = 600) -> None:
        self.max_chars = max_chars

    def chunk(self, text: str) -> list[str]:
        sections, stack, body = [], [], []

        def flush():
            content = "\n".join(body).strip()
            if content:
                sections.append((" > ".join(t for _, t in stack), content))
            body.clear()

        for line in text.splitlines():
            m = self.HEADING.match(line)
            if m:
                flush()
                level = len(m.group(1))
                while stack and stack[-1][0] >= level:   # heading cùng/cao cấp hơn -> đóng mục cũ
                    stack.pop()
                stack.append((level, m.group(2)))
            else:
                body.append(line)
        flush()

        chunks = []
        for path, content in sections:
            candidate = f"{path}\n{content}" if path else content
            if len(candidate) <= self.max_chars:
                chunks.append(candidate)
                continue
            sub_size = max(100, self.max_chars - len(path) - 1)
            for piece in RecursiveChunker(chunk_size=sub_size).chunk(content):
                chunks.append(f"{path}\n{piece}" if path else piece)   # gắn lại tiêu đề
        return chunks
```

**Thành viên 2 — Nguyễn Đăng Thực (2A202603014)** (vai R1 · Data)
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=400, overlap=80)`
- **Mô tả & lý do chọn:** Baseline cửa sổ trượt: không phụ thuộc cấu trúc văn bản, overlap 80 ký tự (20%) để thông tin nằm ở ranh giới có hai cơ hội lọt top-k. Dùng làm mốc để đo xem chiến lược "hiểu cấu trúc" có lợi đến đâu.
- **Code snippet (nếu custom):** không (built-in).

**Thành viên 3 — Lâm Hoàng Phúc (2A202602582)** (vai R2 · Benchmark)
- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)`
- **Mô tả & lý do chọn:** Cắt theo ranh giới tự nhiên `\n\n → \n → ". " → " "` và gom mảnh nhỏ tới sát 400 ký tự. Văn bản quy định nhiều bullet/dòng ngắn nên cách này giữ trọn từng dòng quy định.
- **Code snippet (nếu custom):** không (built-in).

**Thành viên 4 — Nguyễn Đức Minh (2A202602891)** (vai Report & Demo Lead)
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`
- **Mô tả & lý do chọn:** Gom 3 câu thành một chunk, không bao giờ cắt giữa câu. Mục đích là kiểm tra giả thuyết "chunk nhỏ, một ý" có giúp truy xuất trúng các câu chứa con số (hạn mức, mức phạt) hơn chunk dài không. Biết trước điểm yếu: văn bản quy định ít dấu chấm câu nên bullet và heading có thể bị dính vào nhau.
- **Code snippet (nếu custom):** không (built-in).

### So Sánh Giữa Các Thành Viên

"Điểm truy xuất" chấm **theo nội dung**: 2 nếu chunk chứa đáp án ở top-1 và agent đúng, 1 nếu chunk chứa đáp án ở top-2/3 hoặc agent sai/thiếu, 0 nếu không có. Trong ngoặc là điểm chấm ngây thơ theo doc_id. Cột cuối là kết quả đối chứng khi thay embedding bằng MiniLM chạy local (`ket_qua_benchmark_local.txt`, agent trích xuất, không gọi API).

| Thành viên | Chiến lược (Strategy) | Chunks / avg | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu | Đối chứng MiniLM |
|-----------|----------|------|----------------------|-----------|----------|------|
| Nguyễn Văn Tài | HeadingChunker | 32 / 314 | **8** (doc_id 10) | Q1–Q3 top-1 và agent đúng. Q3 có filter: **chiến lược duy nhất** mà nano trả lời đúng, vì mục 2.1 được tách riêng | Q4: mảnh đuôi 93 ký tự (chủ yếu là tiêu đề "Phục vụ phòng đọc") chiếm top-1. Q5: agent bỏ sót "Turnitin". Q3 không filter: agent từ chối trả lời | 7 (doc_id 9) |
| Nguyễn Đăng Thực | FixedSize 400/80 | 30 / 366 | **9** (doc_id 10) | Cả 5 câu có chunk đáp án ở top-1 | Q3 (filter): nano gán nhầm "03 tài liệu" cho học viên cao học. Chunk cắt giữa từ ("ệu (làm rách…"), khó đọc | 6 (doc_id 8) |
| Lâm Hoàng Phúc | Recursive 400 | 35 / 262 | **9** (doc_id 10) | Cả 5 câu top-1. Q3 không filter vẫn đúng vì top-1 là trang Phục vụ "8 cuốn (5 TV + 3 ngoại văn)" | Q3 (filter): nano lẫn sang "đọc tại chỗ: 03 tài liệu" nên trả lời "3 tài liệu". Phần chung nhân đôi: hai chunk "500đ" giống hệt (0.554) chiếm hạng 2–3 ở Q2 | 6 (doc_id 7) |
| Nguyễn Đức Minh | Sentence ×3 | 41 / 223 | 8 (doc_id 9) | Q1, Q4, Q5 top-1, chunk ngắn gọn | Q2, Q3 đáp án ở hạng 2. Q3 filter: agent chỉ nêu "5 tài liệu". Q3 không filter: trả lời "10 tài liệu", **sai đối tượng** | 8 (doc_id 9) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với embedding chính thức `text-embedding-3-small`, Fixed và Recursive (9/10) nhỉnh hơn Heading và Sentence (8/10), và cả 4 đều tìm được chunk đáp án trong top-3 ở 5/5 câu. Nhưng chênh lệch chỉ **1 điểm** và đến từ những chỗ rất khác nhau. Fixed/Recursive mất điểm vì LLM nhỏ đọc nhầm danh sách ở Q3. Heading mất điểm vì một mảnh đuôi quá ngắn (Q4) và agent bỏ sót chi tiết (Q5). Khi đổi sang MiniLM thì thứ hạng **đảo ngược** (Sentence 8, Heading 7, Fixed/Recursive 6; bản MiniLM dùng agent trích xuất nên chỉ so được tương đối). Nên với 5 câu hỏi, nhóm không kết luận được một chiến lược thắng tuyệt đối. Nhóm chọn **Heading** làm hướng phát triển: đây là chiến lược duy nhất giúp LLM nhỏ trả lời đúng câu khó nhất (Q3), và nó cho trích dẫn truy vết được tới "Điều/mục". Điểm yếu Q4 sửa được dễ bằng cách gộp mảnh đuôi quá ngắn vào mảnh trước.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy (khai báo trong `QUERIES` của `bench.py`, kèm chuỗi nguyên văn để kiểm ngữ cảnh và regex để kiểm câu trả lời).

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Trả sách quá hạn thì bị phạt bao nhiêu tiền? *(tra số liệu)* | 1.000đ/cuốn/ngày | `noi-quy-thu-vien` Điều 7 ("Quá hạn phải nộp phạt 1.000đ/cuốn/ngày"); `phuc-vu-muon-tra-tai-lieu` mục Quá hạn ("1000 đồng/1 cuốn/1 ngày"). ⚠ `quy-dinh-muon-tra-*` mục 4.1 ghi 500đ: nguồn mâu thuẫn, xem mục 4 |
| 2 | Sách mượn về nhà được gia hạn mấy lần, mỗi lần bao lâu? *(điều kiện/quy trình)* | 01 lần, thời gian 45 ngày | `phuc-vu-muon-tra-tai-lieu` mục Mượn về nhà ("Số lần được gia hạn: 01 lần với thời gian 45 ngày") |
| 3 | Mỗi bạn đọc được mượn tối đa bao nhiêu tài liệu về nhà? *(cần `metadata_filter={"audience": "student"}`)* | Sinh viên: 05 tài liệu tiếng Việt + 03 tài liệu tiếng Anh (tham khảo) | `quy-dinh-muon-tra-sinh-vien` mục 2.1. Bẫy: `quy-dinh-muon-tra-can-bo-giang-vien` mục 2.1 ghi "Cán bộ, Giảng viên: 10 tài liệu" |
| 4 | Khi vào phòng đọc được mang theo những gì? *(liệt kê)* | Máy tính cá nhân, sách, tập vở và dụng cụ học tập | `noi-quy-thu-vien` Điều 4; `phuc-vu-phong-doc` |
| 5 | Muốn kiểm tra tỉ lệ trùng lặp cho khóa luận, đồ án thì dùng dịch vụ nào? *(dịch vụ/quy trình)* | Dịch vụ quét trùng lặp bằng phần mềm Turnitin; SV, GV-CB dùng qua Hệ thống đào tạo trực tuyến, người dùng khác đến văn phòng LIC | `dich-vu-quet-trung-lap` |

Câu 3 cố ý **không nói người hỏi là ai**, trong khi corpus có hai tài liệu cùng chủ đề, cùng từ vựng nhưng khác đối tượng và khác đáp án.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).
> Cấu hình: `text-embedding-3-small` + `gpt-4.1-nano` (temperature 0), top-3, log `ket_qua_benchmark_all.txt`.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Phạt quá hạn | Cả 4 (2/2) | Có, **hạng 1** ở cả 4 | Chunk "500đ" (nguồn mâu thuẫn) vẫn lọt top-3 ở cả 4, nhưng agent chọn đúng 1.000đ ở top-1. Với MiniLM thì ngược lại: "500đ" chiếm top-1 |
| 2 | Gia hạn | Fixed / Recursive / Heading (2/2) | Có (hạng 1; Sentence hạng 2) | Top-1 của Sentence là Nội quy Điều 3 "thời gian là 45 ngày" (thời hạn mượn, không phải gia hạn) |
| 3 | Hạn mức mượn (filter `student`) | **Heading** (2/2) | Có (hạng 1; Sentence hạng 2) | Retrieval đúng ở cả 4 nhưng nano đọc nhầm danh sách ở 3/4: xem failure case mục 4 |
| 4 | Vật dụng vào phòng đọc | Fixed / Sentence / Recursive (2/2) | Có (hạng 1; Heading hạng 3) | Heading: mảnh đuôi 93 ký tự thắng mảnh có đáp án |
| 5 | Kiểm tra trùng lặp | Fixed / Sentence / Recursive (2/2) | Có, hạng 1 ở cả 4 | Heading: agent nói đúng tên dịch vụ nhưng bỏ sót Turnitin (thiếu chi tiết, 1/2) |

Điểm nhóm theo chiến lược tốt nhất (Fixed của Thực hoặc Recursive của Phúc): **9/10**. Chiến lược heading bắt buộc của L3A (Tài): 8/10. Sentence (Minh): 8/10.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, ở câu 3.** Không filter thì top-1 là tài liệu **giảng viên** ở Fixed, Sentence và Heading (Recursive top-1 là trang chung "8 cuốn"). Hậu quả: Sentence trả lời "10 tài liệu", **sai đối tượng**; Heading thấy ngữ cảnh lẫn hai đối tượng nên từ chối trả lời. Có `audience=student` thì chunk mục 2.1 lên **top-1** ở 3/4 chiến lược (Sentence hạng 2). Nhưng filter **cứng** có giá: ở câu 1, không filter thì top-1 là 1.000đ, còn filter `student` thì top-3 **không còn** chunk 1.000đ nào, chỉ còn "500đ" (đã kiểm với Heading và Recursive). Lý do là đáp án 1.000đ nằm ở tài liệu `audience=all`. Nhóm đề xuất filter `{"audience": ["student", "all"]}` (store hỗ trợ giá trị list). Thử ở câu 3 với Heading và Recursive, chunk chứa đáp án chiếm **hạng 1 và 2**.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Phân công demo (6–8 phút, mỗi thành viên đều trình bày chiến lược của mình):**

| Phần | Thời lượng | Người trình bày |
|------|-----------|-----------------|
| Chủ đề & bộ tài liệu (crawl, làm sạch, tách file theo audience) | 1' | Nguyễn Đăng Thực (R1 · Data) |
| Chiến lược Heading | 30" | Nguyễn Văn Tài |
| Chiến lược FixedSize | 30" | Nguyễn Đăng Thực |
| Chiến lược Recursive | 30" | Lâm Hoàng Phúc |
| Chiến lược Sentence | 30" | Nguyễn Đức Minh |
| So sánh, chiến lược nào thắng, failure case | 3' | Nguyễn Đức Minh (Report & Demo Lead) |
| Demo live `python bench.py` (Q3 có/không filter) | 2' | Lâm Hoàng Phúc (R2 · Benchmark) |

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Đổi embedding tác động mạnh hơn đổi chunker.** Số lượt có chunk đáp án ở top-1 (4 chiến lược × 5 câu): `text-embedding-3-small` **17/20**, MiniLM 11/20, mock 2/20. Chỉ số này đo ở tầng retrieval nên không phụ thuộc LLM. Câu Q1 từ hỏng (MiniLM để "500đ" thắng) thành đúng ở cả 4 chiến lược. Thứ hạng giữa các chunker cũng đảo khi đổi embedding.
> 2. **Chấm theo doc_id thổi phồng kết quả.** OpenAI: Heading 10 → 8, Fixed/Recursive 10 → 9. MiniLM: Fixed 8 → 6, Heading 9 → 7. Lấy đúng tài liệu chưa có nghĩa là trả lời được.
> 3. **Embedding không phân biệt được đối tượng, nên metadata filter là bắt buộc.** Cặp "Giảng viên được mượn 10 tài liệu" và "Sinh viên được mượn 5 tài liệu" có cosine 0.800. Câu phủ định "Tôi (không) muốn mượn sách" đạt 0.895, cao hơn cả cặp đồng nghĩa thật (0.771).
> 4. **Khi retrieval đã tốt, nút thắt chuyển sang LLM nhỏ.** `gpt-4.1-nano` rất rẻ (lần chạy đầu cả 4 chiến lược hết khoảng 13,4k token LLM và 18,8k token embedding; chạy lại tốn 0 token nhờ cache). Nhưng nó đọc nhầm danh sách ở Q3 trong 3/4 chiến lược dù chunk đúng đã ở top-1.

**Failure case — phân tích lỗi (bắt buộc):**
> **Case 1 — Q3 "Mỗi bạn đọc được mượn tối đa bao nhiêu tài liệu về nhà?"**
> - **Hỏng thế nào:** không filter thì tài liệu giảng viên lên top-1 (3/4 chiến lược); Sentence trả lời "10 tài liệu" (sai đối tượng), Heading từ chối. Có filter thì retrieval đúng, nhưng agent vẫn sai ở 3/4: Fixed ghi "05 tài liệu cho sinh viên và **03 tài liệu cho học viên cao học**", Recursive trả lời "**3 tài liệu**" (lấy nhầm dòng "đọc tại chỗ: 03 tài liệu"), Sentence chỉ nêu "5 tài liệu".
> - **Vì sao:** (1) embedding coi câu của giảng viên và sinh viên gần như giống nhau (0.800), nên chỉ metadata mới tách được; (2) dữ liệu gốc là danh sách xuống dòng ("+ Tiếng Việt: 05 / + Tiếng Anh: 03"), đặt sát mục "đặt cọc của học viên cao học" và mục 2.2 "đọc tại chỗ: 03 tài liệu". Fixed/Recursive cắt chunk ngang qua các mục này nên ngữ cảnh chứa nhiều con số của nhiều đối tượng; (3) model nano yếu ở việc gắn con số với đúng đối tượng/loại tài liệu.
> - **Đề xuất:** filter `{"audience": ["student", "all"]}`; chunk theo heading để mục 2.1 đứng riêng (Heading là chiến lược duy nhất nano trả lời đúng); với câu hỏi định lượng, dùng model lớn hơn một bậc (`gpt-4.1-mini`) chỉ cho bước sinh câu trả lời, hoặc yêu cầu trong prompt "liệt kê theo từng loại/đối tượng".
>
> **Case 2 — mâu thuẫn nguồn ở Q1 (lỗi ở tầng dữ liệu):** trang "Quy định mượn – trả tài liệu" (không ghi ngày) ghi 500đ và "không quá 1 học kỳ", còn Nội quy ký 01/11/2022 và trang Phục vụ ghi 1.000đ và 45 ngày. Việc tách file theo audience còn **nhân đôi** chunk "500đ". Với MiniLM, hai bản sao này chiếm top-1/2 và Fixed/Recursive mất hẳn đáp án. Với OpenAI thì 1.000đ thắng, nhưng chỉ cần thêm filter `student` là đáp án đổi thành 500đ. Retrieval không biết văn bản nào còn hiệu lực. **Đề xuất:** chỉ tách phần khác nhau theo audience (phần chung để `audience: all`); thêm metadata ngày hiệu lực hoặc `superseded_by` và ưu tiên văn bản mới nhất; agent nên nêu rõ mâu thuẫn kèm hai trích dẫn. Thí nghiệm dedupe với MiniLM: Heading có chunk 1.000đ ở hạng 2–3 (trước đó hạng 3), Recursive từ không có lên hạng 3, Fixed không cải thiện vì hai bản sao bị cắt lệch nhau.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng tài liệu, cùng câu hỏi, chỉ đổi một dòng chunker thì điểm chênh 1 điểm (8–9/10). Đổi embedding thì số lượt đáp án ở top-1 nhảy từ 11/20 lên 17/20 và thứ hạng chunker đảo. Cần chốt embedding tốt trước rồi mới tối ưu chunker. Mỗi chiến lược hỏng ở một kiểu khác nhau: Fixed cắt giữa từ và trộn con số của nhiều mục; Recursive bị nhân đôi phần chung; Sentence để đáp án rơi xuống hạng 2; Heading bị mảnh đuôi quá ngắn. Heading thắng về khả năng truy vết (biết "Điều 7" hay "mục 2.1") và giữ ranh giới giữa các mục.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> (1) Không nhân đôi phần chung khi tách file theo `audience`, và gắn metadata hiệu lực để xử lý các trang mâu thuẫn ngay từ khâu thu thập. (2) Mở rộng corpus sang trang của phòng Đào tạo/Công tác sinh viên và tăng lên khoảng 15–20 câu hỏi, để chênh lệch giữa các chiến lược có ý nghĩa thống kê. (3) Heading chunker gộp mảnh đuôi dưới 150 ký tự; giữ `gpt-4.1-nano` cho bước rẻ, chỉ nâng lên `gpt-4.1-mini` cho câu hỏi định lượng nếu ngân sách cho phép.

**Ghi chú kỹ thuật cho demo:** crawler mẫu ban đầu báo *mọi* URL của `lic.ut.edu.vn` là "disallowed by robots.txt". Nguyên nhân: `RobotFileParser.read()` gửi User-Agent `Python-urllib`, server trả 403, và robotparser hiểu 403 là cấm tất cả. Trong khi đó robots.txt thật (tải bằng User-Agent khai báo của script) là `Disallow:` rỗng, tức cho phép tất cả. Nhóm đã sửa `scripts/fetch_public_pages.py` để tải robots.txt bằng chính User-Agent của script (giữ nguyên ngữ nghĩa 401/403 là cấm), đồng thời bắt thêm `LookupError` (charset lỗi) để một URL hỏng không làm sập cả lượt chạy.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |

---

## Phụ lục — Repo cá nhân & kết quả chi tiết của từng thành viên

Mỗi thành viên nộp repo riêng `K4-DAY07-<HoVaTen>-<MSSV>`. Phần chung của nhóm giống hệt nhau ở cả 4 repo, phần riêng do từng người tự làm.

**Phần chung (giống nhau ở 4 repo):** `data/thu-vien-uth/` (8 tài liệu + `sources.csv`), `data/urls.csv`, `bench.py`, `src/llm.py` (LLM `gpt-4.1-nano`), `scripts/fetch_public_pages.py` (đã sửa lỗi robots.txt), `report/REPORT_NHOM.md` (bản này), `.gitignore` có `.env` và `.cache/`.

**Phần riêng (mỗi người tự làm):**
- `src/` hoàn thiện mọi TODO, `pytest tests/ -v` → 42 passed. `bench.py` gọi `agent.llm_fn` và `agent.build_prompt(question, results)`, nên `KnowledgeBaseAgent` của mỗi người đều lưu `self.llm_fn` và có method `build_prompt`.
- Dòng `STRATEGY` trong `bench.py` (bảng dưới) và file `ket_qua_benchmark.txt` sinh ra từ đó.
- `report/REPORT_CANHAN.md`. Mục 4 dùng 5 cặp câu của riêng mình (sửa `SIMILARITY_PAIRS` trong `bench.py`, ghi dự đoán trước khi chạy); mục 5 lấy từ bảng kết quả chi tiết của mình bên dưới.
- `.env` riêng (không commit): `EMBEDDING_PROVIDER=openai`, `OPENAI_API_KEY=<key của mình>`, `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`, `OPENAI_LLM_MODEL=gpt-4.1-nano`.

| Thành viên | `STRATEGY` trong `bench.py` | Dòng `TỔNG` trong `ket_qua_benchmark.txt` |
|-----------|------------------------------|---------------------------------------------|
| Nguyễn Văn Tài | `"heading"` | theo doc_id=10/10 · theo nội dung=8/10 · top-3: 5/5 |
| Nguyễn Đăng Thực | `"fixed"` | theo doc_id=10/10 · theo nội dung=9/10 · top-3: 5/5 |
| Lâm Hoàng Phúc | `"recursive"` | theo doc_id=10/10 · theo nội dung=9/10 · top-3: 5/5 |
| Nguyễn Đức Minh | `"sentence"` | theo doc_id=9/10 · theo nội dung=8/10 · top-3: 5/5 |

### Nguyễn Văn Tài — HeadingChunker (32 chunk, avg 314)

Bảng chi tiết nằm trong `report/REPORT_CANHAN.md` mục 5 của Tài: Q1–Q3 đúng 2/2, Q4 1/2 (mảnh đuôi 93 ký tự chiếm top-1), Q5 1/2 (agent bỏ sót Turnitin).

### Nguyễn Đăng Thực — FixedSizeChunker(400, 80) (30 chunk, avg 366)

| # | Câu hỏi | Top-1 chunk (tóm tắt) | Score | Liên quan? | Agent (tóm tắt) | Điểm |
|---|---------|------------------------|-------|-----------|-----------------|------|
| 1 | Phạt quá hạn | Nội quy Điều 7: "Quá hạn phải nộp phạt 1.000đ/cuốn/ngày" | 0.664 | Có | "phạt 1.000 đồng cho mỗi cuốn/ngày [1]" — đúng | 2 |
| 2 | Gia hạn | Phục vụ mượn–trả: "…45 ngày. Số lần được gia hạn: 01 lần…" | 0.675 | Có | "gia hạn 01 lần với thời gian 45 ngày [1]" — đúng | 2 |
| 3 | Hạn mức (filter `student`) | Quy định SV mục 2.1: "Tiếng Việt: 05 / Tiếng Anh: 03" | 0.631 | Có | "05 tài liệu cho sinh viên và 03 tài liệu cho học viên cao học…" — **sai**, gán nhầm "03" | 1 |
| 4 | Phòng đọc | Phục vụ phòng đọc: "Chỉ được mang vào phòng đọc…" | 0.715 | Có | "máy tính cá nhân, sách, tập vở và dụng cụ học tập [1], [3]" — đúng | 2 |
| 5 | Trùng lặp | Dịch vụ quét trùng lặp (có "Turnitin") | 0.645 | Có | "dịch vụ quét trùng lặp… phần mềm chống đạo văn Turnitin [1]" — đúng | 2 |

Top-3 có chunk đáp án: 5/5. A/B Q3 không filter: top-1 là chunk giảng viên "10 tài liệu" (0.666), đáp án sinh viên ở hạng 2; agent vẫn trả lời đúng "5 tiếng Việt + 3 tiếng Anh [2], [3]" (1/2).

### Lâm Hoàng Phúc — RecursiveChunker(400) (35 chunk, avg 262)

| # | Câu hỏi | Top-1 chunk (tóm tắt) | Score | Liên quan? | Agent (tóm tắt) | Điểm |
|---|---------|------------------------|-------|-----------|-----------------|------|
| 1 | Phạt quá hạn | Nội quy Điều 7: "Quá hạn phải nộp phạt 1.000đ/cuốn/ngày" | 0.659 | Có | "phạt 1.000 đồng/1 cuốn/1 ngày [2]" — đúng | 2 |
| 2 | Gia hạn | Phục vụ mượn–trả: mục mượn đọc tại chỗ + mượn về nhà (có "gia hạn: 01 lần…") | 0.657 | Có | "gia hạn 01 lần, mỗi lần kéo dài 45 ngày" — đúng | 2 |
| 3 | Hạn mức (filter `student`) | Quy định SV: "Tiếng Việt: 05 tài liệu + Tiếng Anh (Tham khảo): 03 tài liệu" | 0.586 | Có | "tối đa 3 tài liệu [3]" — **sai**, lấy nhầm dòng "đọc tại chỗ: 03 tài liệu" | 1 |
| 4 | Phòng đọc | Nội quy Điều 4: "Chỉ được mang vào phòng đọc…" | 0.719 | Có | "Máy tính cá nhân, Sách, tập vở và dụng cụ học tập [1][2]" — đúng | 2 |
| 5 | Trùng lặp | Dịch vụ quét trùng lặp (có "Turnitin") | 0.648 | Có | "…phần mềm chống đạo văn Turnitin [1]" — đúng | 2 |

Top-3 có chunk đáp án: 5/5. A/B Q3 không filter: top-1 là trang Phục vụ (`audience=all`) "8 cuốn (5 TV + 3 ngoại văn)" (0.620), agent trả lời "8 tài liệu (5 cuốn Tiếng Việt + 3 cuốn Ngoại văn)", đúng (2/2). Đây là chiến lược duy nhất không filter mà vẫn đúng. Điểm yếu: ở Q2, hạng 2–3 là hai chunk "500đ" giống hệt nhau (0.554), do phần chung bị nhân đôi khi tách file theo audience.

### Nguyễn Đức Minh — SentenceChunker(3) (41 chunk, avg 223)

| # | Câu hỏi | Top-1 chunk (tóm tắt) | Score | Liên quan? | Agent (tóm tắt) | Điểm |
|---|---------|------------------------|-------|-----------|-----------------|------|
| 1 | Phạt quá hạn | Phục vụ mượn–trả, mục Quá hạn: "phạt 1000 đồng/1 cuốn/1 ngày" | 0.673 | Có | "phạt 1000 đồng/1 cuốn/1 ngày [1]" — đúng | 2 |
| 2 | Gia hạn | Nội quy Điều 3: "thời gian là 45 ngày; 8 cuốn" | 0.679 | Không (thời hạn mượn, không phải gia hạn); đáp án ở hạng 2 (0.630) | "gia hạn 01 lần với thời gian 45 ngày [2]" — đúng | 1 |
| 3 | Hạn mức (filter `student`) | Quy định SV mục 3: "Không quá 1 học kỳ" | 0.624 | Không; đáp án ở hạng 2 (0.612) | "tối đa 5 tài liệu (đối với tiếng Việt) [2]" — thiếu 3 tài liệu tiếng Anh | 1 |
| 4 | Phòng đọc | Phục vụ phòng đọc: "Chỉ được mang vào phòng đọc…" | 0.733 | Có | "Máy tính cá nhân, Sách, tập vở và dụng cụ học tập [1][2]" — đúng | 2 |
| 5 | Trùng lặp | Dịch vụ quét trùng lặp (có "Turnitin") | 0.645 | Có | "…phần mềm chống đạo văn Turnitin [1]" — đúng | 2 |

Top-3 có chunk đáp án: 5/5. A/B Q3 không filter: top-1 và top-2 là chunk giảng viên (0.679), agent trả lời "tối đa 10 tài liệu [1]", **sai đối tượng** (0/2). Đây là bằng chứng rõ nhất cho việc cần metadata filter.