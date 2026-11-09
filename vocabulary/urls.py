from django.urls import path
from core.integration_permissions import admin_permissions_required
from . import views

app_name = "vocabulary"

# Phân quyền model-level Q3; view nghiệp vụ được giữ nguyên.
can_view = admin_permissions_required("vocabulary.view_topic", "vocabulary.view_word", match_any=True)
can_add_topic = admin_permissions_required("vocabulary.add_topic")
can_change_topic = admin_permissions_required("vocabulary.change_topic")
can_delete_topic = admin_permissions_required("vocabulary.delete_topic")
can_view_word = admin_permissions_required("vocabulary.view_word")
can_add_word = admin_permissions_required("vocabulary.add_word")
can_change_word = admin_permissions_required("vocabulary.change_word")
can_delete_word = admin_permissions_required("vocabulary.delete_word")

urlpatterns = [
    path("", views.topic_list, name="topic_list"),
    path("topic/<int:pk>/", views.topic_detail, name="topic_detail"),
    path("topic/<int:pk>/start/", views.start_practice, name="start_practice"),
    path("practice/<uuid:key>/", views.practice, name="practice"),
    path("practice/<uuid:key>/submit/", views.submit_practice, name="submit_practice"),
    path("result/<int:pk>/", views.result, name="result"),
    path("manage/", can_view(views.manage_topics), name="manage_topics"),
    path("manage/topic/new/", can_add_topic(views.topic_create), name="topic_create"),
    path("manage/topic/<int:pk>/edit/", can_change_topic(views.topic_edit), name="topic_edit"),
    path("manage/topic/<int:pk>/status/", can_change_topic(views.topic_set_status), name="topic_set_status"),
    path("manage/topic/<int:pk>/delete/", can_delete_topic(views.topic_delete), name="topic_delete"),
    path("manage/topic/<int:topic_id>/words/", can_view_word(views.manage_words), name="manage_words"),
    path("manage/topic/<int:topic_id>/words/new/", can_add_word(views.word_create), name="word_create"),
    path("manage/word/<int:pk>/edit/", can_change_word(views.word_edit), name="word_edit"),
    path("manage/word/<int:pk>/status/", can_change_word(views.word_set_status), name="word_set_status"),
    path("manage/word/<int:pk>/delete/", can_delete_word(views.word_delete), name="word_delete"),
]
