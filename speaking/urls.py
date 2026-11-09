from django.urls import path
from . import views

app_name = "speaking"

urlpatterns = [
    # UC-SPK-01: Danh sách bài luyện Speaking
    path("", views.exercise_list, name="exercise_list"),

    # UC-SPK-02: Làm bài luyện Speaking trực tiếp
    path("<int:exercise_id>/", views.exercise_detail, name="exercise_detail"),

    # UC-SPK-03: Nộp bài Speaking
    path("<int:exercise_id>/submit/", views.exercise_submit, name="exercise_submit"),

    # UC-SPK-04: Xem kết quả bài Speaking
    path("submission/<uuid:submission_key>/", views.submission_result, name="submission_result"),
]
