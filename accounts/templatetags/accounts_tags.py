from django import template

from accounts.permissions import HOC_VIEN_GROUP
from accounts.permissions import is_hoc_vien as _is_hoc_vien
from accounts.permissions import is_quan_tri as _is_quan_tri

register = template.Library()


@register.filter
def is_hoc_vien(user):
    return _is_hoc_vien(user)


@register.filter
def is_quan_tri(user):
    return _is_quan_tri(user)


@register.filter
def initials(user):
    """Chữ cái đầu của 2 từ cuối trong họ tên (VD: Lê Thị Thúy Vy -> TV)."""
    name = (user.get_full_name() or user.get_username() or "?").strip()
    parts = name.split()
    letters = "".join(p[0] for p in parts[-2:]) if len(parts) > 1 else name[:2]
    return letters.upper()


@register.filter
def role_label(user):
    if _is_quan_tri(user):
        return "Quản trị viên"
    if _is_hoc_vien(user):
        return "Học viên"
    return "Chờ cấp quyền"


@register.filter
def access_label(user):
    """Dòng quyền truy cập ở chân trang (theo Figma)."""
    if not user.is_authenticated:
        return "IELTS ĐÌNH LỰC"
    if _is_quan_tri(user):
        return "Quyền truy cập: QUẢN TRỊ VIÊN - Dành cho quản trị viên"
    if _is_hoc_vien(user):
        return f"Quyền truy cập: {HOC_VIEN_GROUP} - Dành cho học viên"
    return "Tài khoản chưa được cấp quyền Học viên"
