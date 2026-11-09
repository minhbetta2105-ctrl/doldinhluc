from decimal import Decimal
import uuid
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.permissions import HOC_VIEN_GROUP
from speaking.models import SpeakingExercise, SpeakingSubmission

User = get_user_model()


class ProgressDashboardTests(TestCase):
    def setUp(self):
        self.hoc_vien_group, _ = Group.objects.get_or_create(name=HOC_VIEN_GROUP)

        self.student = User.objects.create_user(
            username="student_progress",
            password="Password123!",
            email="progress_student@test.com"
        )
        self.student.groups.add(self.hoc_vien_group)

        self.other_student = User.objects.create_user(
            username="other_student",
            password="Password123!",
            email="other_student@test.com"
        )
        self.other_student.groups.add(self.hoc_vien_group)

        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="Password123!",
            email="regular@test.com"
        )

        self.exercise = SpeakingExercise.objects.create(
            title="Describe your hometown",
            part=SpeakingExercise.Part.PART_1,
            topic="Hometown",
            prompt_text="Where is your hometown?",
            level=SpeakingExercise.Level.BEGINNER,
            status=SpeakingExercise.Status.PUBLISHED,
        )

    def test_dashboard_requires_login(self):
        url = reverse("progress:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_hoc_vien_group(self):
        self.client.login(username="regular_user", password="Password123!")
        url = reverse("progress:dashboard")
        response = self.client.get(url)
        # hoc_vien_required renders 403 / wait template or 302
        self.assertIn(response.status_code, [200, 302, 403])
        if response.status_code == 200:
            self.assertTemplateUsed(response, "accounts/cho_cap_quyen.html")

    def test_dashboard_speaking_statistics_calculation(self):
        self.client.login(username="student_progress", password="Password123!")

        dummy_audio = SimpleUploadedFile("audio.webm", b"audio_content", content_type="audio/webm")

        # 1. Graded submission 1: overall 6.5
        SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.exercise,
            exercise_snapshot={"title": self.exercise.title},
            audio_file=dummy_audio,
            overall_score=Decimal("6.5"),
            fluency_score=Decimal("6.0"),
            pronunciation_score=Decimal("6.5"),
            vocabulary_score=Decimal("7.0"),
            grammar_score=Decimal("6.5"),
            status=SpeakingSubmission.Status.GRADED,
        )

        # 2. Graded submission 2: overall 7.5
        dummy_audio2 = SimpleUploadedFile("audio2.webm", b"audio2_content", content_type="audio/webm")
        SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.exercise,
            exercise_snapshot={"title": self.exercise.title},
            audio_file=dummy_audio2,
            overall_score=Decimal("7.5"),
            fluency_score=Decimal("7.5"),
            pronunciation_score=Decimal("8.0"),
            vocabulary_score=Decimal("7.0"),
            grammar_score=Decimal("7.5"),
            status=SpeakingSubmission.Status.GRADED,
        )

        # 3. Submission currently grading (should count in total attempts, NOT in average score)
        dummy_audio3 = SimpleUploadedFile("audio3.webm", b"audio3_content", content_type="audio/webm")
        SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.exercise,
            exercise_snapshot={"title": self.exercise.title},
            audio_file=dummy_audio3,
            overall_score=None,
            status=SpeakingSubmission.Status.GRADING,
        )

        # 4. Failed submission (should count in total attempts, NOT in average score)
        dummy_audio4 = SimpleUploadedFile("audio4.webm", b"audio4_content", content_type="audio/webm")
        SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.student,
            exercise=self.exercise,
            exercise_snapshot={"title": self.exercise.title},
            audio_file=dummy_audio4,
            overall_score=None,
            status=SpeakingSubmission.Status.FAILED,
        )

        # 5. Other student's submission (should NOT affect student_progress's dashboard)
        dummy_audio5 = SimpleUploadedFile("audio5.webm", b"audio5_content", content_type="audio/webm")
        SpeakingSubmission.objects.create(
            submission_key=uuid.uuid4(),
            user=self.other_student,
            exercise=self.exercise,
            exercise_snapshot={"title": self.exercise.title},
            audio_file=dummy_audio5,
            overall_score=Decimal("9.0"),
            status=SpeakingSubmission.Status.GRADED,
        )

        url = reverse("progress:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Total attempts for student_progress: 4
        self.assertEqual(response.context["speaking_total_attempts"], 4)
        # Graded count: 2
        self.assertEqual(response.context["speaking_graded_count"], 2)
        # Avg score: (6.5 + 7.5) / 2 = 7.0
        self.assertEqual(response.context["speaking_avg_score"], 7.0)
        # Avg fluency: (6.0 + 7.5) / 2 = 6.75 -> rounded to 6.8
        self.assertEqual(response.context["speaking_avg_fluency"], 6.8)
        # Avg pronunciation: (6.5 + 8.0) / 2 = 7.25 -> rounded to 7.2 or 7.3
        self.assertAlmostEqual(response.context["speaking_avg_pronunciation"], 7.25, delta=0.1)

    def test_dashboard_with_zero_submissions(self):
        self.client.login(username="student_progress", password="Password123!")
        url = reverse("progress:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["speaking_total_attempts"], 0)
        self.assertEqual(response.context["speaking_graded_count"], 0)
        self.assertIsNone(response.context["speaking_avg_score"])
