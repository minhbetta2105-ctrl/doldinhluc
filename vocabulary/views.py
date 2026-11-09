import uuid

from django.contrib import messages
from django.db import DatabaseError, IntegrityError, transaction
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from accounts.permissions import hoc_vien_required, staff_required

from . import services
from .forms import TopicForm, WordForm
from .models import Answer, Attempt, ExerciseType, Level, QuestionType, Status, Topic, Word

MAX_RUNS_IN_SESSION = 5
TYPE_SHORT = {"MCQ": "Trắc nghiệm", "MATCH": "Nối từ", "DRAG": "Kéo & Thả"}


# ===========================================================================
# HỌC VIÊN
# ===========================================================================
@hoc_vien_required
def topic_list(request):
    """UC-VOC-01: danh sách chủ đề (tên, trình độ, số từ), tìm kiếm + lọc trình độ."""
    q = request.GET.get("q", "").strip()
    level = request.GET.get("level", "")

    topics = Topic.objects.filter(status=Status.PUBLISHED).annotate(
        word_count=Count("words", filter=Q(words__status=Status.PUBLISHED))
    )
    if q:
        topics = topics.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if level in Level.values:
        topics = topics.filter(level=level)

    return render(request, "vocabulary/topic_list.html", {
        "topics": topics.order_by("name"), "q": q, "level": level, "levels": Level.choices,
        "available_topics": list(Topic.objects.filter(status=Status.PUBLISHED)
                                  .order_by("name").values_list("name", flat=True)),
    })


@hoc_vien_required
def topic_detail(request, pk):
    """UC-VOC-02: xem từ theo chủ đề (danh sách / flashcard). Không tính là lượt làm bài."""
    topic = Topic.objects.filter(pk=pk, status=Status.PUBLISHED).first()
    if topic is None:
        messages.error(request, "Chủ đề không còn khả dụng.")
        return redirect("vocabulary:topic_list")

    words = list(topic.words.filter(status=Status.PUBLISHED).order_by("word"))
    mode = "flashcard" if request.GET.get("mode") == "flashcard" else "list"
    available = services.available_types(words)
    types = [
        {"value": value, "label": label, "ok": available[value]}
        for value, label in ExerciseType.choices
    ]
    start_type = next((t["value"] for t in types if t["ok"]), "")  # dạng bài đầu tiên đủ dữ liệu
    return render(request, "vocabulary/topic_detail.html", {
        "topic": topic, "words": words, "mode": mode,
        "start_type": start_type, "can_practice": bool(start_type),
    })


# --- phiên làm bài lưu trong session -------------------------------------
def _get_runs(request):
    return request.session.get("vocab_runs", {})


def _save_run(request, run):
    runs = _get_runs(request)
    runs[run["key"]] = run
    if len(runs) > MAX_RUNS_IN_SESSION:
        for key in sorted(runs, key=lambda k: runs[k]["started_at"])[: len(runs) - MAX_RUNS_IN_SESSION]:
            runs.pop(key, None)
    request.session["vocab_runs"] = runs  # gán lại để Django ghi session


def _drop_run(request, key):
    runs = _get_runs(request)
    if runs.pop(key, None) is not None:
        request.session["vocab_runs"] = runs


@hoc_vien_required
@require_POST
def start_practice(request, pk):
    """UC-VOC-03: tạo bộ câu hỏi cố định cho lượt luyện rồi chuyển sang trang làm bài."""
    topic = Topic.objects.filter(pk=pk, status=Status.PUBLISHED).first()
    if topic is None:
        messages.error(request, "Chủ đề không còn khả dụng.")
        return redirect("vocabulary:topic_list")
    exercise_type = request.POST.get("exercise_type", "")
    try:
        run = services.build_run(topic, exercise_type, request.user.pk)
    except services.NotEnoughData:
        messages.error(request, "Chưa đủ dữ liệu để bắt đầu luyện tập.")
        return redirect("vocabulary:topic_detail", pk=topic.pk)
    _save_run(request, run)
    return redirect("vocabulary:practice", key=run["key"])


def _load_run(request, key):
    run = _get_runs(request).get(str(key))
    if run is None or run.get("user_id") != request.user.pk:
        return None
    return run


@hoc_vien_required
def practice(request, key):
    run = _load_run(request, key)
    if run is None:
        existing = Attempt.objects.filter(submission_key=key, user=request.user).first()
        if existing:
            return redirect("vocabulary:result", pk=existing.pk)
        messages.error(request, "Phiên luyện tập không còn hợp lệ. Hãy bắt đầu lại.")
        return redirect("vocabulary:topic_list")
    if not Topic.objects.filter(pk=run["topic_id"], status=Status.PUBLISHED).exists():
        _drop_run(request, str(key))
        messages.error(request, "Chủ đề không còn khả dụng.")
        return redirect("vocabulary:topic_list")

    topic = Topic.objects.get(pk=run["topic_id"])
    available = services.available_types(list(topic.words.filter(status=Status.PUBLISHED)))
    types = [{"value": v, "ok": available[v]} for v, _ in ExerciseType.choices]
    return render(request, "vocabulary/practice.html", {
        "run": run, "topic": topic, "questions": services.public_questions(run),
        "bank": run["bank"], "types": types,
        "type_label": TYPE_SHORT[run["exercise_type"]],
    })


@hoc_vien_required
@require_POST
def submit_practice(request, key):
    """UC-VOC-04: chấm bài và lưu lượt luyện (mỗi lượt lưu riêng, chống nộp trùng)."""
    key = str(key)

    existing = Attempt.objects.filter(submission_key=key, user=request.user).first()
    if existing:  # E4: gửi trùng -> không tạo thêm lượt
        return redirect("vocabulary:result", pk=existing.pk)

    run = _load_run(request, key)
    if run is None:
        messages.error(request, "Phiên luyện tập không còn hợp lệ. Hãy bắt đầu lại.")
        return redirect("vocabulary:topic_list")

    topic = Topic.objects.filter(pk=run["topic_id"], status=Status.PUBLISHED).first()
    if topic is None:
        _drop_run(request, key)
        messages.error(request, "Chủ đề không còn khả dụng nên không thể nộp bài.")
        return redirect("vocabulary:topic_list")

    try:
        results = services.grade(run, request.POST)
    except services.InvalidSubmission:
        messages.error(request, "Dữ liệu nộp bài không hợp lệ.")
        return redirect("vocabulary:practice", key=key)

    try:
        with transaction.atomic():
            attempt = Attempt.objects.create(
                submission_key=uuid.UUID(key),
                user=request.user,
                topic=topic,
                exercise_type=run["exercise_type"],
                topic_snapshot=run["topic_snapshot"],
                total_questions=len(results),
                correct_answers=sum(1 for r in results if r["is_correct"]),
                started_at=parse_datetime(run["started_at"]),
                submitted_at=timezone.now(),
            )
            Answer.objects.bulk_create([
                Answer(
                    attempt=attempt,
                    word_id=r["question"]["word_id"],
                    question_type=_question_type(run, r["question"]),
                    question_snapshot=r["question"],
                    user_answer=r["user_answer"],
                    is_correct=r["is_correct"],
                    order_no=r["question"]["no"],
                )
                for r in results
            ])
    except IntegrityError:
        existing = Attempt.objects.filter(submission_key=key, user=request.user).first()
        if existing:
            return redirect("vocabulary:result", pk=existing.pk)
        messages.error(request, "Không thể lưu kết quả. Vui lòng nộp lại.")
        return redirect("vocabulary:practice", key=key)
    except DatabaseError:
        messages.error(request, "Không thể lưu kết quả. Vui lòng nộp lại.")
        return redirect("vocabulary:practice", key=key)

    _drop_run(request, key)
    messages.success(request, "Nộp bài thành công.")
    return redirect("vocabulary:result", pk=attempt.pk)


def _question_type(run, question):
    if run["exercise_type"] == "MCQ":
        return question["type"]  # MCQ_MEANING hoặc MCQ_WORD
    return QuestionType.MATCH.value if run["exercise_type"] == "MATCH" else QuestionType.DRAG.value


@hoc_vien_required
def result(request, pk):
    """UC-VOC-05: xem kết quả đúng lượt luyện đã nộp (chỉ của chính mình)."""
    attempt = Attempt.objects.select_related("topic").filter(pk=pk).first()
    if attempt is None:
        return render(request, "accounts/forbidden.html",
                      {"message": "Không tìm thấy kết quả bài luyện."}, status=404)
    if attempt.user_id != request.user.pk:
        return render(request, "accounts/forbidden.html",
                      {"message": "Lượt luyện này không thuộc tài khoản của bạn."}, status=403)
    return render(request, "vocabulary/result.html", {
        "attempt": attempt,
        "answers": attempt.answers.all(),
        "type_label": TYPE_SHORT.get(attempt.exercise_type, attempt.exercise_type),
        "wrong": attempt.total_questions - attempt.correct_answers,
    })


# ===========================================================================
# QUẢN TRỊ VIÊN: chủ đề (UC-VOC-06) và nội dung từ (UC-VOC-07)
# ===========================================================================
@staff_required
def manage_topics(request):
    q = request.GET.get("q", "").strip()
    qs = Topic.objects.annotate(
        word_total=Count("words", distinct=True),
        has_history=Exists(Attempt.objects.filter(topic=OuterRef("pk"))),
    )
    if q:
        qs = qs.filter(name__icontains=q)
    qs = qs.order_by("name")
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    all_topics = Topic.objects.all()
    return render(request, "vocabulary/manage_topics.html", {
        "page_obj": page_obj, "rows": list(page_obj.object_list), "q": q,
        "total": all_topics.count(),
        "shown": all_topics.filter(status=Status.PUBLISHED).count(),
        "hidden": all_topics.filter(status=Status.HIDDEN).count(),
    })


@staff_required
def topic_create(request):
    form = TopicForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(request, "Lưu thất bại. Không có thay đổi nào được ghi nhận.")
        else:
            messages.success(request, "Đã thêm chủ đề.")
            return redirect("vocabulary:manage_topics")
    return render(request, "vocabulary/manage_form.html", {
        "form": form, "title": "Thêm chủ đề từ vựng", "cancel_url": "vocabulary:manage_topics"})


@staff_required
def topic_edit(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    form = TopicForm(request.POST or None, instance=topic)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(request, "Cập nhật thất bại. Không có thay đổi nào được ghi nhận.")
        else:
            messages.success(request, "Đã cập nhật chủ đề.")
            return redirect("vocabulary:manage_topics")
    return render(request, "vocabulary/manage_form.html", {
        "form": form, "title": f"Sửa chủ đề: {topic.name}", "cancel_url": "vocabulary:manage_topics"})


@staff_required
@require_POST
def topic_set_status(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    new_status = Status.PUBLISHED if request.POST.get("status") == Status.PUBLISHED else Status.HIDDEN
    topic.status = new_status
    topic.save(update_fields=["status", "updated_at"])
    messages.success(request, "Đã hiện chủ đề." if new_status == Status.PUBLISHED else "Đã ẩn chủ đề.")
    return redirect("vocabulary:manage_topics")


@staff_required
@require_POST
def topic_delete(request, pk):
    """Chủ đề đã có lịch sử luyện thì không xóa vật lý, chuyển sang Ẩn."""
    topic = get_object_or_404(Topic, pk=pk)
    if Attempt.objects.filter(topic=topic).exists():
        topic.status = Status.HIDDEN
        topic.save(update_fields=["status", "updated_at"])
        messages.info(request, "Chủ đề đã có lịch sử luyện tập nên không xóa được. Hệ thống đã chuyển sang Ẩn.")
    else:
        try:
            topic.delete()
        except DatabaseError:
            messages.error(request, "Không thể xóa chủ đề.")
        else:
            messages.success(request, "Đã xóa chủ đề.")
    return redirect("vocabulary:manage_topics")


@staff_required
def manage_words(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    qs = topic.words.annotate(
        has_history=Exists(Answer.objects.filter(word=OuterRef("pk")))
    ).order_by("word")
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "vocabulary/manage_words.html", {
        "topic": topic, "topics": Topic.objects.all(),
        "page_obj": page_obj, "rows": list(page_obj.object_list),
        "total": topic.words.count(),
        "shown": topic.words.filter(status=Status.PUBLISHED).count(),
        "hidden": topic.words.filter(status=Status.HIDDEN).count(),
    })


@staff_required
def word_create(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    form = WordForm(request.POST or None, topic=topic)
    if request.method == "POST" and form.is_valid():
        word = form.save(commit=False)
        word.topic = topic
        try:
            word.save()
        except DatabaseError:
            messages.error(request, "Lưu thất bại. Không có thay đổi nào được ghi nhận.")
        else:
            messages.success(request, "Đã thêm từ vựng.")
            return redirect("vocabulary:manage_words", topic_id=topic.pk)
    return render(request, "vocabulary/manage_form.html", {
        "form": form, "title": f"Thêm từ vào chủ đề: {topic.name}",
        "cancel_url": "vocabulary:manage_words", "cancel_arg": topic.pk})


@staff_required
def word_edit(request, pk):
    word = get_object_or_404(Word.objects.select_related("topic"), pk=pk)
    form = WordForm(request.POST or None, instance=word, topic=word.topic)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(request, "Cập nhật thất bại. Không có thay đổi nào được ghi nhận.")
        else:
            messages.success(request, "Đã cập nhật từ vựng. Kết quả các lượt luyện trước được giữ nguyên.")
            return redirect("vocabulary:manage_words", topic_id=word.topic_id)
    return render(request, "vocabulary/manage_form.html", {
        "form": form, "title": f"Sửa từ: {word.word}",
        "cancel_url": "vocabulary:manage_words", "cancel_arg": word.topic_id})


@staff_required
@require_POST
def word_set_status(request, pk):
    word = get_object_or_404(Word, pk=pk)
    new_status = Status.PUBLISHED if request.POST.get("status") == Status.PUBLISHED else Status.HIDDEN
    word.status = new_status
    word.save(update_fields=["status", "updated_at"])
    messages.success(request, "Đã hiện từ vựng." if new_status == Status.PUBLISHED else "Đã ẩn từ vựng.")
    return redirect("vocabulary:manage_words", topic_id=word.topic_id)


@staff_required
@require_POST
def word_delete(request, pk):
    """Từ đã phát sinh lịch sử thì ẩn để giữ liên kết, chưa có thì xóa hẳn."""
    word = get_object_or_404(Word, pk=pk)
    topic_id = word.topic_id
    if Answer.objects.filter(word=word).exists():
        word.status = Status.HIDDEN
        word.save(update_fields=["status", "updated_at"])
        messages.info(request, "Từ này đã có lịch sử luyện tập nên không xóa được. Hệ thống đã chuyển sang Ẩn.")
    else:
        try:
            word.delete()
        except DatabaseError:
            messages.error(request, "Không thể xóa từ vựng.")
        else:
            messages.success(request, "Đã xóa từ vựng.")
    return redirect("vocabulary:manage_words", topic_id=topic_id)
