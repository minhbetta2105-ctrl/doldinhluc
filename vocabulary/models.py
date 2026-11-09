"""Models Vocabulary - khớp DRD của nhóm (B15-B18):
vocabulary_topic, vocabulary_word, vocabulary_attempt, vocabulary_answer.

Tên bảng do Django tự đặt (<app>_<model>) nên trùng đúng tên trong báo cáo.
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Level(models.TextChoices):
    BEGINNER = "BEGINNER", "Beginner"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    ADVANCED = "ADVANCED", "Advanced"


class Status(models.TextChoices):
    PUBLISHED = "PUBLISHED", "Hiển thị"
    HIDDEN = "HIDDEN", "Ẩn"


class ExerciseType(models.TextChoices):
    MCQ = "MCQ", "Trắc nghiệm (Multiple Choice)"
    MATCH = "MATCH", "Nối từ"
    DRAG = "DRAG", "Kéo & Thả"


class QuestionType(models.TextChoices):
    MCQ_MEANING = "MCQ_MEANING", "Trắc nghiệm - chọn nghĩa"
    MCQ_WORD = "MCQ_WORD", "Trắc nghiệm - điền từ"
    MATCH = "MATCH", "Nối từ"
    DRAG = "DRAG", "Kéo & Thả"


class Topic(models.Model):
    """B15: chủ đề từ vựng."""

    name = models.CharField("Tên chủ đề", max_length=150, unique=True,
                            error_messages={"unique": "Tên chủ đề đã tồn tại."})
    description = models.TextField("Mô tả", blank=True)
    level = models.CharField("Trình độ", max_length=20, choices=Level.choices, default=Level.BEGINNER)
    status = models.CharField("Trạng thái", max_length=20, choices=Status.choices, default=Status.HIDDEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Word(models.Model):
    """B16: từ vựng thuộc chủ đề."""

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="words")
    word = models.CharField("Từ / cụm từ", max_length=150)
    phonetic = models.CharField("Phiên âm", max_length=150, blank=True)
    part_of_speech = models.CharField("Loại từ", max_length=50, blank=True)
    meaning_vi = models.TextField("Nghĩa tiếng Việt")
    example_sentence = models.TextField("Câu ví dụ", blank=True)
    gap_sentence = models.TextField("Câu điền khuyết (Kéo & Thả)", blank=True)
    gap_answer = models.CharField("Đáp án ô trống", max_length=150, blank=True)
    audio_file = models.CharField("Đường dẫn audio", max_length=500, blank=True)
    status = models.CharField("Trạng thái", max_length=20, choices=Status.choices, default=Status.HIDDEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["word"]

    def __str__(self):
        return self.word


class Attempt(models.Model):
    """B17: một lượt luyện đã NỘP thành công (lượt chưa nộp không lưu)."""

    submission_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name="vocabulary_attempts")
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="attempts")
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    topic_snapshot = models.JSONField(default=dict)
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField()
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField()

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.CheckConstraint(check=Q(total_questions__gt=0), name="vocab_attempt_total_gt_0"),
            models.CheckConstraint(check=Q(correct_answers__lte=F("total_questions")),
                                   name="vocab_attempt_correct_lte_total"),
        ]

    @property
    def percent(self):
        return round(self.correct_answers * 100 / self.total_questions) if self.total_questions else 0


class Answer(models.Model):
    """B18: chi tiết từng đơn vị chấm của một lượt luyện."""

    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    word = models.ForeignKey(Word, on_delete=models.PROTECT, related_name="answers")
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    question_snapshot = models.JSONField()
    user_answer = models.TextField(blank=True)
    is_correct = models.BooleanField()
    order_no = models.PositiveIntegerField()

    class Meta:
        ordering = ["order_no"]
        constraints = [
            models.UniqueConstraint(fields=["attempt", "order_no"], name="vocab_answer_unique_order"),
        ]
