from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ServiceFeedback(models.Model):
    """
    Bảng service_feedback: Đánh giá/góp ý của học viên về trải nghiệm website.
    """
    class Status(models.TextChoices):
        VISIBLE = "VISIBLE", "Hiển thị"
        HIDDEN = "HIDDEN", "Ẩn"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.VISIBLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_feedback"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if not (self.content or "").strip():
            raise ValidationError({"content": "Nội dung đánh giá không được để trống."})

    @property
    def is_visible(self):
        return self.status == self.Status.VISIBLE

    def __str__(self):
        return f"Feedback #{self.id} by {self.user.username}"
