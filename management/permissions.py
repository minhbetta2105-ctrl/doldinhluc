import logging
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from writing.permissions import get_writing_login_url

logger = logging.getLogger(__name__)


def check_writing_admin_access(user, required_perm: str = None) -> bool:
    """
    Kiểm tra quyền truy cập khu vực quản trị Writing (UC-WRI-05, UC-WRI-06):
    1. Phải đăng nhập (is_authenticated == True).
    2. Tài khoản phải kích hoạt (is_active == True).
    3. Không dành cho học viên thông thường (user không có quyền staff/superuser bị từ chối).
    4. Superuser luôn có toàn quyền theo cơ chế Django.
    5. Staff user phải có quyền quản lý tương ứng (hoặc permission cụ thể nếu yêu cầu).
    6. Tuyệt đối không dùng DEBUG=True để bypass quyền quản trị.
    """
    if not user or not user.is_authenticated:
        return False

    if not user.is_active:
        return False

    # Superuser có toàn quyền
    if user.is_superuser:
        return True

    # Phải là staff user
    if not user.is_staff:
        return False

    # Nếu yêu cầu permission cụ thể (ví dụ: 'writing.change_writingprompt')
    if required_perm:
        return user.has_perm(required_perm)

    # Mặc định staff cần có ít nhất quyền xem hoặc quản lý Writing
    return (
        user.has_perm("writing.view_writingprompt")
        or user.has_perm("writing.change_writingprompt")
        or user.has_perm("writing.add_writingprompt")
    )


def writing_admin_required(perm: str = None):
    """
    Decorator bảo vệ các view quản trị Writing ở phía Server cho mọi request (GET & POST).
    - Chưa đăng nhập: chuyển hướng an toàn đến trang login với tham số `next`.
    - Đã đăng nhập nhưng inactive hoặc không đủ quyền quản trị: trả về HTTP 403 Forbidden.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url=get_writing_login_url()
                )

            if not user.is_active:
                return HttpResponseForbidden("Tài khoản của bạn đã bị khóa hoặc ngừng kích hoạt.")

            # Kiểm tra quyền quản trị
            if not check_writing_admin_access(user, required_perm=perm):
                logger.warning(
                    f"Người dùng #{user.id} ({user.username}) bị từ chối truy cập quản trị Writing: thiếu quyền {perm}"
                )
                return HttpResponseForbidden(
                    "Bạn không có quyền truy cập hoặc thực hiện thao tác trong khu vực quản trị Writing."
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def check_speaking_admin_access(user, required_perm: str = None) -> bool:
    """Kiểm tra quyền truy cập quản trị Speaking (UC-SPK-05, UC-SPK-06)."""
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if not user.is_staff:
        return False
    if required_perm:
        return user.has_perm(required_perm)
    return True


def speaking_admin_required(perm: str = None):
    """Decorator bảo vệ các view quản trị Speaking (UC-SPK-05, UC-SPK-06)."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url=get_writing_login_url()
                )
            if not user.is_active:
                return HttpResponseForbidden("Tài khoản của bạn đã bị khóa hoặc ngừng kích hoạt.")
            if not check_speaking_admin_access(user, required_perm=perm):
                logger.warning(
                    f"Người dùng #{user.id} ({user.username}) bị từ chối truy cập quản trị Speaking: thiếu quyền {perm}"
                )
                return HttpResponseForbidden(
                    "Bạn không có quyền truy cập hoặc thực hiện thao tác trong khu vực quản trị Speaking."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Chương 3 – Django Groups/Permissions. Không tạo nhóm quyền mới.
def can_enter_teacher_dashboard(user):
    if not user or not user.is_authenticated or not user.is_active or not user.is_staff:
        return False
    if user.is_superuser:
        return True
    return any(user.has_perm(name) for name in (
        'auth.view_user', 'auth.change_user',
        'writing.view_writingprompt', 'speaking.view_speakingexercise',
        'vocabulary.view_topic', 'vocabulary.view_word',
        'receptive.view_exercise', 'reading.view_readingexercise',
        'listening.view_listeningexercise', 'feedback.view_servicefeedback',
        'writing.view_writingsupport', 'speaking.view_speakingsupport',
    ))


def teacher_dashboard_required(view):
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=get_writing_login_url())
        if not can_enter_teacher_dashboard(request.user):
            raise PermissionDenied('Tài khoản không có quyền truy cập quản lý.')
        return view(request, *args, **kwargs)
    return guarded


def receptive_teacher_required(skill, action='view'):
    # Quản lý đề Reading/Listening trên bảng dùng chung receptive.Exercise.
    perm = f'receptive.{action}_exercise'
    proxy_perm = f'{skill.lower()}.{action}_{skill.lower()}exercise'
    def decorator(view):
        @wraps(view)
        def guarded(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=get_writing_login_url())
            if not user.is_active or not user.is_staff or not (user.is_superuser or user.has_perm(perm) or user.has_perm(proxy_perm)):
                raise PermissionDenied('Tài khoản chưa được cấp quyền quản lý nội dung này.')
            return view(request, *args, **kwargs)
        return guarded
    return decorator
