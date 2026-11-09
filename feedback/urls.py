from django.urls import path
from . import views

app_name = "feedback"

urlpatterns = [
    # UC-FBK-01: Học viên gửi đánh giá / góp ý
    path("", views.feedback_submit, name="feedback_submit"),

    # UC-FBK-02: Quản trị viên xem danh sách đánh giá
    path("manage/", views.feedback_list, name="feedback_list"),

    # UC-FBK-03: Ẩn/Hiện đánh giá
    path("<int:pk>/status/", views.feedback_status_toggle, name="feedback_status_toggle"),

    # UC-FBK-03: Xóa đánh giá (có xác nhận)
    path("<int:pk>/delete/", views.feedback_delete, name="feedback_delete"),
]
