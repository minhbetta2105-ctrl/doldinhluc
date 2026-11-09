"""Django Admin remains technical; teacher uses /management/."""
from django.contrib.admin import AdminSite

class DolSystemAdminSite(AdminSite):
    site_header = "DOL IELTS – Quản trị hệ thống"
    site_title = "DOL IELTS System Admin"
    index_title = "Quản trị kỹ thuật"

    def has_permission(self, request):
        user = request.user
        return bool(user.is_authenticated and user.is_active and user.is_superuser)
