from django.urls import path
from listening import views

app_name = "listening"

urlpatterns = [
    path("", views.exercise_list, name="exercise_list"),
    path("<int:pk>/", views.exercise_detail, name="exercise_detail"),
    path("<int:pk>/submit/", views.exercise_submit, name="exercise_submit"),
    path("attempt/<uuid:submission_key>/result/", views.attempt_result, name="attempt_result"),
]
