import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class SpeakingExercise(models.Model):
    """
    Bảng 1: Đề luyện Speaking (speaking_exercise) theo thiết kế ERD.
    """
    class Part(models.TextChoices):
        PART_1 = "PART_1", "Part 1"
        PART_2 = "PART_2", "Part 2"
        PART_3 = "PART_3", "Part 3"

    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"
        HIDDEN = "HIDDEN", "Hidden"

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    part = models.CharField(max_length=10, choices=Part.choices)
    topic = models.CharField(max_length=100)
    prompt_text = models.TextField()
    level = models.CharField(max_length=20, choices=Level.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.HIDDEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "speaking_exercise"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.pk and self.submissions.exists():
            fields = ("title", "part", "topic", "prompt_text", "level")
            original = SpeakingExercise.objects.filter(pk=self.pk).values(*fields).first()
            if original:
                changed = [field for field in fields if getattr(self, field) != original[field]]
                if changed:
                    raise ValidationError(
                        "Đề đã có bài nộp; không được đổi nội dung hoặc trình độ. "
                        "Có thể Ẩn/Hiện đề để bảo toàn lịch sử. Trường bị thay đổi: " + ", ".join(changed)
                    )

    def delete(self, *args, **kwargs):
        if self.pk and self.submissions.exists():
            raise ValidationError(
                "Không thể xóa đề bài đã có bài nộp của học viên. Hãy chuyển trạng thái sang HIDDEN để ẩn đề."
            )
        return super().delete(*args, **kwargs)

    @property
    def has_submissions(self):
        if not self.pk:
            return False
        return self.submissions.exists()

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    def __str__(self):
        return f"{self.get_part_display()}: {self.title}"


class SpeakingSupport(models.Model):
    """
    Bảng 2: Nội dung hỗ trợ Speaking (speaking_support) gắn 1-1 với SpeakingExercise.
    """
    exercise = models.OneToOneField(
        SpeakingExercise,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="support"
    )
    idea_hint = models.TextField(blank=True)
    sample_answer = models.TextField(blank=True)
    suggested_vocabulary = models.TextField(blank=True)
    sample_audio_file = models.FileField(
        upload_to="speaking_samples/",
        max_length=500,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "speaking_support"

    def __str__(self):
        return f"Support: {self.exercise.title}"


class SpeakingSubmission(models.Model):
    """
    Bảng 3: Bài nộp Speaking (speaking_submission) lưu bài nộp audio và kết quả chấm AI.
    """
    class Status(models.TextChoices):
        GRADING = "GRADING", "Grading"
        GRADED = "GRADED", "Graded"
        FAILED = "FAILED", "Failed"

    id = models.BigAutoField(primary_key=True)
    submission_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="speaking_submissions"
    )
    exercise = models.ForeignKey(
        SpeakingExercise,
        on_delete=models.PROTECT,
        related_name="submissions"
    )
    exercise_snapshot = models.JSONField()
    audio_file = models.FileField(
        upload_to="speaking_submissions/%Y/%m/",
        max_length=500
    )
    overall_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )
    fluency_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )
    pronunciation_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )
    vocabulary_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )
    grammar_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )
    feedback = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GRADING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "speaking_submission"
        ordering = ["-submitted_at"]

    def clean(self):
        super().clean()
        errors = {}
        if self.status == self.Status.GRADED:
            if self.overall_score is None:
                errors["overall_score"] = "Bài nộp ở trạng thái GRADED bắt buộc phải có điểm overall_score."
        elif self.status == self.Status.GRADING:
            if self.overall_score is not None:
                errors["overall_score"] = "Bài nộp đang ở trạng thái GRADING thì điểm phải là NULL."
        elif self.status == self.Status.FAILED:
            if self.overall_score is not None:
                errors["overall_score"] = "Bài nộp ở trạng thái FAILED thì điểm phải là NULL."

        if self.overall_score is not None:
            if self.overall_score < 0 or self.overall_score > 9:
                errors["overall_score"] = "Điểm IELTS Speaking chỉ hợp lệ trong khoảng 0 đến 9."

        if not self.exercise_snapshot or not isinstance(self.exercise_snapshot, dict):
            errors["exercise_snapshot"] = "exercise_snapshot phải là một dictionary chứa thông tin đề tại thời điểm nộp."

        if errors:
            raise ValidationError(errors)

    @property
    def is_graded(self):
        return self.status == self.Status.GRADED

    @property
    def is_grading(self):
        return self.status == self.Status.GRADING

    @property
    def is_failed(self):
        return self.status == self.Status.FAILED

    def __str__(self):
        return f"Speaking Submission #{self.id} ({self.status})"
