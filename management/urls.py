from django.urls import path
from . import views, progress_views

app_name = "management"

urlpatterns = [
    path("students/progress/", progress_views.student_progress_list, name="student_progress_list"),
    path("students/progress/<int:user_id>/", progress_views.student_progress_detail, name="student_progress_detail"),
    # Giáo viên: Reading/Listening trên bảng receptive hiện có (không tạo bảng mới)
    path("reading/", views.reading_exercise_list, name="reading_exercise_list"),
    path("reading/new/", views.reading_exercise_create, name="reading_exercise_create"),
    path("reading/<int:pk>/edit/", views.reading_exercise_edit, name="reading_exercise_edit"),
    path("reading/<int:pk>/status/", views.reading_exercise_status, name="reading_exercise_status"),
    path("reading/<int:pk>/questions/", views.reading_question_list, name="reading_question_list"),
    path("reading/<int:pk>/questions/new/", views.reading_question_create, name="reading_question_create"),
    path("reading/<int:pk>/questions/<int:qpk>/edit/", views.reading_question_edit, name="reading_question_edit"),
    path("reading/<int:pk>/questions/<int:qpk>/options/new/", views.reading_option_create, name="reading_option_create"),
    path("reading/<int:pk>/questions/<int:qpk>/options/<int:opk>/edit/", views.reading_option_edit, name="reading_option_edit"),
    path("listening/", views.listening_exercise_list, name="listening_exercise_list"),
    path("listening/new/", views.listening_exercise_create, name="listening_exercise_create"),
    path("listening/<int:pk>/edit/", views.listening_exercise_edit, name="listening_exercise_edit"),
    path("listening/<int:pk>/status/", views.listening_exercise_status, name="listening_exercise_status"),
    path("listening/<int:pk>/questions/", views.listening_question_list, name="listening_question_list"),
    path("listening/<int:pk>/questions/new/", views.listening_question_create, name="listening_question_create"),
    path("listening/<int:pk>/questions/<int:qpk>/edit/", views.listening_question_edit, name="listening_question_edit"),
    path("listening/<int:pk>/questions/<int:qpk>/options/new/", views.listening_option_create, name="listening_option_create"),
    path("listening/<int:pk>/questions/<int:qpk>/options/<int:opk>/edit/", views.listening_option_edit, name="listening_option_edit"),

    # Điểm vào khu vực quản trị: /management/
    path("", views.dashboard_redirect, name="dashboard"),

    # UC-WRI-05: Quản lý danh sách đề Writing (Hình 42)
    path("writing/", views.writing_prompt_list, name="writing_prompt_list"),
    path("writing/prompts/", views.writing_prompt_list, name="writing_prompt_list_alias"),

    # UC-WRI-05: Thêm đề Writing mới (Hình 43)
    path("writing/new/", views.writing_prompt_create, name="writing_prompt_create"),

    # UC-WRI-05: Xem thông tin chi tiết đề
    path("writing/<int:pk>/", views.writing_prompt_detail, name="writing_prompt_detail"),

    # UC-WRI-05: Chỉnh sửa đề Writing (Hình 43)
    path("writing/<int:pk>/edit/", views.writing_prompt_edit, name="writing_prompt_edit"),

    # UC-WRI-05: Thay đổi trạng thái hiển thị bằng POST
    path("writing/<int:pk>/status/", views.writing_prompt_status_toggle, name="writing_prompt_status_toggle"),

    # UC-WRI-06: Chọn đề cần quản lý nội dung hỗ trợ
    path("writing/support/", views.writing_support_index, name="writing_support_index"),

    # UC-WRI-06: Chỉnh sửa nội dung hỗ trợ của đề (Hình 44)
    path("writing/<int:pk>/support/", views.writing_support_manage, name="writing_support_manage"),

    # ==========================================================================
    # UC-SPK-05: Quản lý bài luyện Speaking
    # ==========================================================================
    path("speaking/", views.speaking_exercise_list, name="speaking_exercise_list"),
    path("speaking/new/", views.speaking_exercise_create, name="speaking_exercise_create"),
    path("speaking/<int:pk>/", views.speaking_exercise_detail, name="speaking_exercise_detail"),
    path("speaking/<int:pk>/edit/", views.speaking_exercise_edit, name="speaking_exercise_edit"),
    path("speaking/<int:pk>/status/", views.speaking_exercise_status_toggle, name="speaking_exercise_status_toggle"),

    # UC-SPK-06: Quản lý nội dung hỗ trợ Speaking
    path("speaking/support/", views.speaking_support_index, name="speaking_support_index"),
    path("speaking/<int:pk>/support/", views.speaking_support_manage, name="speaking_support_manage"),
]
