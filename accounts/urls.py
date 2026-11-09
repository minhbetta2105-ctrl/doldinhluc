from django.urls import path
from django.contrib.auth import get_user_model
from core.integration_permissions import admin_permissions_required
from . import views

app_name = "accounts"

# Tương thích khi thay đổi AUTH_USER_MODEL trong tương lai.
user_model = get_user_model()
prefix = f"{user_model._meta.app_label}."
view_user = prefix + f"view_{user_model._meta.model_name}"
change_user = prefix + f"change_{user_model._meta.model_name}"

can_list_users = admin_permissions_required(view_user, change_user, match_any=True)
can_change_user = admin_permissions_required(change_user)

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("waiting/", views.waiting_view, name="waiting"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("manage/", can_list_users(views.manage_users), name="manage_users"),
    path("manage/<int:user_id>/", can_list_users(views.profile_view), name="user_profile"),
    path("manage/<int:user_id>/edit/", can_change_user(views.profile_edit), name="user_edit"),
    path("manage/<int:user_id>/toggle-active/", can_change_user(views.toggle_active), name="toggle_active"),
    path("manage/<int:user_id>/student/", can_change_user(views.set_student), name="set_student"),
]
