"""Regression tests UI/permission for shared layout; not testing external Gemini API."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


class UnifiedWebsiteSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(username='ui_student', password='test-strong-123')
        group, _ = Group.objects.get_or_create(name='HOC_VIEN')
        cls.student.groups.add(group)
        cls.admin = User.objects.create_superuser(username='ui_admin', email='ui@example.test', password='test-strong-123')
        cls.staff_without_permissions = User.objects.create_user(username='ui_staff', is_staff=True, password='test-strong-123')

    def test_public_home_shared_nav(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Luyện tập mỗi ngày')
        self.assertContains(r, 'site-global-header')
        self.assertContains(r, 'site-global-footer')

    def test_student_access_and_shared_nav(self):
        self.client.force_login(self.student)
        paths = ['listening:exercise_list', 'reading:exercise_list', 'writing:prompt_list',
                 'speaking:exercise_list', 'vocabulary:topic_list', 'progress:dashboard',
                 'feedback:feedback_submit', 'accounts:profile']
        for name in paths:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, 'site-global-header')
                self.assertContains(r, 'site-global-footer')

    def test_teacher_dashboard_and_managers(self):
        self.client.force_login(self.admin)
        paths = ['management:dashboard', 'management:writing_prompt_list',
                 'management:speaking_exercise_list', 'management:reading_exercise_list',
                 'management:listening_exercise_list', 'feedback:feedback_list',
                 'accounts:manage_users']
        for name in paths:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, 'teacher-sidebar')

    def test_staff_without_permissions_forbidden_teacher_dashboard(self):
        self.client.force_login(self.staff_without_permissions)
        r = self.client.get(reverse('management:dashboard'))
        self.assertEqual(r.status_code, 403)

    def test_student_forbidden_teacher_actions(self):
        self.client.force_login(self.student)
        for name in ['management:dashboard', 'management:reading_exercise_create',
                     'management:listening_exercise_create']:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 403)

    def test_teacher_receptive_create_forms(self):
        self.client.force_login(self.admin)
        for name in ['management:reading_exercise_create', 'management:listening_exercise_create']:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, 'name="title"')

    def test_teacher_creates_reading_exercise_and_question(self):
        from receptive.models import Exercise, Question, Option
        self.client.force_login(self.admin)
        r = self.client.post(reverse('management:reading_exercise_create'), {
            'title':'Bài Reading test', 'topic':'Education', 'description':'Demo',
            'level':'BEGINNER','passage':'A brief passage','status':'HIDDEN',
        })
        self.assertEqual(r.status_code, 302)
        exercise = Exercise.objects.get(title='Bài Reading test')
        self.assertEqual(exercise.skill, 'READING')
        r = self.client.post(reverse('management:reading_question_create', args=[exercise.pk]), {
            'order_no':1,'question_type':'MCQ','question_text':'Choose the correct answer',
            'correct_answers':'["A"]','explanation':'Because ...','status':'HIDDEN',
        })
        self.assertEqual(r.status_code, 302)
        question = Question.objects.get(exercise=exercise)
        r = self.client.post(reverse('management:reading_option_create', args=[exercise.pk,question.pk]), {
            'order_no':1,'option_key':'A','option_text':'A correct answer',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Option.objects.get(question=question).option_key,'A')

    def test_private_speaking_recording_denies_other_students(self):
        from tempfile import TemporaryDirectory
        from django.test import override_settings
        from django.core.files.base import ContentFile
        from speaking.models import SpeakingExercise, SpeakingSubmission
        from django.urls import reverse
        other = get_user_model().objects.create_user(username='other_student',password='test-strong-123')
        other.groups.add(Group.objects.get(name='HOC_VIEN'))
        with TemporaryDirectory() as tempdir, override_settings(MEDIA_ROOT=tempdir):
            exercise = SpeakingExercise.objects.create(title='Audio security test',part='PART_1',topic='Test',
                prompt_text='Say anything',level='BEGINNER',status='PUBLISHED')
            sub = SpeakingSubmission(user=self.student, exercise=exercise, exercise_snapshot={},status='GRADING')
            sub.audio_file.save('recording.webm', ContentFile(b'webm test bytes'),save=True)
            path = '/media/' + sub.audio_file.name
            self.client.force_login(other)
            self.assertEqual(self.client.get(path).status_code,404)
            self.client.force_login(self.student)
            r = self.client.get(path)
            self.assertEqual(r.status_code,200)
            self.assertEqual(r['Content-Type'],'audio/webm')
            r.close()
            self.client.force_login(self.admin)
            r = self.client.get(path)
            self.assertEqual(r.status_code,200)
            r.close()
