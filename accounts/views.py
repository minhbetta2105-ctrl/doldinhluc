from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, RegisterForm
from .permissions import HOC_VIEN_GROUP, is_hoc_vien, is_quan_tri, staff_required

User = get_user_model()


def _forbidden(request, message="Bạn không có quyền truy cập nội dung này."):
    return render(request, "accounts/forbidden.html", {"message": message}, status=403)


def _landing_url(user):
    """Business administrator -> management; superuser -> Django Admin."""
    if is_quan_tri(user):
        if user.is_superuser:
            return reverse("admin:index")
        manage_perms = (
            "writing.view_writingprompt", "speaking.view_speakingexercise",
            "receptive.view_exercise", "vocabulary.view_topic",
            "feedback.view_servicefeedback", "auth.view_user",
        )
        return reverse("management:dashboard") if any(user.has_perm(p) for p in manage_perms) else reverse("home")
    if is_hoc_vien(user):
        return reverse("home")
    return reverse("accounts:waiting")


def _safe_next(request, url):
    if url and url_has_allowed_host_and_scheme(
        url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return url
    return None


def _can_manage(actor, target):
    """Quản trị viên thường không được đụng vào tài khoản superuser."""
    return not (target.is_superuser and not actor.is_superuser)


# --------------------------------------------------------------------------
# UC-ACC-01/02/03: đăng ký, đăng nhập, đăng xuất
# --------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect(_landing_url(request.user))
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(request, "Không thể tạo tài khoản lúc này. Vui lòng thử lại.")
        else:
            messages.success(
                request,
                "Đăng ký thành công. Hãy đăng nhập và chờ quản trị viên cấp quyền Học viên.",
            )
            return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_landing_url(request.user))
    form = LoginForm(request, request.POST or None)
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        return redirect(_safe_next(request, next_url) or _landing_url(form.user))
    return render(request, "accounts/login.html", {"form": form, "next": next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Bạn đã đăng xuất.")
    return redirect("accounts:login")


@login_required
def waiting_view(request):
    """Thông báo chờ cấp quyền Học viên."""
    return render(request, "accounts/waiting.html")


# --------------------------------------------------------------------------
# UC-ACC-04/05: xem và cập nhật hồ sơ
# --------------------------------------------------------------------------
def _get_target(request, user_id):
    """Trả về tài khoản cần xem/sửa, hoặc None nếu không đủ quyền."""
    if user_id is None or user_id == request.user.pk:
        return request.user
    if not is_quan_tri(request.user):
        return None
    target = get_object_or_404(User, pk=user_id)
    return target if _can_manage(request.user, target) else None


@login_required
def profile_view(request, user_id=None):
    target = _get_target(request, user_id)
    if target is None:
        return _forbidden(request, "Bạn không có quyền xem hồ sơ của tài khoản này.")
    context = {
        "target": target,
        "target_is_student": is_hoc_vien(target),
        "is_own": target.pk == request.user.pk,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request, user_id=None):
    target = _get_target(request, user_id)
    if target is None:
        return _forbidden(request, "Bạn không có quyền chỉnh sửa tài khoản này.")
    is_own = target.pk == request.user.pk
    back = redirect("accounts:profile") if is_own else redirect("accounts:user_profile", user_id=target.pk)

    form = ProfileForm(request.POST or None, instance=target)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except DatabaseError:
            messages.error(request, "Không thể lưu thay đổi. Vui lòng thử lại.")
        else:
            messages.success(request, "Cập nhật thành công.")
            return back
    return render(request, "accounts/profile_edit.html", {"form": form, "target": target, "is_own": is_own})


# --------------------------------------------------------------------------
# UC-ACC-06/07: quản trị viên mở/khóa tài khoản, cấp/thu hồi quyền Học viên
# --------------------------------------------------------------------------
@staff_required
def manage_users(request):
    q = request.GET.get("q", "").strip()
    student = request.GET.get("student", "")   # "", "yes", "no"
    status = request.GET.get("status", "")     # "", "active", "locked"

    sort = request.GET.get("sort", "newest")   # newest | oldest | name
    order = {"newest": "-date_joined", "oldest": "date_joined", "name": "first_name"}.get(sort, "-date_joined")

    users = User.objects.all().order_by(order, "pk")
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
            | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "locked":
        users = users.filter(is_active=False)
    if student == "yes":
        users = users.filter(groups__name=HOC_VIEN_GROUP)
    elif student == "no":
        users = users.exclude(groups__name=HOC_VIEN_GROUP)

    page_obj = Paginator(users, 10).get_page(request.GET.get("page"))
    rows = list(page_obj.object_list)
    student_ids = set(
        User.groups.through.objects.filter(
            group__name=HOC_VIEN_GROUP, user_id__in=[u.pk for u in rows]
        ).values_list("user_id", flat=True)
    )
    for u in rows:
        u.is_student = u.pk in student_ids
        # Teacher/staff can review accounts, but only superuser may lock/grant.
        u.can_manage = request.user.is_superuser and _can_manage(request.user, u)
        u.is_me = u.pk == request.user.pk

    stats = {
        "total": User.objects.count(),
        "active": User.objects.filter(is_active=True).count(),
        "locked": User.objects.filter(is_active=False).count(),
        "students": User.objects.filter(groups__name=HOC_VIEN_GROUP).distinct().count(),
    }
    context = {"rows": rows, "page_obj": page_obj, "q": q, "student": student,
               "can_change_access": request.user.is_superuser,
               "status": status, "sort": sort, "stats": stats,
               "result_count": page_obj.paginator.count}
    return render(request, "accounts/manage_users.html", context)


def _back_to_list(request):
    return redirect(_safe_next(request, request.POST.get("next")) or reverse("accounts:manage_users"))


@staff_required
@require_POST
def toggle_active(request, user_id):
    if not request.user.is_superuser:
        return _forbidden(request, "Chỉ quản trị hệ thống mới được khóa tài khoản hoặc cấp/thu hồi quyền Học viên.")
    target = get_object_or_404(User, pk=user_id)
    if not _can_manage(request.user, target):
        return _forbidden(request, "Bạn không có quyền thay đổi tài khoản này.")
    if target.pk == request.user.pk:
        messages.error(request, "Bạn không thể tự khóa tài khoản của chính mình.")
        return _back_to_list(request)
    new_state = not target.is_active
    try:
        target.is_active = new_state
        target.save(update_fields=["is_active"])
    except DatabaseError:
        messages.error(request, "Không thể cập nhật trạng thái. Trạng thái cũ được giữ nguyên.")
    else:
        verb = "Đã mở khóa" if new_state else "Đã khóa"
        messages.success(request, f"{verb} tài khoản {target.get_username()}.")
    return _back_to_list(request)


@staff_required
@require_POST
def set_student(request, user_id):
    if not request.user.is_superuser:
        return _forbidden(request, "Chỉ quản trị hệ thống mới được khóa tài khoản hoặc cấp/thu hồi quyền Học viên.")
    target = get_object_or_404(User, pk=user_id)
    if not _can_manage(request.user, target):
        return _forbidden(request, "Bạn không có quyền thay đổi tài khoản này.")
    action = request.POST.get("action")
    if action not in ("grant", "revoke"):
        messages.error(request, "Thao tác không hợp lệ.")
        return _back_to_list(request)

    try:
        with transaction.atomic():
            group, _ = Group.objects.get_or_create(name=HOC_VIEN_GROUP)
            has_role = target.groups.filter(pk=group.pk).exists()
            if action == "grant":
                if has_role:
                    messages.info(request, "Tài khoản này đã có quyền Học viên.")
                else:
                    target.groups.add(group)
                    messages.success(request, f"Đã cấp quyền Học viên cho {target.get_username()}.")
                    if not target.is_active:
                        messages.info(request, "Tài khoản đang bị khóa. Muốn sử dụng phải mở khóa riêng.")
            else:
                if not has_role:
                    messages.info(request, "Tài khoản này chưa có quyền Học viên.")
                else:
                    target.groups.remove(group)
                    messages.success(request, f"Đã thu hồi quyền Học viên của {target.get_username()}.")
    except DatabaseError:
        messages.error(request, "Không thể lưu thay đổi quyền. Không có thay đổi nào được ghi nhận.")
    return _back_to_list(request)
