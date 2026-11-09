"""Kiểm tra permission cho các trang quản trị thuộc Q3.

Được đặt tại URL layer, giữ nguyên view nghiệp vụ trong Accounts/Vocabulary.
Những request trực tiếp qua URL (GET/POST) đều phải vượt qua kiểm tra.
"""
from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden


def admin_permissions_required(*permissions, match_any=False):
    """Chỉ staff hoạt động có quyền Django model tương ứng mới được gọi view."""
    if not permissions:
        raise ValueError("Cần ít nhất một permission")

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not user.is_active or not user.is_staff:
                return HttpResponseForbidden("Bạn không có quyền quản trị chức năng này.")
            checks = [user.has_perm(perm) for perm in permissions]
            if (any(checks) if match_any else all(checks)) is False:
                return HttpResponseForbidden("Tài khoản thiếu quyền quản trị tương ứng.")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
