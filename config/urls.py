"""URLconf tích hợp Nhóm 6 (Q1/Q6) – giữ route các module ở namespace gốc."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from core.views import home
from speaking.views import private_submission_audio

urlpatterns = [
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("admin/", admin.site.urls),
    # Hạn chế truy cập bản ghi Speaking: thuộc sở hữu học viên hoặc người có quyền quản lý.
    path("media/speaking_submissions/<path:relative_path>", private_submission_audio, name="private_speaking_audio"),
    path("", home, name="home"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("listening/", include("listening.urls", namespace="listening")),
    path("reading/", include("reading.urls", namespace="reading")),
    path("writing/", include("writing.urls", namespace="writing")),
    path("speaking/", include("speaking.urls", namespace="speaking")),
    path("vocabulary/", include("vocabulary.urls", namespace="vocabulary")),
    path("progress/", include("progress.urls", namespace="progress")),
    path("feedback/", include("feedback.urls", namespace="feedback")),
    path("management/", include("management.urls", namespace="management")),
]

# Phục vụ file media trực tiếp trong môi trường development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
