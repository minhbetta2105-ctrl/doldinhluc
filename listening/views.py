import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from core.decorators import hoc_vien_required
from listening.models import ListeningExercise
from receptive.models import Exercise, Attempt, Question
from receptive.services.submission import submit_receptive_exercise


@hoc_vien_required
def exercise_list(request):
    """UC-LIS-01: Xem danh sách bài luyện Listening.
    Hỗ trợ A1 (Tìm kiếm), A2 (Lọc theo level), A3 (Sắp xếp).
    """
    queryset = ListeningExercise.objects.filter(status=Exercise.Status.PUBLISHED)

    # A1 - Tìm kiếm từ khóa
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(topic__icontains=query) | Q(description__icontains=query))

    # Selectable OR typable topic (from actual published data, not a fixed list).
    topic_filter = request.GET.get("topic", "").strip()
    if topic_filter:
        queryset = queryset.filter(topic__icontains=topic_filter)

    question_type = request.GET.get("question_type", "").strip()
    if question_type in Question.Type.values:
        queryset = queryset.filter(questions__question_type=question_type,
                                   questions__status=Question.Status.PUBLISHED).distinct()

    # A2 - Lọc theo trình độ
    level_filter = request.GET.get("level", "").strip()
    if level_filter in [Exercise.Level.BEGINNER, Exercise.Level.INTERMEDIATE, Exercise.Level.ADVANCED]:
        queryset = queryset.filter(level=level_filter)

    # A3 - Sắp xếp
    sort_option = request.GET.get("sort", "newest").strip()
    if sort_option == "oldest":
        queryset = queryset.order_by("created_at")
    else:
        queryset = queryset.order_by("-created_at")

    # Phân trang: 6 bài mỗi trang
    paginator = Paginator(queryset, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Lấy thông tin lượt luyện gần nhất của học viên cho các bài hiển thị
    exercise_ids = [ex.id for ex in page_obj]
    user_attempts = (
        Attempt.objects.filter(user=request.user, exercise_id__in=exercise_ids)
        .order_by("exercise_id", "-submitted_at")
    )
    attempt_map = {}
    for att in user_attempts:
        if att.exercise_id not in attempt_map:
            attempt_map[att.exercise_id] = att

    # Bổ sung dữ liệu hiển thị cho từng bài
    exercises_data = []
    for ex in page_obj:
        q_count = ex.questions.filter(status=Question.Status.PUBLISHED).count()
        types = list(ex.questions.filter(status=Question.Status.PUBLISHED).values_list("question_type", flat=True).distinct())
        type_names = {
            "MCQ": "Multiple Choice",
            "SHORT_TEXT": "Điền đáp án",
            "MATCHING": "Nối thông tin",
            "TFNG": "True/False/Not Given",
            "YNNG": "Yes/No/Not Given",
        }
        types_display = ", ".join([type_names.get(t, t) for t in types[:2]])

        att = attempt_map.get(ex.id)
        exercises_data.append({
            "exercise": ex,
            "question_count": q_count,
            "types_display": types_display,
            "latest_attempt": att,
        })

    context = {
        "active_nav": "listening",
        "page_obj": page_obj,
        "exercises_data": exercises_data,
        "query": query,
        "topic_filter": topic_filter,
        "question_type": question_type,
        "available_topics": list(ListeningExercise.objects.filter(status=Exercise.Status.PUBLISHED)
                                  .exclude(topic="").order_by("topic").values_list("topic", flat=True).distinct()),
        "question_type_choices": Question.Type.choices,
        "level_choices": Exercise.Level.choices,
        "level_filter": level_filter,
        "sort_option": sort_option,
        "total_count": paginator.count,
    }
    return render(request, "listening/exercise_list.html", context)


@hoc_vien_required
def exercise_detail(request, pk):
    """UC-LIS-02: Làm bài Listening.
    Hiển thị Audio Player và các câu hỏi, chuẩn bị submission_key chống nộp lặp.
    """
    exercise = get_object_or_404(ListeningExercise, pk=pk, status=Exercise.Status.PUBLISHED)
    questions = exercise.questions.filter(status=Question.Status.PUBLISHED).prefetch_related("options").order_by("order_no", "id")

    # Sinh submission_key (UUID) và thời điểm bắt đầu
    submission_key = uuid.uuid4()
    started_at = timezone.now().isoformat()

    context = {
        "active_nav": "listening",
        "exercise": exercise,
        "questions": questions,
        "submission_key": submission_key,
        "started_at": started_at,
        "total_questions": questions.count(),
    }
    return render(request, "listening/exercise_detail.html", context)


@hoc_vien_required
def exercise_submit(request, pk):
    """UC-LIS-03 & UC-LIS-04: Nộp bài Listening & Tự động chấm điểm.
    Nhận dữ liệu bài làm và lưu kết quả trong atomic transaction.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Phương thức không được hỗ trợ.")

    exercise = get_object_or_404(ListeningExercise, pk=pk, status=Exercise.Status.PUBLISHED)

    # Đọc dữ liệu từ form data hoặc JSON
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Dữ liệu JSON không hợp lệ"}, status=400)
        answers_dict = data.get("answers", {})
        submission_key = data.get("submission_key")
        started_at_str = data.get("started_at")
    else:
        # Form thông thường
        answers_dict = {}
        for key, val in request.POST.items():
            if key.startswith("answer_"):
                q_id = key.replace("answer_", "")
                answers_dict[q_id] = val
        submission_key = request.POST.get("submission_key")
        started_at_str = request.POST.get("started_at")

    started_at = None
    if started_at_str:
        try:
            started_at = timezone.datetime.fromisoformat(started_at_str)
        except Exception:
            started_at = timezone.now()

    try:
        attempt, created = submit_receptive_exercise(
            user=request.user,
            exercise=exercise,
            answers_dict=answers_dict,
            started_at=started_at,
            submission_key=submission_key,
        )
    except Exception as e:
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"error": str(e)}, status=400)
        return render(request, "listening/error.html", {"error_message": str(e)})

    result_url = reverse("listening:attempt_result", kwargs={"submission_key": attempt.submission_key})

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({"success": True, "result_url": result_url, "created": created})

    return redirect(result_url)


@hoc_vien_required
def attempt_result(request, submission_key):
    """UC-LIS-05: Xem kết quả bài làm Listening.
    Truy xuất từ Attempt và Answer snapshot của chính học viên.
    """
    attempt = get_object_or_404(Attempt, submission_key=submission_key)

    # Phân quyền: Chỉ học viên sở hữu lượt luyện hoặc staff mới được xem
    if attempt.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Bạn không có quyền xem kết quả của lượt luyện này.")

    answers = attempt.answers.select_related("question").order_by("question__order_no", "id")

    correct_count = attempt.correct_answers
    total_count = attempt.total_questions
    wrong_count = 0
    unanswered_count = 0

    answers_display = []
    for ans in answers:
        q_snap = ans.question_snapshot or {}
        correct_list = q_snap.get("correct_answers", [])
        correct_display = ", ".join([str(c) for c in correct_list]) if correct_list else ""
        user_ans = ans.user_answer.strip() if ans.user_answer else ""

        if not user_ans:
            status = "unanswered"
            unanswered_count += 1
        elif ans.is_correct:
            status = "correct"
        else:
            status = "wrong"
            wrong_count += 1

        answers_display.append({
            "order_no": q_snap.get("order_no", ans.question.order_no if ans.question else 1),
            "question_text": q_snap.get("question_text", ans.question.question_text if ans.question else ""),
            "user_answer": user_ans if user_ans else "Chưa trả lời",
            "correct_answer": correct_display,
            "explanation": q_snap.get("explanation", ""),
            "status": status,
        })

    # Tính tỷ lệ phần trăm đúng
    percentage = round((correct_count / total_count * 100), 1) if total_count > 0 else 0

    context = {
        "active_nav": "listening",
        "attempt": attempt,
        "exercise": attempt.exercise,
        "correct_count": correct_count,
        "total_count": total_count,
        "wrong_count": wrong_count,
        "unanswered_count": unanswered_count,
        "percentage": percentage,
        "answers_display": answers_display,
    }
    return render(request, "listening/attempt_result.html", context)
