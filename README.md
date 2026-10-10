# Ôn tập HCM202 – Tư tưởng Hồ Chí Minh

Web ôn trắc nghiệm môn HCM202 (673 câu), dựng lại từ web ôn tập HDH-Chuong2-OnTap với ngân hàng câu hỏi mới.

- Trắc nghiệm 3–5 đáp án; câu nhiều đáp án đúng ("Chọn 2") chấm đủ mới tính đúng.
- Sau khi trả lời: hiện đáp án đúng và ghi chú *Kiểu hỏi khác* (cách hỏi khác của cùng câu) từ tài liệu.
- Lọc câu sai / chưa làm / đánh dấu ★, chế độ ngẫu nhiên, bản đồ câu, tìm kiếm (Ctrl+K), sáng/tối, đồng bộ tiến độ.
- 3 câu tài liệu gốc chưa ghi đáp án sẽ hiện "Chưa có đáp án chính thức".

## Chạy trên máy

```bash
python -m http.server 8000
```

Mở `http://localhost:8000`.

## Cập nhật câu hỏi

`data/hcm202.json` được tạo từ file Word:

```bash
python tools/build_questions.py "duong/dan/HCM202.docx"
```

Quy ước trong file Word: câu hỏi bắt đầu bằng `#`, đáp án `A.`–`D.` (đáp án cuối kết thúc bằng `@`), dòng tiếp theo là chữ cái đáp án đúng. Script tự gộp câu trùng, ghép "Kiểu hỏi khác" vào ghi chú và bỏ tên / số điện thoại người đóng góp kèm trong câu.
