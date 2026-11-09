from django.db import models
from receptive.models import Exercise


class ListeningExerciseManager(models.Manager):
    """Manager tự động lọc các bài tập thuộc kỹ năng LISTENING."""
    def get_queryset(self):
        return super().get_queryset().filter(skill=Exercise.Skill.LISTENING)


class ListeningExercise(Exercise):
    """Proxy model cho Listening Exercise.
    Tái sử dụng 100% bảng reading_listening_exercise, KHÔNG tạo thêm bảng CSDL mới.
    """
    objects = ListeningExerciseManager()
    all_objects = models.Manager()

    def save(self, *args, **kwargs):
        self.skill = Exercise.Skill.LISTENING
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Bài luyện Listening"
        verbose_name_plural = "Quản lý bài Listening"
