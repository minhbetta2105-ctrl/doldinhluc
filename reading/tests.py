import uuid
from django.test import SimpleTestCase, RequestFactory
from django.urls import reverse
from reading import views


class ReadingViewRoutingTests(SimpleTestCase):
    def test_reverse_urls(self):
        self.assertEqual(reverse("reading:exercise_list"), "/reading/")
        self.assertEqual(reverse("reading:exercise_detail", kwargs={"pk": 1}), "/reading/1/")
        self.assertEqual(reverse("reading:exercise_submit", kwargs={"pk": 1}), "/reading/1/submit/")
        key = uuid.uuid4()
        self.assertEqual(
            reverse("reading:attempt_result", kwargs={"submission_key": key}),
            f"/reading/attempt/{key}/result/",
        )

    def test_anonymous_redirects(self):
        factory = RequestFactory()
        req = factory.get(reverse("reading:exercise_list"))
        from django.contrib.auth.models import AnonymousUser
        req.user = AnonymousUser()
        resp = views.exercise_list(req)
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
