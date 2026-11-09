import uuid
from django.test import SimpleTestCase, RequestFactory
from django.urls import reverse
from listening import views


class ListeningViewRoutingTests(SimpleTestCase):
    def test_reverse_urls(self):
        self.assertEqual(reverse("listening:exercise_list"), "/listening/")
        self.assertEqual(reverse("listening:exercise_detail", kwargs={"pk": 1}), "/listening/1/")
        self.assertEqual(reverse("listening:exercise_submit", kwargs={"pk": 1}), "/listening/1/submit/")
        key = uuid.uuid4()
        self.assertEqual(
            reverse("listening:attempt_result", kwargs={"submission_key": key}),
            f"/listening/attempt/{key}/result/",
        )

    def test_anonymous_redirects(self):
        factory = RequestFactory()
        req = factory.get(reverse("listening:exercise_list"))
        from django.contrib.auth.models import AnonymousUser
        req.user = AnonymousUser()
        resp = views.exercise_list(req)
        # Should redirect to login
        self.assertEqual(resp.status_code, 302)
