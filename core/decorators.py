"""Lớp tương thích Q2: Reading/Listening dùng cùng chính sách HOC_VIEN của Accounts.

Đây là re-export, không chỉnh sửa logic làm bài các module gốc.
"""
from accounts.permissions import HOC_VIEN_GROUP, hoc_vien_required, is_hoc_vien

__all__ = ["HOC_VIEN_GROUP", "hoc_vien_required", "is_hoc_vien"]
