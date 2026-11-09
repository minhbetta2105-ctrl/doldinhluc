from django.contrib import admin
from receptive.models import Exercise, Question, Option, Attempt, Answer


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    fields = ("order_no", "option_key", "option_text")
    ordering = ("order_no", "id")


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ("order_no", "question_type", "question_text", "correct_answers", "explanation", "status")
    ordering = ("order_no", "id")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "skill", "level", "topic", "status", "created_at")
    list_filter = ("skill", "level", "status")
    search_fields = ("title", "topic", "description")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "exercise", "order_no", "question_type", "status")
    list_filter = ("exercise__skill", "question_type", "status")
    search_fields = ("question_text", "exercise__title")
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "order_no", "option_key", "option_text")
    search_fields = ("option_text", "option_key")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "user_answer", "is_correct", "question_snapshot")
    can_delete = False


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "submission_key", "user", "exercise", "correct_answers", "total_questions", "submitted_at")
    list_filter = ("exercise__skill", "submitted_at")
    search_fields = ("user__username", "exercise__title", "submission_key")
    readonly_fields = ("submission_key", "started_at", "submitted_at", "exercise_snapshot")
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "user_answer", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("user_answer", "attempt__user__username")
    readonly_fields = ("attempt", "question", "question_snapshot", "user_answer", "is_correct")
