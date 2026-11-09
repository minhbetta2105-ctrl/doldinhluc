from django.test import SimpleTestCase
from receptive.services.grading import is_answer_correct, normalize_answer_string


class ReceptiveGradingTests(SimpleTestCase):
    def test_normalize_answer_string(self):
        self.assertEqual(normalize_answer_string("  Hello   World  "), "hello world")
        self.assertEqual(normalize_answer_string(""), "")
        self.assertEqual(normalize_answer_string(None), "")

    def test_grading_mcq(self):
        self.assertTrue(is_answer_correct("MCQ", "A", ["A"]))
        self.assertTrue(is_answer_correct("MCQ", "b", ["B"]))
        self.assertFalse(is_answer_correct("MCQ", "C", ["A", "B"]))

    def test_grading_tfng_ynng(self):
        self.assertTrue(is_answer_correct("TFNG", "true", ["True"]))
        self.assertTrue(is_answer_correct("TFNG", "NOT GIVEN", ["Not Given"]))
        self.assertTrue(is_answer_correct("YNNG", "yes", ["Yes"]))
        self.assertFalse(is_answer_correct("TFNG", "False", ["True"]))

    def test_grading_short_text(self):
        accepted = ["an apple", "apple", "apples"]
        self.assertTrue(is_answer_correct("SHORT_TEXT", "apple", accepted))
        self.assertTrue(is_answer_correct("SHORT_TEXT", "An Apple", accepted))
        self.assertFalse(is_answer_correct("SHORT_TEXT", "orange", accepted))

    def test_empty_answer_never_correct(self):
        self.assertFalse(is_answer_correct("MCQ", "", ["A"]))
        self.assertFalse(is_answer_correct("MCQ", "   ", ["A"]))
        self.assertFalse(is_answer_correct("SHORT_TEXT", "", ["apple"]))
        self.assertFalse(is_answer_correct("SHORT_TEXT", None, ["apple"]))
