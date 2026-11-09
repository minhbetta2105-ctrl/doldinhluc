"""New regression checks for unified group policy and administration routing."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.permissions import is_hoc_vien


class IntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = get_user_model().objects.create_user(username="student_demo", password="examplepass123")
        cls.staff = get_user_model().objects.create_user(username="staff_demo", password="examplepass123", is_staff=True)
        cls.group = Group.objects.create(name="HOC_VIEN")

    def test_public_home_and_all_routes(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        for name in ("accounts:login", "reading:exercise_list", "listening:exercise_list", "writing:prompt_list", "vocabulary:topic_list", "management:writing_prompt_list"):
            self.assertTrue(reverse(name).startswith("/"))

    def test_non_student_denied_practice(self):
        self.client.force_login(self.person)
        for name in ("reading:exercise_list", "listening:exercise_list", "writing:prompt_list", "vocabulary:topic_list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    @override_settings(DEBUG=True)
    def test_staff_not_exempt_from_learning_group(self):
        self.client.force_login(self.staff)
        self.assertFalse(is_hoc_vien(self.staff))
        for name in ("reading:exercise_list", "listening:exercise_list", "writing:prompt_list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_group_grant_revoke(self):
        self.assertFalse(is_hoc_vien(self.person))
        self.person.groups.add(self.group)
        self.assertTrue(is_hoc_vien(self.person))
        self.person.groups.remove(self.group)
        self.assertFalse(is_hoc_vien(self.person))

    def test_accounts_model_permission(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("accounts:manage_users")).status_code, 403)
        perm = Permission.objects.get(codename="view_user", content_type__app_label="auth")
        self.staff.user_permissions.add(perm)
        self.assertEqual(self.client.get(reverse("accounts:manage_users")).status_code, 200)
        self.assertEqual(self.client.post(reverse("accounts:toggle_active", args=[self.person.pk])).status_code, 403)

    def test_vocabulary_model_permission(self):
        self.client.force_login(self.staff)
        url = reverse("vocabulary:manage_topics")
        self.assertEqual(self.client.get(url).status_code, 403)
        perm = Permission.objects.get(codename="view_topic", content_type__app_label="vocabulary")
        self.staff.user_permissions.add(perm)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("vocabulary:topic_create")).status_code, 403)
