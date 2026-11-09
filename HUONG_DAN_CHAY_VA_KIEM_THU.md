# DOL IELTS ĐÌNH LỰC — Bản thống nhất giao diện

Bản này phát triển từ `du_an_django(1).zip` của nhóm. Giữ các app hiện có và dữ liệu SQLite/media gốc. Không chuyển sang React, DRF hay project Django mới.

## 1. Chuẩn bị và chạy trên Windows/PyCharm

1. Giải nén ZIP và mở thư mục `doldinhluc` (thư mục chứa `manage.py`).
2. **Bảo quản file `.env` đang dùng ở máy cũ và chép lại vào thư mục này.** ZIP bàn giao **không chứa `.env` hoặc API key thật** để tránh lộ thông tin. `.env.example` chỉ là mẫu.
3. Bản ZIP không kèm `.venv312` vì môi trường ảo Windows không nên phân phối qua ZIP. Nếu m đang làm trên thư mục PyCharm cũ, giữ lại `.venv312`. Nếu môi trường mới, tạo venv Python 3.12 và cài `pip install -r requirements.txt`.
4. Mở Terminal tại `doldinhluc` và chạy:

```powershell
.\.venv312\Scripts\python.exe manage.py check
.\.venv312\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv312\Scripts\python.exe manage.py runserver
```

Đường dẫn kiểm tra:
- Trang chủ: `http://127.0.0.1:8000/`
- Listening/Reading/Writing/Speaking/Vocabulary: `/listening/`, `/reading/`, `/writing/`, `/speaking/`, `/vocabulary/`
- Tiến độ: `/progress/`
- Góp ý: `/feedback/`
- Khu giáo viên: `/management/` (đòi hỏi staff và quyền Django tương ứng)
- Django Admin kỹ thuật: `/admin/` (không xóa)

Không chạy lệnh seed phá hủy dữ liệu; đã giữ lại database hiện có và media trong bản ZIP.

## 2. Những gì đã thay đổi

- Một `templates/base.html` và `templates/core/_header.html`, `_footer.html` dùng chung.
- Tách CSS gốc ra các file static theo module để không mất style đang có; đặt CSS token chung trong `site.css`.
- Writing và Speaking nay kế thừa từ `base.html`, giữ nguyên các trang con, JS ghi âm và logic AI.
- Accounts, Vocabulary, Feedback, Reading, Listening và Progress dùng thanh điều hướng chung; giao diện quản lý Vocabulary kế thừa khu giáo viên.
- Trang chủ thiết kế lại bằng HTML/CSS và một minh họa SVG gốc, không sao chép website tham khảo, không đưa số liệu học viên giả vào nội dung.
- `/management/` trở thành dashboard có liên kết tới Reading, Listening, Writing, Speaking, Vocabulary, Feedback và tài khoản theo quyền.
- Giao diện nghiệp vụ để giáo viên thêm/sửa/ẩn/hiện đề Reading/Listening và quản lý câu hỏi/phương án thông qua model `receptive` vốn có. **Không sinh model hay migration mới.**
- Chuẩn hóa URL theo Django `reverse`/`{% url %}`, bỏ mã UC hiển thị ra giao diện; mã UC vẫn có thể còn trong comment kỹ thuật.
- Bảo vệ route phát file Speaking đã nộp bằng kiểm tra chủ sở hữu/nhóm HOC_VIEN hoặc quyền quản lý.
- Bỏ API key thực khỏi `.env.example`, bổ sung `.venv312/` vào `.gitignore`.

## 3. Đối chiếu học phần MIS3010

Dùng tài liệu sẵn có trong project và các slide/bài thực hành mà nhóm đã gửi:

- **Chương 1:** các View Django, URL và template; vẫn giữ MVT và Django Templates.
- **Chương 2:** Django ORM, model, SQLite; không tạo bảng dữ liệu mới hoặc sửa schema.
- **Chương 3:** xác thực, Django Groups, model permissions và phân quyền quản trị trong view.
- **Chương 4:** `ModelForm`, kiểm tra dữ liệu trên server, `GET`/`POST` và `CSRF`; upload sử dụng `multipart/form-data`.
- **Chương 5:** slide hướng dẫn REST API/DRF. Bản này **không** thêm DRF vì phạm vi là chuẩn hóa Django Templates; giữ nguyên các API integration (Gemini) hiện có.
- **Chương 6:** slide quản lý Static/Media. CSS/JS/logo được dùng với `{% static %}`; file nộp được lưu bằng Django FileField, có kiểm tra quyền truy cập audio Speaking trong môi trường local.
- **Chương 7:** ZIP không có file slide Chương 7 riêng để đối chiếu chi tiết; không suy đoán kiến thức trong đó, chỉ giữ và kiểm tra cơ chế authentication/session hiện có.

## 4. Kết quả kiểm thử

Bản gốc chạy 181 test: **5 lỗi đã có sẵn**. Hai lỗi liên quan biểu diễn `7.5` trong khi locale `vi` hiển thị `7,5`; ba lỗi còn lại kỳ vọng cũ không còn phù hợp (admin login/DEBUG cho staff). Test được cập nhật về **hành vi bảo mật hiện hành**, không thay đổi thang điểm hay logic Writing.

Bản sau cải tiến có **189 test, toàn bộ PASS** (bao gồm các test smoke cho navigation, trang chủ, phân quyền và form CRUD mới, bảo vệ audio Speaking).

Chạy:
```powershell
.\.venv312\Scripts\python.exe manage.py test
```

Các lệnh `manage.py check` và `makemigrations --check --dry-run` đều thành công, **không có migration mới**.

## 5. Phạm vi chưa kiểm chứng / lưu ý

- Đã test trang qua Django Test Client và HTTP local, **chưa có kiểm thử visual browser thành công** trong môi trường bàn giao; kiểm tra thêm ở desktop/tablet/mobile (Chrome hoặc Edge) sau khi mở dự án trong PyCharm.
- Không gọi Gemini API thật trong test; chỉ mock integration. Sau khi chép lại `.env`, nên test thủ công một bài Writing và Speaking mới.
- Trong production không được phục vụ toàn bộ `MEDIA_ROOT` công khai bằng Nginx/CDN nếu chứa bài nói riêng tư. Route bảo vệ audio Speaking trong bản này phục vụ luồng Django; cần đảm bảo web server production không bypass route.
- Đây là bản chuẩn hóa giao diện và nghiệp vụ quản lý, không phải khẳng định toàn hệ thống đã qua security audit chuyên sâu hoặc chứng nhận accessibility.

## 6. Kiểm tra hồi quy thực tế

Trên máy m, đăng nhập bằng tài khoản HOC_VIEN và lần lượt thực hiện: Reading, Listening, Writing, Speaking (ghi âm/Upload), Vocabulary, xem Progress, gửi Feedback. Sau đó đăng nhập tài khoản quản trị có quyền và vào `/management/` để kiểm tra thêm/sửa/ẩn đề. Luôn sao lưu database trước khi nhập dữ liệu thật mới.
