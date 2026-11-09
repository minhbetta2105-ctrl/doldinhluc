from django.contrib import admin
from .models import SpeakingExercise, SpeakingSupport, SpeakingSubmission


class SpeakingSupportInline(admin.StackedInline):
    model = SpeakingSupport
    can_delete = False
    extra = 0


@admin.register(SpeakingExercise)
class SpeakingExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "part", "topic", "level", "status", "created_at")
    list_filter = ("part", "level", "status")
    search_fields = ("title", "topic", "prompt_text")
    inlines = [SpeakingSupportInline]

    def get_readonly_fields(self, request, obj=None):
        # Match Teacher Dashboard: keep old submissions/snapshots meaningful.
        if obj and obj.submissions.exists():
            return ("title", "part", "topic", "prompt_text", "level", "created_at", "updated_at")
        return ("created_at", "updated_at")


@admin.register(SpeakingSubmission)
class SpeakingSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "submission_key", "user", "exercise", "overall_score", "status", "submitted_at")
    list_filter = ("status", "exercise__part", "submitted_at")
    search_fields = ("submission_key", "user__username", "exercise__title")
    readonly_fields = ("submission_key", "submitted_at", "graded_at", "user", "exercise",
                       "exercise_snapshot", "audio_file", "overall_score", "fluency_score",
                       "pronunciation_score", "vocabulary_score", "grammar_score", "feedback", "status")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
