import logging

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from writing.models import WritingPrompt, WritingSupport
from speaking.models import SpeakingExercise, SpeakingSupport
from .forms import (
    WritingPromptAdminForm,
    WritingSupportAdminForm,
    SpeakingExerciseAdminForm,
    SpeakingSupportAdminForm,
)
from .permissions import writing_admin_required, speaking_admin_required, teacher_dashboard_required, receptive_teacher_required

logger = logging.getLogger(__name__)


@teacher_dashboard_required
def dashboard_redirect(request):
    """Dashboard giáo viên (chỉ thống kê dữ liệu hiện có, không tạo bảng mới)."""
    from receptive.models import Exercise
    from vocabulary.models import Topic
    from feedback.models import ServiceFeedback
    from django.contrib.auth import get_user_model
    user = request.user
    def allowed(*permissions):
        return user.is_superuser or any(user.has_perm(p) for p in permissions)
    panels = []
    def add(title, number, url, *permissions):
        if allowed(*permissions):
            panels.append({'title': title, 'count': number, 'url': reverse(url)})
    add('Listening', Exercise.objects.filter(skill='LISTENING').count(), 'management:listening_exercise_list', 'receptive.view_exercise', 'listening.view_listeningexercise')
    add('Reading', Exercise.objects.filter(skill='READING').count(), 'management:reading_exercise_list', 'receptive.view_exercise', 'reading.view_readingexercise')
    add('Writing', WritingPrompt.objects.count(), 'management:writing_prompt_list', 'writing.view_writingprompt')
    add('Speaking', SpeakingExercise.objects.count(), 'management:speaking_exercise_list', 'speaking.view_speakingexercise')
    add('Chủ đề Vocabulary', Topic.objects.count(), 'vocabulary:manage_topics', 'vocabulary.view_topic')
    add('Đánh giá / Góp ý', ServiceFeedback.objects.count(), 'feedback:feedback_list', 'feedback.view_servicefeedback')
    add('Tài khoản', get_user_model().objects.count(), 'accounts:manage_users', 'auth.view_user', 'auth.change_user')
    add('Tiến độ học viên', get_user_model().objects.count(), 'management:student_progress_list', 'auth.view_user')
    return render(request, 'management/dashboard.html', {'panels': panels, 'active_nav':'dashboard'})


@writing_admin_required(perm="writing.view_writingprompt")
def writing_prompt_list(request):
    """
    UC-WRI-05: Danh sách quản lý đề Writing (Hình 42).
    Hiển thị danh sách đề, lọc dạng bài, trình độ, trạng thái và tìm kiếm.
    """
    queryset = WritingPrompt.objects.annotate(
        submission_count=Count("submissions")
    ).order_by("-created_at")

    # Bộ lọc tìm kiếm
    search_q = request.GET.get("q", "").strip()
    if search_q:
        queryset = queryset.filter(
            Q(title__icontains=search_q) | Q(prompt_text__icontains=search_q)
        )

    # Lọc Task Type
    task_type = request.GET.get("task_type", "").strip()
    if task_type in [WritingPrompt.TaskType.TASK_1, WritingPrompt.TaskType.TASK_2]:
        queryset = queryset.filter(task_type=task_type)

    # Lọc Level
    level = request.GET.get("level", "").strip()
    if level in [WritingPrompt.Level.BEGINNER, WritingPrompt.Level.INTERMEDIATE, WritingPrompt.Level.ADVANCED]:
        queryset = queryset.filter(level=level)

    # Lọc Status
    status = request.GET.get("status", "").strip()
    if status in [WritingPrompt.Status.PUBLISHED, WritingPrompt.Status.HIDDEN]:
        queryset = queryset.filter(status=status)

    total_prompts = WritingPrompt.objects.count()
    filtered_prompts_count = queryset.count()

    context = {
        "prompts": queryset,
        "total_prompts": total_prompts,
        "filtered_prompts_count": filtered_prompts_count,
        "search_q": search_q,
        "selected_task_type": task_type,
        "selected_level": level,
        "selected_status": status,
        "task_types": WritingPrompt.TaskType.choices,
        "levels": WritingPrompt.Level.choices,
        "statuses": WritingPrompt.Status.choices,
        "active_nav": "writing_tasks",
    }
    return render(request, "management/writing_prompt_list.html", context)


@writing_admin_required(perm="writing.add_writingprompt")
def writing_prompt_create(request):
    """
    UC-WRI-05: Thêm đề Writing mới (Hình 43 layout phong cách 2 cột + Live Preview).
    Trạng thái mặc định là HIDDEN.
    """
    if request.method == "POST":
        form = WritingPromptAdminForm(request.POST)
        if form.is_valid():
            new_prompt = form.save()
            messages.success(
                request,
                f"Đã thêm đề Writing mới thành công: #{new_prompt.id:03d} - {new_prompt.title}."
            )
            return redirect("management:writing_prompt_list")
        else:
            messages.error(request, "Vui lòng kiểm tra và sửa các thông tin chưa hợp lệ.")
    else:
        form = WritingPromptAdminForm()

    context = {
        "form": form,
        "is_create": True,
        "active_nav": "writing_tasks",
    }
    return render(request, "management/writing_prompt_form.html", context)


@writing_admin_required(perm="writing.view_writingprompt")
def writing_prompt_detail(request, pk):
    """
    UC-WRI-05: Xem thông tin chi tiết đề Writing.
    Bao gồm thông tin đề, trạng thái, nội dung hỗ trợ đi kèm và số lượng bài nộp.
    """
    prompt = get_object_or_404(
        WritingPrompt.objects.annotate(submission_count=Count("submissions")),
        pk=pk
    )
    support = getattr(prompt, "support", None)

    context = {
        "prompt": prompt,
        "support": support,
        "active_nav": "writing_tasks",
    }
    return render(request, "management/writing_prompt_detail.html", context)


@writing_admin_required(perm="writing.change_writingprompt")
def writing_prompt_edit(request, pk):
    """
    UC-WRI-05: Chỉnh sửa đề Writing (Hình 43).
    Nếu đề đã có bài nộp (submissions.exists() == True):
    - Khóa các trường cốt lõi (title, task_type, prompt_text, image_file, level).
    - Chỉ cho phép chuyển đổi status giữa PUBLISHED và HIDDEN.
    """
    prompt = get_object_or_404(WritingPrompt, pk=pk)
    has_subs = prompt.submissions.exists()

    if request.method == "POST":
        form = WritingPromptAdminForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Đã cập nhật đề Writing #{prompt.id:03d} - {prompt.title} thành công."
            )
            return redirect("management:writing_prompt_list")
        else:
            messages.error(
                request,
                "Không thể lưu các thay đổi. Vui lòng kiểm tra các lỗi hiển thị bên dưới."
            )
    else:
        form = WritingPromptAdminForm(instance=prompt)

    context = {
        "form": form,
        "prompt": prompt,
        "is_create": False,
        "has_submissions": has_subs,
        "active_nav": "writing_tasks",
    }
    return render(request, "management/writing_prompt_form.html", context)


@require_POST
@writing_admin_required(perm="writing.change_writingprompt")
def writing_prompt_status_toggle(request, pk):
    """
    UC-WRI-05: Chuyển đổi trạng thái hiển thị của đề Writing (Ẩn / Hiện).
    Thực hiện bằng phương thức POST an toàn.
    """
    prompt = get_object_or_404(WritingPrompt, pk=pk)

    if prompt.status == WritingPrompt.Status.PUBLISHED:
        prompt.status = WritingPrompt.Status.HIDDEN
        msg = f"Đã ẩn đề #{prompt.id:03d} - {prompt.title}. Học viên sẽ không nhìn thấy đề này."
    else:
        prompt.status = WritingPrompt.Status.PUBLISHED
        msg = f"Đã kích hoạt hiển thị đề #{prompt.id:03d} - {prompt.title} cho học viên."

    prompt.save(update_fields=["status", "updated_at"])
    messages.success(request, msg)

    # Quay lại trang trước đó (referrer) hoặc danh sách
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("management:writing_prompt_list")


@writing_admin_required(perm="writing.change_writingsupport")
def writing_support_index(request):
    """
    UC-WRI-06: Điểm vào khu vực quản lý tài liệu hỗ trợ Writing.
    Tự động chuyển hướng đến đề đầu tiên trong danh sách (hoặc đề có id nhỏ nhất).
    """
    first_prompt = WritingPrompt.objects.order_by("id").first()
    if first_prompt:
        return redirect("management:writing_support_manage", pk=first_prompt.id)

    context = {
        "prompts": [],
        "active_nav": "support_materials",
    }
    return render(request, "management/writing_support_manage.html", context)


@writing_admin_required(perm="writing.change_writingsupport")
def writing_support_manage(request, pk):
    """
    UC-WRI-06: Chỉnh sửa nội dung hỗ trợ Writing (Hình 44).
    """
    selected_prompt = get_object_or_404(WritingPrompt, pk=pk)

    search_q = request.GET.get("q", "").strip()
    prompts_queryset = WritingPrompt.objects.all().order_by("-created_at")
    if search_q:
        prompts_queryset = prompts_queryset.filter(
            Q(title__icontains=search_q) | Q(prompt_text__icontains=search_q)
        )

    support_instance = WritingSupport.objects.filter(prompt=selected_prompt).first()

    if request.method == "POST":
        form = WritingSupportAdminForm(request.POST, instance=support_instance)
        if form.is_valid():
            support_obj = form.save(commit=False)
            support_obj.prompt = selected_prompt
            support_obj.save()
            messages.success(
                request,
                f"Cập nhật thành công nội dung hỗ trợ cho đề #{selected_prompt.id:03d} - {selected_prompt.title}."
            )
            return redirect("management:writing_support_manage", pk=selected_prompt.id)
        else:
            messages.error(
                request,
                "Không thể lưu nội dung hỗ trợ. Vui lòng kiểm tra lại thông tin."
            )
    else:
        form = WritingSupportAdminForm(instance=support_instance)

    context = {
        "selected_prompt": selected_prompt,
        "prompts": prompts_queryset,
        "search_q": search_q,
        "form": form,
        "support": support_instance,
        "active_nav": "support_materials",
    }
    return render(request, "management/writing_support_manage.html", context)


# ==============================================================================
# QUẢN TRỊ SPEAKING (UC-SPK-05, UC-SPK-06)
# ==============================================================================

@speaking_admin_required(perm="speaking.view_speakingexercise")
def speaking_exercise_list(request):
    """
    UC-SPK-05: Danh sách quản lý bài Speaking.
    Hiển thị danh sách bài, lọc theo Part, Level, Status và tìm kiếm.
    """
    queryset = SpeakingExercise.objects.annotate(
        submission_count=Count("submissions")
    ).order_by("-created_at")

    search_q = request.GET.get("q", "").strip()
    if search_q:
        queryset = queryset.filter(
            Q(title__icontains=search_q) | Q(topic__icontains=search_q) | Q(prompt_text__icontains=search_q)
        )

    part = request.GET.get("part", "").strip()
    if part in SpeakingExercise.Part.values:
        queryset = queryset.filter(part=part)

    level = request.GET.get("level", "").strip()
    if level in SpeakingExercise.Level.values:
        queryset = queryset.filter(level=level)

    status = request.GET.get("status", "").strip()
    if status in SpeakingExercise.Status.values:
        queryset = queryset.filter(status=status)

    total_exercises = SpeakingExercise.objects.count()
    filtered_count = queryset.count()

    context = {
        "exercises": queryset,
        "total_exercises": total_exercises,
        "filtered_count": filtered_count,
        "search_q": search_q,
        "selected_part": part,
        "selected_level": level,
        "selected_status": status,
        "parts": SpeakingExercise.Part.choices,
        "levels": SpeakingExercise.Level.choices,
        "statuses": SpeakingExercise.Status.choices,
        "active_nav": "speaking_tasks",
    }
    return render(request, "management/speaking_exercise_list.html", context)


@speaking_admin_required(perm="speaking.add_speakingexercise")
def speaking_exercise_create(request):
    """
    UC-SPK-05: Thêm bài Speaking mới.
    Mặc định trạng thái là HIDDEN.
    """
    if request.method == "POST":
        form = SpeakingExerciseAdminForm(request.POST)
        if form.is_valid():
            new_exercise = form.save()
            messages.success(
                request,
                f"Đã thêm bài Speaking mới thành công: #{new_exercise.id:03d} - {new_exercise.title}."
            )
            return redirect("management:speaking_exercise_list")
        else:
            messages.error(request, "Vui lòng kiểm tra và sửa các thông tin chưa hợp lệ.")
    else:
        form = SpeakingExerciseAdminForm()

    context = {
        "form": form,
        "is_create": True,
        "active_nav": "speaking_tasks",
    }
    return render(request, "management/speaking_exercise_form.html", context)


@speaking_admin_required(perm="speaking.view_speakingexercise")
def speaking_exercise_detail(request, pk):
    """
    UC-SPK-05: Xem thông tin chi tiết bài Speaking.
    """
    exercise = get_object_or_404(
        SpeakingExercise.objects.annotate(submission_count=Count("submissions")),
        pk=pk
    )
    support = getattr(exercise, "support", None)

    context = {
        "exercise": exercise,
        "support": support,
        "active_nav": "speaking_tasks",
    }
    return render(request, "management/speaking_exercise_detail.html", context)


@speaking_admin_required(perm="speaking.change_speakingexercise")
def speaking_exercise_edit(request, pk):
    """
    UC-SPK-05: Chỉnh sửa bài Speaking.
    Nếu bài đã có bài nộp (submissions.exists() == True):
    - Khóa các trường cốt lõi (title, part, topic, prompt_text, level).
    - Chỉ cho phép chuyển đổi status giữa PUBLISHED và HIDDEN.
    """
    exercise = get_object_or_404(SpeakingExercise, pk=pk)
    has_subs = exercise.submissions.exists()

    if request.method == "POST":
        form = SpeakingExerciseAdminForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Đã cập nhật bài Speaking #{exercise.id:03d} - {exercise.title} thành công."
            )
            return redirect("management:speaking_exercise_list")
        else:
            messages.error(
                request,
                "Không thể lưu các thay đổi. Vui lòng kiểm tra các lỗi hiển thị bên dưới."
            )
    else:
        form = SpeakingExerciseAdminForm(instance=exercise)

    context = {
        "form": form,
        "exercise": exercise,
        "is_create": False,
        "has_submissions": has_subs,
        "active_nav": "speaking_tasks",
    }
    return render(request, "management/speaking_exercise_form.html", context)


@require_POST
@speaking_admin_required(perm="speaking.change_speakingexercise")
def speaking_exercise_status_toggle(request, pk):
    """
    UC-SPK-05: Chuyển đổi trạng thái hiển thị của bài Speaking (Ẩn / Hiện).
    """
    exercise = get_object_or_404(SpeakingExercise, pk=pk)

    if exercise.status == SpeakingExercise.Status.PUBLISHED:
        exercise.status = SpeakingExercise.Status.HIDDEN
        msg = f"Đã ẩn bài Speaking #{exercise.id:03d} - {exercise.title}. Học viên sẽ không nhìn thấy bài này."
    else:
        exercise.status = SpeakingExercise.Status.PUBLISHED
        msg = f"Đã kích hoạt hiển thị bài Speaking #{exercise.id:03d} - {exercise.title} cho học viên."

    exercise.save(update_fields=["status", "updated_at"])
    messages.success(request, msg)

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("management:speaking_exercise_list")


@speaking_admin_required(perm="speaking.change_speakingsupport")
def speaking_support_index(request):
    """
    UC-SPK-06: Điểm vào khu vực quản lý tài liệu hỗ trợ Speaking.
    """
    first_exercise = SpeakingExercise.objects.order_by("id").first()
    if first_exercise:
        return redirect("management:speaking_support_manage", pk=first_exercise.id)

    context = {
        "exercises": [],
        "active_nav": "speaking_support_materials",
    }
    return render(request, "management/speaking_support_manage.html", context)


@speaking_admin_required(perm="speaking.change_speakingsupport")
def speaking_support_manage(request, pk):
    """
    UC-SPK-06: Chỉnh sửa nội dung hỗ trợ Speaking.
    """
    selected_exercise = get_object_or_404(SpeakingExercise, pk=pk)

    search_q = request.GET.get("q", "").strip()
    exercises_queryset = SpeakingExercise.objects.all().order_by("-created_at")
    if search_q:
        exercises_queryset = exercises_queryset.filter(
            Q(title__icontains=search_q) | Q(topic__icontains=search_q) | Q(prompt_text__icontains=search_q)
        )

    support_instance = SpeakingSupport.objects.filter(exercise=selected_exercise).first()

    if request.method == "POST":
        form = SpeakingSupportAdminForm(request.POST, request.FILES, instance=support_instance)
        if form.is_valid():
            support_obj = form.save(commit=False)
            support_obj.exercise = selected_exercise
            support_obj.save()
            messages.success(
                request,
                f"Cập nhật thành công nội dung hỗ trợ cho bài Speaking #{selected_exercise.id:03d} - {selected_exercise.title}."
            )
            return redirect("management:speaking_support_manage", pk=selected_exercise.id)
        else:
            messages.error(
                request,
                "Không thể lưu nội dung hỗ trợ. Vui lòng kiểm tra lại thông tin."
            )
    else:
        form = SpeakingSupportAdminForm(instance=support_instance)

    context = {
        "selected_exercise": selected_exercise,
        "exercises": exercises_queryset,
        "search_q": search_q,
        "form": form,
        "support": support_instance,
        "active_nav": "speaking_support_materials",
    }
    return render(request, "management/speaking_support_manage.html", context)


# Chương 2–4: Django ORM, ModelForm và validation; Chương 6: upload file qua request.FILES.
from receptive.models import Exercise as ReceptiveExercise, Question as ReceptiveQuestion, Option as ReceptiveOption
from .forms import ReceptiveExerciseForm, ReceptiveQuestionForm, ReceptiveOptionForm
from django.core.exceptions import ValidationError


def _receptive_context(skill):
    return {'skill': skill, 'skill_label': skill.title(), 'active_nav':skill.lower()+'_manage'}


def receptive_exercise_list(request, skill):
    qs = ReceptiveExercise.objects.filter(skill=skill).order_by('-updated_at')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(topic__icontains=q))
    context = _receptive_context(skill)
    context.update({'exercises':qs,'query':q})
    return render(request, 'management/receptive_exercise_list.html', context)


def receptive_exercise_form(request, skill, pk=None):
    obj = get_object_or_404(ReceptiveExercise, pk=pk, skill=skill) if pk else None
    form = ReceptiveExerciseForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        exercise = form.save(commit=False)
        exercise.skill = skill
        try:
            exercise.full_clean()
            exercise.save()
            messages.success(request, 'Đã lưu bài luyện '+skill.title()+'.')
            return redirect('management:'+skill.lower()+'_exercise_list')
        except ValidationError as error:
            form.add_error(None, error)
    context = _receptive_context(skill)
    context.update({'form':form,'exercise':obj})
    return render(request, 'management/receptive_exercise_form.html', context)


def receptive_exercise_status(request, skill, pk):
    obj = get_object_or_404(ReceptiveExercise, pk=pk, skill=skill)
    obj.status = ReceptiveExercise.Status.HIDDEN if obj.status == ReceptiveExercise.Status.PUBLISHED else ReceptiveExercise.Status.PUBLISHED
    try:
        obj.full_clean()
        obj.save(update_fields=['status','updated_at'])
        messages.success(request, 'Đã cập nhật trạng thái bài luyện.')
    except ValidationError as error:
        messages.error(request, 'Không thể công bố bài: '+str(error))
    return redirect('management:'+skill.lower()+'_exercise_list')


def receptive_question_list(request, skill, pk):
    exercise = get_object_or_404(ReceptiveExercise, pk=pk, skill=skill)
    context = _receptive_context(skill)
    context.update({'exercise':exercise, 'questions':exercise.questions.prefetch_related('options').all()})
    return render(request, 'management/receptive_question_list.html', context)


def receptive_question_form(request, skill, pk, qpk=None):
    exercise = get_object_or_404(ReceptiveExercise, pk=pk, skill=skill)
    obj = get_object_or_404(ReceptiveQuestion, pk=qpk, exercise=exercise) if qpk else None
    form = ReceptiveQuestionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.exercise = exercise
        try:
            question.full_clean()
            question.save()
            messages.success(request, 'Đã lưu câu hỏi.')
            return redirect('management:'+skill.lower()+'_question_list', pk=exercise.pk)
        except ValidationError as error:
            form.add_error(None, error)
    context = _receptive_context(skill)
    context.update({'exercise':exercise,'question':obj,'form':form})
    return render(request, 'management/receptive_question_form.html', context)


def receptive_option_form(request, skill, pk, qpk, opk=None):
    exercise = get_object_or_404(ReceptiveExercise, pk=pk, skill=skill)
    question = get_object_or_404(ReceptiveQuestion, pk=qpk, exercise=exercise)
    obj = get_object_or_404(ReceptiveOption, pk=opk, question=question) if opk else None
    form = ReceptiveOptionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        option = form.save(commit=False)
        option.question = question
        option.save()
        messages.success(request, 'Đã lưu phương án.')
        return redirect('management:'+skill.lower()+'_question_list', pk=exercise.pk)
    context = _receptive_context(skill)
    context.update({'exercise':exercise,'question':question,'option':obj,'form':form})
    return render(request, 'management/receptive_option_form.html', context)


# Wrappers có permission cụ thể và kiểm tra server-side trên từng thao tác.
@receptive_teacher_required('READING', 'view')
def reading_exercise_list(request): return receptive_exercise_list(request, 'READING')
@receptive_teacher_required('LISTENING', 'view')
def listening_exercise_list(request): return receptive_exercise_list(request, 'LISTENING')
@receptive_teacher_required('READING', 'add')
def reading_exercise_create(request): return receptive_exercise_form(request, 'READING')
@receptive_teacher_required('LISTENING', 'add')
def listening_exercise_create(request): return receptive_exercise_form(request, 'LISTENING')
@receptive_teacher_required('READING', 'change')
def reading_exercise_edit(request, pk): return receptive_exercise_form(request, 'READING', pk)
@receptive_teacher_required('LISTENING', 'change')
def listening_exercise_edit(request, pk): return receptive_exercise_form(request, 'LISTENING', pk)
@require_POST
@receptive_teacher_required('READING', 'change')
def reading_exercise_status(request, pk): return receptive_exercise_status(request, 'READING', pk)
@require_POST
@receptive_teacher_required('LISTENING', 'change')
def listening_exercise_status(request, pk): return receptive_exercise_status(request, 'LISTENING', pk)
@receptive_teacher_required('READING', 'view')
def reading_question_list(request, pk): return receptive_question_list(request, 'READING', pk)
@receptive_teacher_required('LISTENING', 'view')
def listening_question_list(request, pk): return receptive_question_list(request, 'LISTENING', pk)
@receptive_teacher_required('READING', 'change')
def reading_question_create(request, pk): return receptive_question_form(request, 'READING', pk)
@receptive_teacher_required('LISTENING', 'change')
def listening_question_create(request, pk): return receptive_question_form(request, 'LISTENING', pk)
@receptive_teacher_required('READING', 'change')
def reading_question_edit(request, pk, qpk): return receptive_question_form(request, 'READING', pk, qpk)
@receptive_teacher_required('LISTENING', 'change')
def listening_question_edit(request, pk, qpk): return receptive_question_form(request, 'LISTENING', pk, qpk)
@receptive_teacher_required('READING', 'change')
def reading_option_create(request, pk, qpk): return receptive_option_form(request, 'READING', pk, qpk)
@receptive_teacher_required('LISTENING', 'change')
def listening_option_create(request, pk, qpk): return receptive_option_form(request, 'LISTENING', pk, qpk)
@receptive_teacher_required('READING', 'change')
def reading_option_edit(request, pk, qpk, opk): return receptive_option_form(request, 'READING', pk, qpk, opk)
@receptive_teacher_required('LISTENING', 'change')
def listening_option_edit(request, pk, qpk, opk): return receptive_option_form(request, 'LISTENING', pk, qpk, opk)
