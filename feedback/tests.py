from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.permissions import HOC_VIEN_GROUP
from feedback.models import ServiceFeedback

User = get_user_model()


class FeedbackModuleTest(TestCase):
    """
    Bộ kiểm thử cho Module Đánh giá / Góp ý (Feedback) theo UC-FBK-01, UC-FBK-02, UC-FBK-03.
    """

    def setUp(self):
        self.hoc_vien_group, _ = Group.objects.get_or_create(name=HOC_VIEN_GROUP)

        # Học viên hợp lệ
        self.student = User.objects.create_user(
            username="student_feedback",
            password="Password123@",
            first_name="Học Viên Góp Ý"
        )
        self.student.groups.add(self.hoc_vien_group)

        # Người dùng thường chưa có quyền HOC_VIEN
        self.unapproved_user = User.objects.create_user(
            username="regular_user",
            password="Password123@"
        )

        # Quản trị viên (is_staff=True)
        self.staff_admin = User.objects.create_user(
            username="staff_feedback_admin",
            password="Password123@",
            is_staff=True
        )

        # Dữ liệu mẫu ban đầu
        self.feedback_visible = ServiceFeedback.objects.create(
            user=self.student,
            content="Giao diện làm bài rất trực quan, tôi thấy tính năng ghi âm rất tiện lợi.",
            status=ServiceFeedback.Status.VISIBLE
        )

        self.feedback_hidden = ServiceFeedback.objects.create(
            user=self.student,
            content="Phản hồi thử nghiệm đã bị ẩn bởi quản trị viên.",
            status=ServiceFeedback.Status.HIDDEN
        )

    def test_unauthenticated_user_cannot_access_feedback_form(self):
        """Người chưa đăng nhập bị chuyển hướng đến trang đăng nhập."""
        resp = self.client.get(reverse("feedback:feedback_submit"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_unapproved_user_cannot_submit_feedback(self):
        """1. Người dùng chưa có Group HOC_VIEN bị từ chối truy cập (HTTP 403)."""
        self.client.force_login(self.unapproved_user)
        resp = self.client.get(reverse("feedback:feedback_submit"))
        self.assertEqual(resp.status_code, 403)

        post_resp = self.client.post(reverse("feedback:feedback_submit"), {"content": "Test content"})
        self.assertEqual(post_resp.status_code, 403)

    def test_student_submit_valid_feedback_success(self):
        """2. Học viên thuộc Group HOC_VIEN gửi phản hồi hợp lệ thành công (UC-FBK-01)."""
        self.client.force_login(self.student)
        feedback_content = "Hệ thống hỗ trợ rất tốt, tôi đã tiến bộ kỹ năng Speaking sau 1 tuần."

        resp = self.client.post(reverse("feedback:feedback_submit"), {
            "content": feedback_content
        })
        self.assertEqual(resp.status_code, 302)

        # Kiểm tra bản ghi trong DB
        new_feedback = ServiceFeedback.objects.filter(content=feedback_content).first()
        self.assertIsNotNone(new_feedback)
        self.assertEqual(new_feedback.user, self.student)
        self.assertEqual(new_feedback.status, ServiceFeedback.Status.VISIBLE)
        self.assertIsNotNone(new_feedback.created_at)

    def test_submit_empty_or_whitespace_feedback_rejected(self):
        """3. Không cho gửi nội dung rỗng hoặc chỉ chứa khoảng trắng."""
        self.client.force_login(self.student)
        initial_count = ServiceFeedback.objects.count()

        # Rỗng hoàn toàn
        resp = self.client.post(reverse("feedback:feedback_submit"), {"content": ""})
        self.assertEqual(resp.status_code, 200)  # Form invalid, render lại trang
        self.assertEqual(ServiceFeedback.objects.count(), initial_count)

        # Khoảng trắng
        resp_space = self.client.post(reverse("feedback:feedback_submit"), {"content": "    \n   "})
        self.assertEqual(resp_space.status_code, 200)
        self.assertEqual(ServiceFeedback.objects.count(), initial_count)

    def test_feedback_model_clean_validation(self):
        """4. Model clean() kiểm tra nội dung rỗng."""
        fb = ServiceFeedback(user=self.student, content="   ")
        with self.assertRaises(ValidationError):
            fb.clean()

    def test_student_cannot_access_feedback_admin_list(self):
        """5. Học viên thông thường không được phép truy cập trang quản trị phản hồi (HTTP 403)."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse("feedback:feedback_list"))
        self.assertEqual(resp.status_code, 403)

    def test_staff_can_view_feedback_list(self):
        """6. Quản trị viên xem được danh sách toàn bộ phản hồi (UC-FBK-02)."""
        self.client.force_login(self.staff_admin)
        resp = self.client.get(reverse("feedback:feedback_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Giao diện làm bài rất trực quan")
        self.assertContains(resp, "Phản hồi thử nghiệm đã bị ẩn")

    def test_filter_feedbacks_by_visible_and_hidden(self):
        """7. Lọc danh sách phản hồi theo VISIBLE và HIDDEN (UC-FBK-02)."""
        self.client.force_login(self.staff_admin)

        # Lọc VISIBLE
        resp_visible = self.client.get(reverse("feedback:feedback_list") + "?status=VISIBLE")
        self.assertEqual(resp_visible.status_code, 200)
        self.assertContains(resp_visible, "Giao diện làm bài rất trực quan")
        self.assertNotContains(resp_visible, "Phản hồi thử nghiệm đã bị ẩn")

        # Lọc HIDDEN
        resp_hidden = self.client.get(reverse("feedback:feedback_list") + "?status=HIDDEN")
        self.assertEqual(resp_hidden.status_code, 200)
        self.assertNotContains(resp_hidden, "Giao diện làm bài rất trực quan")
        self.assertContains(resp_hidden, "Phản hồi thử nghiệm đã bị ẩn")

    def test_staff_can_hide_and_unhide_feedback(self):
        """8. Quản trị viên có thể Ẩn hoặc Hiện lại phản hồi (UC-FBK-03)."""
        self.client.force_login(self.staff_admin)

        # 1. Ẩn phản hồi đang VISIBLE
        resp = self.client.post(reverse("feedback:feedback_status_toggle", args=[self.feedback_visible.id]))
        self.assertEqual(resp.status_code, 302)
        self.feedback_visible.refresh_from_db()
        self.assertEqual(self.feedback_visible.status, ServiceFeedback.Status.HIDDEN)

        # 2. Hiện lại phản hồi đang HIDDEN
        resp2 = self.client.post(reverse("feedback:feedback_status_toggle", args=[self.feedback_visible.id]))
        self.assertEqual(resp2.status_code, 302)
        self.feedback_visible.refresh_from_db()
        self.assertEqual(self.feedback_visible.status, ServiceFeedback.Status.VISIBLE)

    def test_staff_can_delete_feedback_permanently(self):
        """9. Quản trị viên xóa vĩnh viễn phản hồi khi đã xác nhận (UC-FBK-03)."""
        self.client.force_login(self.staff_admin)
        target_id = self.feedback_hidden.id

        resp = self.client.post(reverse("feedback:feedback_delete", args=[target_id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ServiceFeedback.objects.filter(id=target_id).exists())

    def test_student_cannot_delete_or_toggle_feedback(self):
        """10. Học viên không thể gửi POST để ẩn hoặc xóa phản hồi của người khác."""
        self.client.force_login(self.student)

        toggle_resp = self.client.post(reverse("feedback:feedback_status_toggle", args=[self.feedback_visible.id]))
        self.assertEqual(toggle_resp.status_code, 403)

        del_resp = self.client.post(reverse("feedback:feedback_delete", args=[self.feedback_visible.id]))
        self.assertEqual(del_resp.status_code, 403)
