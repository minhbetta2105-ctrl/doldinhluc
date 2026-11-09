from django.contrib import admin
from .models import ServiceFeedback


@admin.register(ServiceFeedback)
class ServiceFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "content_preview", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("created_at", "updated_at")

    def content_preview(self, obj):
        return (obj.content[:80] + "...") if len(obj.content) > 80 else obj.content
    content_preview.short_description = "Nội dung"
