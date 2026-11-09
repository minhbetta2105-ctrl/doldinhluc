# DOL IELTS Đình Lực — Bản source đã chỉnh sửa trực tiếp

## 1. Phạm vi và nguyên tắc

Đây là bản mã nguồn đã sửa từ dự án Django do nhóm cung cấp; thư mục gốc là `doldinhluc`, cấu hình Django vẫn nằm ở `config/`. Không tạo dự án Django mới, không đổi tên app, không thay database schema/migrations và không thay thuật toán chấm bài Writing/Speaking.

**Lưu ý dữ liệu:** ZIP kèm `db.sqlite3` xuất phát từ bản người dùng tải lên, đã được thêm 9 đề Speaking mẫu. Nếu máy bạn có database mới hơn, **sao lưu database đó và ưu tiên giữ database mới**, rồi chỉ chạy lệnh seed idempotent bên dưới để bổ sung đề Speaking mà không xóa lịch sử cũ. Sao lưu và giữ thư mục `media/` của máy bạn nếu nó có audio được nộp sau thời điểm gửi ZIP.

## 2. Những phần đã sửa

- Reading, Listening, Writing, Speaking và Vocabulary dùng chung bộ lọc từ `templates/core/_practice_filter.html`, CSS `static/css/practice-ui.css`; tìm kiếm chủ đề hỗ trợ nhập/chọn gợi ý từ chủ đề thực có trong CSDL khi model có trường phù hợp.
- Reading/Listening có bộ lọc chủ đề; bài Reading dùng vùng passage sticky có thể cuộn độc lập; Listening có player cùng bảng điều hướng trong cột sticky khi màn hình đủ rộng. Màn hình nhỏ có bố cục responsive.
- Chỉnh lỗi lựa chọn True/False hiển thị lặp bằng template filter `receptive/templatetags/receptive_tags.py` mà không thay mã đáp án trong database.
- Sửa quy tắc height/flex trong CSS tài khoản khiến Footer bị hiển thị chèn giữa nội dung, đồng thời bổ sung quy tắc Footer chung.
- Thống nhất các phần quản lý hỗ trợ Speaking/Writing bằng `static/css/teacher-support.css` và template quản lý hiện có.
- Giao diện xem kết quả Speaking bổ sung điểm tổng dạng vòng, radar 4 tiêu chí và thang điểm thành phần như Writing (dùng điểm do Gemini đã lưu). Giữ lại transcript, audio, phản hồi chi tiết, danh sách điểm mạnh/yếu và gợi ý sửa lỗi.
- Thêm command `seed_speaking_demo`: 9 bài luyện mới (3 bài cho Part 1, 3 bài Part 2, 3 bài Part 3), có hướng dẫn, bài mẫu, từ vựng, không tạo bản trùng khi chạy lại.
- Tách phạm vi quản trị kỹ thuật: `is_superuser=True` mới vào Django Admin `/admin/`. Giáo viên là staff có Django model permissions, quản lý nội dung và xem tiến độ qua `/management/`, được xem tài khoản nhưng KHÔNG được khóa/mở hoặc cấp/thu hồi HOC_VIEN.
- Thêm lệnh `grant_teacher_permissions <username>` để chủ dự án chủ động cấp quyền nội dung cho **tài khoản staff đã có**. Lệnh không tạo tài khoản hay Group mới.
- Thêm màn hình giáo viên xem danh sách và lịch sử tiến độ học viên từ các bảng nộp bài có sẵn, không tạo bảng mới.
- Thống nhất khóa nội dung Speaking sau khi phát sinh bài nộp giữa Model, Teacher Form và Django Admin; không sửa/xóa điểm AI trong Admin.

## 3. Chạy trên Windows mà không dùng môi trường ảo

Mở Terminal ở chính thư mục `doldinhluc` có `manage.py`, với Python 3.12 đã cài:

```powershell
py -3.12 --version
py -3.12 -m pip install -r requirements.txt
py -3.12 manage.py check
py -3.12 manage.py runserver
```

Mở http://127.0.0.1:8000/ . Nếu đã cài thư viện thì có thể bỏ qua pip. Trong IDE chọn **System Interpreter** của Python 3.12. Cài thư viện vào Python toàn máy có thể ảnh hưởng các dự án khác dùng cùng interpreter.

Đặt `.env` của dự án đang sử dụng (với GEMINI_API_KEY) vào thư mục cùng cấp với `manage.py`. ZIP **không kèm `.env`**, không kèm Python virtualenv. Không chia sẻ API key công khai.

## 4. Quản lý dữ liệu và quyền

Cập nhật dữ liệu Speaking mẫu vào database hiện có (không phá hủy bản ghi cũ):

```powershell
py -3.12 manage.py seed_speaking_demo
```

Sau khi tự tạo tài khoản giáo viên và đánh dấu `is_staff=True`, tài khoản superuser/chủ dự án có thể tự cấp bộ quyền nghiệp vụ đã được giới hạn bằng lệnh:

```powershell
py -3.12 manage.py grant_teacher_permissions <username_giao_vien>
```

Không dùng lệnh trên cho tài khoản superuser hoặc học viên thường. Giáo viên quản lý nội dung: `/management/`. Superuser quản trị kỹ thuật và quyền người dùng: `/admin/`.

Lưu ý: `grant_teacher_permissions` chỉ **thêm** các quyền theo danh sách an toàn; nếu trước đó một giáo viên đã được cấp `auth.change_user`, `is_superuser=True` hoặc các quyền tương tự, cần chủ dự án thu hồi chúng trong Django Admin để bảo đảm đúng ma trận phân quyền. Quyền chặn khóa/cấp HOC_VIEN đã được kiểm tra trực tiếp trong View cho mọi staff không phải superuser.

## 5. Kiểm thử đã chạy

Trong môi trường sửa source:

- `python manage.py test`: **200 tests — OK** (bao gồm 11 test về UI/phân quyền mới và các test ban đầu).
- `python manage.py check`: **System check identified no issues**.
- `python manage.py makemigrations --check --dry-run`: **No changes detected**.
- Lệnh Speaking seed chạy hai lần: lần thứ hai tạo 0 bài mới (idempotent).

**Giới hạn:** Môi trường thử nghiệm chặn điều hướng Chromium/Playwright (`net::ERR_BLOCKED_BY_ADMINISTRATOR`). Do đó chưa xác minh ảnh chụp browser ở 390px/768px/1440px hoặc thao tác thực tế MediaRecorder/Gemini API. Cần mở project ở máy Windows để kiểm tra giao diện và chấm bài thật. Bộ test AI dùng mock, không tiêu thụ Gemini API và không xác nhận chất lượng chấm của mô hình.

## 6. Các trang nên kiểm tra thủ công

1. Trang chủ / Đăng ký / Đăng nhập: Footer nằm sau nội dung, không đè biểu mẫu.
2. Reading và Listening: lọc theo chủ đề, tiêu đề, trình độ, dạng câu hỏi; mở đề, cuộn bài; kiểm tra player/passage dễ truy cập; True/False chỉ hiển thị một nhãn; nộp bài vẫn chấm đúng.
3. Writing và Speaking: bộ lọc gọn, nộp bài, xem điểm và nhận xét AI theo dữ liệu thật.
4. Speaking: thấy 9 đề mẫu; thử ghi âm trình duyệt/đưa file lên; kết quả hiển thị radar, điểm thành phần, transcript, sửa lỗi nếu Gemini trả về.
5. Vocabulary: lọc từ khóa/tên chủ đề, cuộn các card và Footer không đè.
6. Giáo viên: `/management/`, tạo/ẩn đề, quản lý support, xem tiến độ; không khóa/cấp quyền học viên. Superuser: `/admin/`, quản lý User/Group.

Tất cả phần ngoài danh sách sửa được giữ theo logic hiện tại của dự án.
