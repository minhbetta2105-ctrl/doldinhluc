from django.contrib import admin

from .models import Answer, Attempt, Topic, Word


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "status", "updated_at")
    list_filter = ("level", "status")
    search_fields = ("name",)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("word", "topic", "part_of_speech", "status")
    list_filter = ("topic", "status")
    search_fields = ("word", "meaning_vi")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "topic", "exercise_type", "correct_answers", "total_questions", "submitted_at")
    list_filter = ("exercise_type", "topic")
    readonly_fields = [f.name for f in Attempt._meta.fields]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "order_no", "question_type", "is_correct")
    readonly_fields = [f.name for f in Answer._meta.fields]
