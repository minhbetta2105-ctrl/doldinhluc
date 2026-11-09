import logging
from django.db.models import Avg, Count
from django.shortcuts import render

from accounts.permissions import hoc_vien_required
from speaking.models import SpeakingSubmission
from writing.models import WritingSubmission
from receptive.models import Attempt

logger = logging.getLogger(__name__)


def _format_avg(val):
    if val is None:
        return None
    return round(float(val), 1)


@hoc_vien_required
def progress_dashboard(request):
    """
    Theo dõi tiến độ học tập và lịch sử rèn luyện của học viên.
    Tích hợp dữ liệu Speaking, Writing, Reading, Listening mà KHÔNG tạo bảng Progress riêng:
    - Mỗi lần nộp Speaking hợp lệ tính là một lượt luyện (kể cả GRADING và FAILED).
    - Chỉ kết quả GRADED có overall_score hợp lệ mới được tính vào thống kê điểm số.
    """
    user = request.user

    # 1. Thống kê SPEAKING
    all_speaking = SpeakingSubmission.objects.filter(user=user)
    speaking_total_attempts = all_speaking.count()
    graded_speaking = all_speaking.filter(
        status=SpeakingSubmission.Status.GRADED,
        overall_score__isnull=False
    )
    speaking_graded_count = graded_speaking.count()
    speaking_avg_score = graded_speaking.aggregate(Avg("overall_score"))["overall_score__avg"]
    speaking_avg_fluency = graded_speaking.aggregate(Avg("fluency_score"))["fluency_score__avg"]
    speaking_avg_pronunciation = graded_speaking.aggregate(Avg("pronunciation_score"))["pronunciation_score__avg"]
    speaking_avg_vocab = graded_speaking.aggregate(Avg("vocabulary_score"))["vocabulary_score__avg"]
    speaking_avg_grammar = graded_speaking.aggregate(Avg("grammar_score"))["grammar_score__avg"]
    recent_speaking_submissions = all_speaking.select_related("exercise").order_by("-submitted_at")[:8]

    # 2. Thống kê WRITING
    all_writing = WritingSubmission.objects.filter(user=user)
    writing_total_attempts = all_writing.count()
    graded_writing = all_writing.filter(
        status=WritingSubmission.Status.GRADED,
        score__isnull=False
    )
    writing_graded_count = graded_writing.count()
    writing_avg_score = graded_writing.aggregate(Avg("score"))["score__avg"]
    recent_writing_submissions = all_writing.select_related("prompt").order_by("-submitted_at")[:8]

    # 3. Thống kê LISTENING & READING (từ Attempt)
    listening_attempts = Attempt.objects.filter(user=user, exercise__skill="LISTENING")
    listening_count = listening_attempts.count()
    recent_listening = listening_attempts.select_related("exercise").order_by("-submitted_at")[:5]

    reading_attempts = Attempt.objects.filter(user=user, exercise__skill="READING")
    reading_count = reading_attempts.count()
    recent_reading = reading_attempts.select_related("exercise").order_by("-submitted_at")[:5]

    context = {
        "speaking_total_attempts": speaking_total_attempts,
        "speaking_graded_count": speaking_graded_count,
        "speaking_avg_score": _format_avg(speaking_avg_score),
        "speaking_avg_fluency": _format_avg(speaking_avg_fluency),
        "speaking_avg_pronunciation": _format_avg(speaking_avg_pronunciation),
        "speaking_avg_vocab": _format_avg(speaking_avg_vocab),
        "speaking_avg_grammar": _format_avg(speaking_avg_grammar),
        "recent_speaking_submissions": recent_speaking_submissions,

        "writing_total_attempts": writing_total_attempts,
        "writing_graded_count": writing_graded_count,
        "writing_avg_score": _format_avg(writing_avg_score),
        "recent_writing_submissions": recent_writing_submissions,

        "listening_count": listening_count,
        "recent_listening": recent_listening,

        "reading_count": reading_count,
        "recent_reading": recent_reading,

        "active_nav": "progress",
    }
    return render(request, "progress/dashboard.html", context)
