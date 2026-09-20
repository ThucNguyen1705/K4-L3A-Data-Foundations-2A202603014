# Biến thể K4-L3A — Truy xuất Dịch vụ/Quy định Đại học

L3A dùng chung cam kết mã nguồn cốt lõi (core coding contract) với L3B, nhưng Giai đoạn 2 (Phase 2) phải xây dựng cơ sở tri thức (knowledge base) về **dịch vụ hoặc quy định đại học** — đăng ký học phần, học phí, học bổng, thư viện, ký túc xá, phúc khảo.

> Lớp L3B cùng bài học này crawl chủ đề **thương mại điện tử** (đổi trả/bảo hành) thay vì đại học — hai lớp thu thập dữ liệu khác nhau nhưng cùng ràng buộc kỹ thuật và cùng rubric chấm điểm bên dưới.

## Quy tắc riêng của L3A

- Mỗi tài liệu (document) phải có metadata `audience` (`student` / `faculty` / `staff` / `all`) và ít nhất một trường (field) hữu ích khác (`department`, `category`, `language`...).
- Ngoài `audience`, mỗi tài liệu phải có `source_url`, `retrieved_at` và `document_version`; chỉ dùng quy định/dịch vụ công khai hoặc được phép chia sẻ.
- Trong 5 câu hỏi đánh giá (benchmark query), có ít nhất một câu hỏi cần `metadata_filter={"audience": "student"}` để tránh lấy tài liệu dành cho đối tượng khác.
- Ít nhất một thành viên thử chia nhỏ (chunking) theo tiêu đề/mục (heading/section) của sổ tay hoặc quy định học vụ.
- Câu trả lời chuẩn (Gold answer) phải trích được từ tài liệu nhóm thu thập, không suy đoán quy định của trường.

Thư mục `data/university/` có dữ liệu khởi động nhỏ; nhóm vẫn cần bổ sung tập tài liệu (corpus) 5–10 tài liệu theo yêu cầu Lab.
