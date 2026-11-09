"""Kiểm tra quyền dùng chung cho cả dự án.

Các module khác (reading, listening, writing, speaking, progress, feedback)
có thể dùng lại:

    from accounts.permissions import hoc_vien_required

    @hoc_vien_required
    def my_view(request): ...
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

HOC_VIEN_GROUP = "HOC_VIEN"


def is_hoc_vien(user):
    """Học viên = đã đăng nhập, is_active=True và thuộc Group HOC_VIEN."""
    return bool(
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name=HOC_VIEN_GROUP).exists()
    )


def is_quan_tri(user):
    """Quản trị viên = đã đăng nhập, is_active=True và is_staff=True."""
    return bool(user.is_authenticated and user.is_active and user.is_staff)


def hoc_vien_required(view_func):
    """Chưa đăng nhập -> trang đăng nhập; chưa có quyền Học viên -> thông báo chờ cấp quyền."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_hoc_vien(request.user):
            return render(request, "accounts/waiting.html", status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped


def staff_required(view_func):
    """Chỉ quản trị viên (is_staff) mới được vào."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_quan_tri(request.user):
            return render(
                request,
                "accounts/forbidden.html",
                {"message": "Bạn không có quyền quản trị để thực hiện thao tác này."},
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
