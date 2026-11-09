import json
import logging
import uuid

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import hoc_vien_required
from .forms import SpeakingSubmissionForm
from .models import SpeakingExercise, SpeakingSupport, SpeakingSubmission
from .services.ai_grading import grade_speaking_submission_safely

logger = logging.getLogger(__name__)


@hoc_vien_required
def exercise_list(request):
    """
    UC-SPK-01: Xem danh sách bài luyện Speaking.
    - Chỉ hiển thị các bài có status = PUBLISHED.
    - Xác định trạng thái Đã làm / Chưa làm theo tài khoản học viên hiện tại.
    - Hỗ trợ kết hợp bộ lọc: part, level, topic, status (đã làm / chưa làm).
    - Tối ưu hóa truy vấn bằng Exists() Subquery để tránh N+1.
    """
    query = request.GET.get("q", "").strip()
    sort_option = request.GET.get("sort", "newest").strip()
    part_filter = request.GET.get("part", "").strip()
    level_filter = request.GET.get("level", "").strip()
    topic_filter = request.GET.get("topic", "").strip()
    status_filter = request.GET.get("status", "").strip().lower()

    db_error = None
    exercises = []

    try:
        user_submissions = SpeakingSubmission.objects.filter(
            exercise=OuterRef("pk"),
            user=request.user
        )

        qs = SpeakingExercise.objects.filter(
            status=SpeakingExercise.Status.PUBLISHED
        ).annotate(
            is_done=Exists(user_submissions)
        )

        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(topic__icontains=query) | Q(prompt_text__icontains=query))

        if part_filter in SpeakingExercise.Part.values:
            qs = qs.filter(part=part_filter)

        if level_filter in SpeakingExercise.Level.values:
            qs = qs.filter(level=level_filter)

        if topic_filter:
            qs = qs.filter(
                Q(topic__icontains=topic_filter) | Q(title__icontains=topic_filter)
            )

        if status_filter == "done":
            qs = qs.filter(is_done=True)
        elif status_filter == "not_done":
            qs = qs.filter(is_done=False)

        qs = qs.order_by("created_at" if sort_option == "oldest" else "-created_at")
        exercises = list(qs)

    except DatabaseError as e:
        logger.error("Lỗi cơ sở dữ liệu khi truy vấn danh sách bài Speaking: %s", str(e))
        db_error = "Đã xảy ra lỗi khi truy xuất dữ liệu từ cơ sở dữ liệu. Vui lòng thử lại sau."

    # Lấy danh sách topic độc nhất để hiển thị bộ lọc gợi ý
    available_topics = SpeakingExercise.objects.filter(
        status=SpeakingExercise.Status.PUBLISHED
    ).values_list("topic", flat=True).distinct()

    context = {
        "exercises": exercises,
        "query": query,
        "sort_option": sort_option,
        "db_error": db_error,
        "selected_part": part_filter,
        "selected_level": level_filter,
        "selected_topic": topic_filter,
        "selected_status": status_filter,
        "part_choices": SpeakingExercise.Part.choices,
        "level_choices": SpeakingExercise.Level.choices,
        "available_topics": sorted(set(available_topics)),
        "total_count": len(exercises) if not db_error else 0,
        "active_nav": "speaking",
    }
    return render(request, "speaking/exercise_list.html", context)


@hoc_vien_required
def exercise_detail(request, exercise_id):
    """
    UC-SPK-02: Làm bài Speaking trực tiếp trên website.
    - Chỉ cho phép mở đề ở trạng thái PUBLISHED.
    - Sinh khóa định danh bài nộp duy nhất (submission_key UUID4) cho mỗi lượt làm bài mới trên GET.
    - Truy xuất tài liệu hỗ trợ (SpeakingSupport) qua quan hệ 1-1.
    - Tuyệt đối không tạo SpeakingSubmission hoặc lưu file vào database khi mở trang.
    """
    exercise = get_object_or_404(
        SpeakingExercise,
        pk=exercise_id,
        status=SpeakingExercise.Status.PUBLISHED
    )

    support = getattr(exercise, "support", None)

    submission_count = SpeakingSubmission.objects.filter(
        exercise=exercise,
        user=request.user
    ).count()

    session_submission_key = uuid.uuid4()
    form = SpeakingSubmissionForm(initial={
        "submission_key": session_submission_key,
    })

    context = {
        "exercise": exercise,
        "support": support,
        "submission_count": submission_count,
        "submission_key": session_submission_key,
        "form": form,
        "active_nav": "speaking",
    }
    return render(request, "speaking/exercise_detail.html", context)


@require_POST
@hoc_vien_required
def exercise_submit(request, exercise_id):
    """
    UC-SPK-03: Nộp bài Speaking (Idempotent POST).
    - Xác thực người dùng và quyền HOC_VIEN.
    - Kiểm tra đề Speaking tồn tại và đang PUBLISHED.
    - Validate tệp âm thanh và submission_key qua SpeakingSubmissionForm.
    - Xử lý idempotency:
        + Nếu submission_key đã tồn tại và thuộc về cùng user & exercise: redirect về kết quả đã lưu.
        + Nếu submission_key bị dùng xung đột với user hoặc exercise khác: từ chối HTTP 400.
    - Lưu SpeakingSubmission với status = GRADING trong transaction.atomic().
    - Sau khi transaction commit, kích hoạt gọi Gemini AI (UC-SPK-07).
    - Chuyển hướng Post/Redirect/Get sang màn hình kết quả (UC-SPK-04).
    """
    exercise = get_object_or_404(SpeakingExercise, pk=exercise_id)

    form = SpeakingSubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        support = getattr(exercise, "support", None)
        submission_count = SpeakingSubmission.objects.filter(exercise=exercise, user=request.user).count()

        return render(request, "speaking/exercise_detail.html", {
            "exercise": exercise,
            "support": support,
            "submission_count": submission_count,
            "submission_key": request.POST.get("submission_key", ""),
            "form": form,
            "active_nav": "speaking",
        }, status=400)

    sub_key = form.cleaned_data["submission_key"]
    audio_file = form.cleaned_data["audio_file"]

    # Kiểm tra Idempotency
    existing_sub = SpeakingSubmission.objects.filter(submission_key=sub_key).first()
    if existing_sub:
        if (existing_sub.user_id == request.user.id and existing_sub.exercise_id == exercise.id):
            logger.info("Idempotent replay detected for speaking submission %s", sub_key)
            return redirect("speaking:submission_result", submission_key=existing_sub.submission_key)
        else:
            logger.warning("Conflicting submission_key %s detected", sub_key)
            return HttpResponseBadRequest("Khóa định danh bài nộp (submission_key) bị xung đột hoặc đã được sử dụng.")

    # Đề thi phải đang ở trạng thái PUBLISHED
    if exercise.status != SpeakingExercise.Status.PUBLISHED:
        return HttpResponseBadRequest("Đề bài Speaking này hiện đã bị ẩn hoặc không còn khả dụng.")

    # Tạo snapshot đề thi độc quyền từ server
    exercise_snapshot = {
        "title": exercise.title,
        "part": exercise.part,
        "topic": exercise.topic,
        "prompt_text": exercise.prompt_text,
        "level": exercise.level,
    }

    try:
        with transaction.atomic():
            submission = SpeakingSubmission(
                submission_key=sub_key,
                user=request.user,
                exercise=exercise,
                exercise_snapshot=exercise_snapshot,
                audio_file=audio_file,
                overall_score=None,
                fluency_score=None,
                pronunciation_score=None,
                vocabulary_score=None,
                grammar_score=None,
                feedback=None,
                status=SpeakingSubmission.Status.GRADING,
                graded_at=None,
            )
            submission.full_clean()
            submission.save()

    except IntegrityError:
        # Xử lý tương tranh
        existing_sub = SpeakingSubmission.objects.filter(submission_key=sub_key).first()
        if existing_sub and existing_sub.user_id == request.user.id and existing_sub.exercise_id == exercise.id:
            return redirect("speaking:submission_result", submission_key=existing_sub.submission_key)
        return HttpResponseBadRequest("Lỗi xung đột dữ liệu bài nộp trong cơ sở dữ liệu.")

    except (ValidationError, DatabaseError) as err:
        logger.error("Lỗi khi lưu bài nộp Speaking vào database: %s", str(err))
        support = getattr(exercise, "support", None)
        submission_count = SpeakingSubmission.objects.filter(exercise=exercise, user=request.user).count()
        return render(request, "speaking/exercise_detail.html", {
            "exercise": exercise,
            "support": support,
            "submission_count": submission_count,
            "submission_key": sub_key,
            "form": form,
            "db_error": "Hệ thống gặp sự cố khi lưu tệp âm thanh bài nói. Vui lòng thử lại.",
            "active_nav": "speaking",
        }, status=500)

    # Nộp bài thành công và transaction đã commit:
    # Kích hoạt dịch vụ chấm điểm Speaking bằng Gemini AI (UC-SPK-07)
    try:
        grade_speaking_submission_safely(submission)
    except Exception as ai_dispatch_err:
        logger.error("Lỗi ngoại lệ khi kích hoạt AI grading cho speaking submission #%s: %s", submission.pk, str(ai_dispatch_err))

    return redirect("speaking:submission_result", submission_key=submission.submission_key)


@hoc_vien_required
def submission_result(request, submission_key):
    """
    UC-SPK-04: Xem kết quả bài làm Speaking.
    - Chỉ cho phép chính chủ (submission.user == request.user) xem bài nộp (chống IDOR).
    - Sử dụng exercise_snapshot đã lưu trữ để hiển thị thông tin đề bài tại thời điểm nộp.
    - Hiển thị kết quả chi tiết: Overall Band, 4 tiêu chí, Transcript, audio nghe lại, gợi ý sửa lỗi.
    - Tuyệt đối không gọi Gemini API trên request GET.
    """
    submission = get_object_or_404(
        SpeakingSubmission,
        submission_key=submission_key,
        user=request.user
    )

    snapshot = submission.exercise_snapshot or {}

    assessment = None
    if submission.feedback:
        try:
            parsed = json.loads(submission.feedback)
            if isinstance(parsed, dict):
                assessment = parsed
        except (json.JSONDecodeError, TypeError):
            assessment = None

    # Visual display only. Use the four *stored* IELTS criteria; never recompute grades.
    radar_points = None
    scores = (submission.fluency_score, submission.vocabulary_score,
              submission.grammar_score, submission.pronunciation_score)
    if submission.status == SpeakingSubmission.Status.GRADED and all(v is not None for v in scores):
        # Clockwise vertices: top, right, bottom, left. Center (110,110), radius 75.
        values = [max(0, min(9, float(value))) / 9 for value in scores]
        radar_points = " ".join((
            f"110,{110 - 75 * values[0]:.2f}",
            f"{110 + 75 * values[1]:.2f},110",
            f"110,{110 + 75 * values[2]:.2f}",
            f"{110 - 75 * values[3]:.2f},110",
        ))

    context = {
        "submission": submission,
        "snapshot": snapshot,
        "radar_points": radar_points,
        "assessment": assessment,
        "is_grading": submission.status == SpeakingSubmission.Status.GRADING,
        "is_graded": submission.status == SpeakingSubmission.Status.GRADED,
        "is_failed": submission.status == SpeakingSubmission.Status.FAILED,
        "active_nav": "speaking",
    }
    return render(request, "speaking/submission_result.html", context)


# Chương 6 (Media) + Chương 3 (Permissions): file nộp Speaking không được public.
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
import mimetypes


@login_required
def private_submission_audio(request, relative_path):
    """Phục vụ bản ghi âm đã nộp với kiểm tra quyền sở hữu phía server.

    Route /media/speaking_submissions/... được đăng ký TRƯỚC static MEDIA_URL
    của development server. Với production cần private storage cấu hình riêng.
    """
    name = 'speaking_submissions/' + relative_path
    submission = get_object_or_404(SpeakingSubmission, audio_file=name)
    user = request.user
    from accounts.permissions import is_hoc_vien
    allowed = user.is_active and ((submission.user_id == user.pk and is_hoc_vien(user)) or
        (user.is_staff and (user.is_superuser or user.has_perm('speaking.view_speakingsubmission'))))
    if not allowed:
        raise Http404('Không tìm thấy bản ghi âm.')
    try:
        source = submission.audio_file.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404('Tệp ghi âm không tồn tại.')
    mime = 'audio/webm' if name.lower().endswith('.webm') else (mimetypes.guess_type(name)[0] or 'application/octet-stream')
    response = FileResponse(source, content_type=mime)
    response['Content-Disposition'] = 'inline'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
