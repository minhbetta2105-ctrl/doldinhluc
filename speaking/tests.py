import io
import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.permissions import HOC_VIEN_GROUP
from speaking.models import SpeakingExercise, SpeakingSupport, SpeakingSubmission
from speaking.services.ielts_rubric import (
    calculate_ielts_speaking_overall,
    build_ielts_speaking_prompt,
)
from speaking.services.ai_grading import (
    MockSpeakingAIGradingProvider,
    parse_and_validate_speaking_payload,
    validate_speaking_score,
    grade_speaking_submission_safely,
    AIResponseValidationError,
    AIConnectionError,
    AITimeoutError,
)

User = get_user_model()


class IELTSSpeakingRubricUnitTest(TestCase):
    """Kiểm tra logic tính điểm và làm tròn IELTS Speaking Band theo chuẩn quốc tế."""

    def test_overall_calculation_exact(self):
        # 6.0 + 6.0 + 6.0 + 6.0 -> 6.0
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("6.0"), Decimal("6.0"), Decimal("6.0"), Decimal("6.0")
            ),
            Decimal("6.0")
        )

    def test_overall_calculation_round_to_half(self):
        # (6.5 + 6.5 + 6.0 + 6.0) / 4 = 6.25 -> làm tròn lên 6.5
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("6.5"), Decimal("6.5"), Decimal("6.0"), Decimal("6.0")
            ),
            Decimal("6.5")
        )
        # (6.5 + 6.5 + 6.5 + 6.0) / 4 = 6.375 -> làm tròn lên 6.5
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("6.5"), Decimal("6.5"), Decimal("6.5"), Decimal("6.0")
            ),
            Decimal("6.5")
        )
        # (6.5 + 7.0 + 6.5 + 6.5) / 4 = 6.625 -> làm tròn xuống 6.5
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("6.5"), Decimal("7.0"), Decimal("6.5"), Decimal("6.5")
            ),
            Decimal("6.5")
        )

    def test_overall_calculation_round_to_next_whole(self):
        # (7.0 + 6.5 + 6.5 + 7.0) / 4 = 6.75 -> làm tròn lên 7.0
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("7.0"), Decimal("6.5"), Decimal("6.5"), Decimal("7.0")
            ),
            Decimal("7.0")
        )
        # (7.0 + 7.0 + 7.0 + 6.5) / 4 = 6.875 -> làm tròn lên 7.0
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("7.0"), Decimal("7.0"), Decimal("7.0"), Decimal("6.5")
            ),
            Decimal("7.0")
        )

    def test_overall_calculation_round_down_to_whole(self):
        # (6.0 + 6.0 + 6.0 + 6.5) / 4 = 6.125 -> làm tròn xuống 6.0
        self.assertEqual(
            calculate_ielts_speaking_overall(
                Decimal("6.0"), Decimal("6.0"), Decimal("6.0"), Decimal("6.5")
            ),
            Decimal("6.0")
        )

    def test_overall_calculation_invalid_input(self):
        with self.assertRaises(ValueError):
            calculate_ielts_speaking_overall(Decimal("-1.0"), Decimal("6.0"), Decimal("6.0"), Decimal("6.0"))
        with self.assertRaises(ValueError):
            calculate_ielts_speaking_overall(Decimal("9.5"), Decimal("6.0"), Decimal("6.0"), Decimal("6.0"))

    def test_build_ielts_speaking_prompt(self):
        prompt = build_ielts_speaking_prompt("Part 1", "Hometown", "Where do you come from?")
        self.assertIn("Part 1", prompt)
        self.assertIn("Hometown", prompt)
        self.assertIn("Where do you come from?", prompt)
        self.assertIn("fluency_score", prompt)
        self.assertIn("pronunciation_score", prompt)


class SpeakingAIGradingValidationTest(TestCase):
    """Kiểm tra xác thực payload phản hồi từ AI."""

    def test_validate_speaking_score(self):
        self.assertEqual(validate_speaking_score(6.5, "test"), Decimal("6.5"))
        self.assertEqual(validate_speaking_score("7.0", "test"), Decimal("7.0"))
        with self.assertRaises(AIResponseValidationError):
            validate_speaking_score(6.3, "test")  # Không phải bước 0.5
        with self.assertRaises(AIResponseValidationError):
            validate_speaking_score(10.0, "test")  # Ngoài thang điểm
        with self.assertRaises(AIResponseValidationError):
            validate_speaking_score(None, "test")

    def test_parse_and_validate_speaking_payload_success(self):
        valid_payload = {
            "transcript": "Hello, I live in Hanoi.",
            "fluency_score": 6.5,
            "lexical_score": 6.0,
            "grammar_score": 6.0,
            "pronunciation_score": 6.5,
            "overall_feedback": "Khá tốt.",
            "strengths": ["Nói tự nhiên"],
            "weaknesses": ["Còn lỗi thì"],
            "grammar_corrections": [],
            "vocabulary_suggestions": [],
            "pronunciation_feedback": [],
            "improvement_suggestions": [],
        }
        res = parse_and_validate_speaking_payload(valid_payload)
        self.assertEqual(res.overall_score, Decimal("6.5"))
        self.assertEqual(res.fluency_score, Decimal("6.5"))
        self.assertEqual(res.transcript, "Hello, I live in Hanoi.")

    def test_parse_and_validate_speaking_payload_missing_transcript(self):
        payload = {
            "transcript": "",
            "fluency_score": 6.5,
            "lexical_score": 6.0,
            "grammar_score": 6.0,
            "pronunciation_score": 6.5,
        }
        with self.assertRaises(AIResponseValidationError):
            parse_and_validate_speaking_payload(payload)


class SpeakingModelAndAccessTest(TestCase):
    """Kiểm tra các Model, ràng buộc toàn vẹn và phân quyền truy cập Speaking."""

    def setUp(self):
        self.hoc_vien_group, _ = Group.objects.get_or_create(name=HOC_VIEN_GROUP)

        # Học viên có quyền
        self.student = User.objects.create_user(
            username="student_spk",
            password="Password123@",
            first_name="Học Viên",
            email="student_spk@example.com"
        )
        self.student.groups.add(self.hoc_vien_group)

        # Học viên khác (để test IDOR)
        self.other_student = User.objects.create_user(
            username="other_spk",
            password="Password123@",
            first_name="Học Viên Khác"
        )
        self.other_student.groups.add(self.hoc_vien_group)

        # Người dùng thường chưa được duyệt vào HOC_VIEN
        self.unapproved_user = User.objects.create_user(
            username="unapproved_user",
            password="Password123@"
        )

        # Quản trị viên
        self.staff_user = User.objects.create_user(
            username="staff_spk",
            password="Password123@",
            is_staff=True
        )

        # Đề bài công bố
        self.published_exercise = SpeakingExercise.objects.create(
            title="Describe your hometown",
            part=SpeakingExercise.Part.PART_1,
            topic="Hometown",
            prompt_text="Where is your hometown? What do you like about it?",
            level=SpeakingExercise.Level.INTERMEDIATE,
            status=SpeakingExercise.Status.PUBLISHED
        )

        # Đề bài bị ẩn
        self.hidden_exercise = SpeakingExercise.objects.create(
            title="Hidden Speaking Task",
            part=SpeakingExercise.Part.PART_2,
            topic="Technology",
            prompt_text="Describe an AI tool you use daily.",
            level=SpeakingExercise.Level.ADVANCED,
            status=SpeakingExercise.Status.HIDDEN
        )

        # Tài liệu hỗ trợ
        self.support = SpeakingSupport.objects.create(
            exercise=self.published_exercise,
            idea_hint="Talk about location, weather, and people.",
            sample_answer="Well, I was born and raised in Da Nang city...",
            suggested_vocabulary="picturesque, coastal city, vibrant"
        )

    def test_unauthenticated_user_redirected(self):
        """1. Người chưa đăng nhập bị chuyển hướng đến trang login."""
        resp = self.client.get(reverse("speaking:exercise_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_unapproved_user_denied_access(self):
        """2. Người chưa có Group HOC_VIEN nhận thông báo 403."""
        self.client.force_login(self.unapproved_user)
        resp = self.client.get(reverse("speaking:exercise_list"))
        self.assertEqual(resp.status_code, 403)

    def test_student_can_view_published_exercises(self):
        """3. Học viên có quyền xem danh sách đề PUBLISHED."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse("speaking:exercise_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Describe your hometown")
        self.assertNotContains(resp, "Hidden Speaking Task")

    def test_filter_exercises_by_part_and_level(self):
        """4. Bộ lọc theo Part, Level, Topic hoạt động chính xác."""
        self.client.force_login(self.student)

        # Lọc theo Part 1
        resp = self.client.get(reverse("speaking:exercise_list") + "?part=PART_1")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Describe your hometown")

        # Lọc theo Part 3 (không có)
        resp = self.client.get(reverse("speaking:exercise_list") + "?part=PART_3")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Describe your hometown")

    def test_hidden_exercise_cannot_be_opened_by_student(self):
        """5. Đề HIDDEN trả về 404 khi học viên cố tình mở link trực tiếp."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse("speaking:exercise_detail", args=[self.hidden_exercise.id]))
        self.assertEqual(resp.status_code, 404)

    def test_exercise_detail_loads_support_material(self):
        """6. Màn hình làm bài hiển thị đầy đủ tài liệu hỗ trợ."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse("speaking:exercise_detail", args=[self.published_exercise.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Talk about location, weather, and people.")
        self.assertContains(resp, "picturesque, coastal city, vibrant")

    def test_submit_speaking_without_audio_rejected(self):
        """7. Không nộp bài khi chưa có audio."""
        self.client.force_login(self.student)
        sub_key = str(uuid.uuid4())
        resp = self.client.post(
            reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
            {"submission_key": sub_key}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(SpeakingSubmission.objects.count(), 0)

    def test_submit_speaking_invalid_audio_format_rejected(self):
        """8. Từ chối tệp âm thanh sai định dạng (ví dụ: .txt)."""
        self.client.force_login(self.student)
        sub_key = str(uuid.uuid4())
        fake_file = SimpleUploadedFile("malicious.txt", b"plain text content", content_type="text/plain")
        resp = self.client.post(
            reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
            {"submission_key": sub_key, "audio_file": fake_file}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(SpeakingSubmission.objects.count(), 0)

    def test_submit_speaking_successful_with_mock_ai(self):
        """9. Nộp bài hợp lệ: lưu vào database và AI chấm điểm chuyển sang GRADED."""
        self.client.force_login(self.student)
        sub_key = str(uuid.uuid4())
        audio_content = b"RIFF....WAVEfmt ...."  # Giả lập audio bytes
        audio_file = SimpleUploadedFile("test_recording.mp3", audio_content, content_type="audio/mp3")

        mock_provider = MockSpeakingAIGradingProvider(
            fc=Decimal("6.5"),
            lr=Decimal("6.0"),
            gra=Decimal("6.0"),
            p=Decimal("6.5")
        )

        with patch("speaking.views.grade_speaking_submission_safely") as mock_grade:
            def side_effect(sub):
                grade_speaking_submission_safely(sub, provider=mock_provider)
            mock_grade.side_effect = side_effect

            resp = self.client.post(
                reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
                {"submission_key": sub_key, "audio_file": audio_file}
            )

        self.assertEqual(resp.status_code, 302)
        sub = SpeakingSubmission.objects.get(submission_key=sub_key)
        self.assertEqual(sub.status, SpeakingSubmission.Status.GRADED)
        self.assertEqual(sub.overall_score, Decimal("6.5"))
        self.assertEqual(sub.fluency_score, Decimal("6.5"))
        self.assertEqual(sub.pronunciation_score, Decimal("6.5"))
        self.assertIsNotNone(sub.feedback)
        self.assertIsNotNone(sub.graded_at)

    def test_idempotent_duplicate_submission_does_not_create_duplicate(self):
        """10. Gửi trùng submission_key không tạo bản ghi mới."""
        self.client.force_login(self.student)
        sub_key = str(uuid.uuid4())
        audio_file = SimpleUploadedFile("test.mp3", b"dummy audio", content_type="audio/mp3")

        mock_provider = MockSpeakingAIGradingProvider()

        # Nộp lần 1
        with patch("speaking.views.grade_speaking_submission_safely", side_effect=lambda s: grade_speaking_submission_safely(s, provider=mock_provider)):
            resp1 = self.client.post(
                reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
                {"submission_key": sub_key, "audio_file": audio_file}
            )
        self.assertEqual(resp1.status_code, 302)
        self.assertEqual(SpeakingSubmission.objects.filter(submission_key=sub_key).count(), 1)

        # Nộp lần 2 với cùng submission_key
        audio_file2 = SimpleUploadedFile("test.mp3", b"dummy audio", content_type="audio/mp3")
        resp2 = self.client.post(
            reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
            {"submission_key": sub_key, "audio_file": audio_file2}
        )
        self.assertEqual(resp2.status_code, 302)
        self.assertEqual(SpeakingSubmission.objects.filter(submission_key=sub_key).count(), 1)

    def test_ai_error_marks_status_failed_and_score_null(self):
        """11. AI gặp lỗi thì chuyển sang FAILED và điểm để NULL, tuyệt đối không gán 0.0."""
        self.client.force_login(self.student)
        sub_key = str(uuid.uuid4())
        audio_file = SimpleUploadedFile("test.mp3", b"dummy audio", content_type="audio/mp3")

        mock_failing_provider = MockSpeakingAIGradingProvider(
            exception_to_raise=AITimeoutError("Gemini API timed out")
        )

        with patch("speaking.views.grade_speaking_submission_safely", side_effect=lambda s: grade_speaking_submission_safely(s, provider=mock_failing_provider)):
            resp = self.client.post(
                reverse("speaking:exercise_submit", args=[self.published_exercise.id]),
                {"submission_key": sub_key, "audio_file": audio_file}
            )

        sub = SpeakingSubmission.objects.get(submission_key=sub_key)
        self.assertEqual(sub.status, SpeakingSubmission.Status.FAILED)
        self.assertIsNone(sub.overall_score)
        self.assertIsNone(sub.fluency_score)
        self.assertNotEqual(sub.overall_score, Decimal("0.0"))

    def test_idor_protection_student_cannot_view_others_submission(self):
        """12. IDOR: Học viên không được xem bài nộp của học viên khác (trả về 404)."""
        sub = SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.other_student,
            exercise=self.published_exercise,
            exercise_snapshot={"title": "Test"},
            audio_file=SimpleUploadedFile("dummy.mp3", b"audio"),
            status=SpeakingSubmission.Status.GRADED,
            overall_score=Decimal("7.0")
        )

        self.client.force_login(self.student)
        resp = self.client.get(reverse("speaking:submission_result", args=[sub.submission_key]))
        self.assertEqual(resp.status_code, 404)

        self.client.force_login(self.other_student)
        resp_own = self.client.get(reverse("speaking:submission_result", args=[sub.submission_key]))
        self.assertEqual(resp_own.status_code, 200)

    def test_submission_result_get_does_not_call_ai_api(self):
        """13. Mở trang kết quả (GET) không gọi lại AI API."""
        sub = SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.published_exercise,
            exercise_snapshot={"title": "Test Snapshot", "part": "Part 1", "level": "Intermediate", "topic": "Travel", "prompt_text": "Sample"},
            audio_file=SimpleUploadedFile("dummy.mp3", b"audio"),
            status=SpeakingSubmission.Status.GRADED,
            overall_score=Decimal("6.5"),
            fluency_score=Decimal("6.5"),
            pronunciation_score=Decimal("6.5"),
            vocabulary_score=Decimal("6.5"),
            grammar_score=Decimal("6.5"),
            feedback=json.dumps({"transcript": "Sample transcript", "overall_feedback": "Good job"})
        )

        self.client.force_login(self.student)
        with patch("speaking.services.ai_grading.GeminiSpeakingAIGradingProvider.grade") as mock_api:
            resp = self.client.get(reverse("speaking:submission_result", args=[sub.submission_key]))
            self.assertEqual(resp.status_code, 200)
            mock_api.assert_not_called()

    def test_exercise_cannot_be_deleted_if_submissions_exist(self):
        """14. Không xóa vật lý đề bài đã phát sinh bài nộp của học viên."""
        sub = SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.published_exercise,
            exercise_snapshot={"title": "Snapshot"},
            audio_file=SimpleUploadedFile("dummy.mp3", b"audio"),
            status=SpeakingSubmission.Status.GRADED,
            overall_score=Decimal("6.0")
        )

        with self.assertRaises(ValidationError):
            self.published_exercise.delete()


class SpeakingManagementAdminTest(TestCase):
    """Kiểm tra chức năng quản trị đề Speaking (UC-SPK-05, UC-SPK-06)."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="admin_staff",
            password="Password123@",
            is_staff=True
        )
        for codename in [
            "view_speakingexercise", "add_speakingexercise",
            "change_speakingexercise", "delete_speakingexercise",
            "view_speakingsupport", "change_speakingsupport"
        ]:
            perm = Permission.objects.filter(codename=codename).first()
            if perm:
                self.staff_user.user_permissions.add(perm)

        self.student = User.objects.create_user(
            username="student_user",
            password="Password123@"
        )
        self.exercise = SpeakingExercise.objects.create(
            title="Describe an important decision",
            part=SpeakingExercise.Part.PART_2,
            topic="Life Experience",
            prompt_text="Describe a decision you made recently.",
            level=SpeakingExercise.Level.ADVANCED,
            status=SpeakingExercise.Status.HIDDEN
        )

    def test_student_cannot_access_speaking_management(self):
        """Học viên không có quyền truy cập trang quản trị Speaking."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse("management:speaking_exercise_list"))
        self.assertEqual(resp.status_code, 403)

    def test_staff_can_view_speaking_exercises_list(self):
        """Staff có quyền xem danh sách đề Speaking."""
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse("management:speaking_exercise_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Describe an important decision")

    def test_staff_can_toggle_exercise_status(self):
        """Staff có thể chuyển đổi trạng thái Ẩn/Hiện của đề Speaking."""
        self.client.force_login(self.staff_user)
        self.assertEqual(self.exercise.status, SpeakingExercise.Status.HIDDEN)

        # Chuyển sang PUBLISHED
        resp = self.client.post(reverse("management:speaking_exercise_status_toggle", args=[self.exercise.id]))
        self.assertEqual(resp.status_code, 302)
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.status, SpeakingExercise.Status.PUBLISHED)

        # Chuyển ngược lại sang HIDDEN
        self.client.post(reverse("management:speaking_exercise_status_toggle", args=[self.exercise.id]))
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.status, SpeakingExercise.Status.HIDDEN)
