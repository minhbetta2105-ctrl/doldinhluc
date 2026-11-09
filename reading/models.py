from django.db import models
from receptive.models import Exercise


class ReadingExerciseManager(models.Manager):
    """Manager tự động lọc các bài tập thuộc kỹ năng READING."""
    def get_queryset(self):
        return super().get_queryset().filter(skill=Exercise.Skill.READING)


class ReadingExercise(Exercise):
    """Proxy model cho Reading Exercise.
    Tái sử dụng 100% bảng reading_listening_exercise, KHÔNG tạo thêm bảng CSDL mới.
    """
    objects = ReadingExerciseManager()
    all_objects = models.Manager()

    def save(self, *args, **kwargs):
        self.skill = Exercise.Skill.READING
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Bài luyện Reading"
        verbose_name_plural = "Quản lý bài Reading"
