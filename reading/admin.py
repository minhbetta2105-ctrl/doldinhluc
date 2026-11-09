from django.contrib import admin
from reading.models import ReadingExercise
from receptive.models import Question, Option


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


@admin.register(ReadingExercise)
class ReadingExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "level", "topic", "status", "created_at", "updated_at")
    list_filter = ("level", "status", "topic")
    search_fields = ("title", "topic", "description", "passage")
    fields = ("title", "description", "topic", "level", "passage", "status")
    inlines = [QuestionInline]

    def save_model(self, request, obj, form, change):
        obj.skill = ReadingExercise.Skill.READING
        super().save_model(request, obj, form, change)
