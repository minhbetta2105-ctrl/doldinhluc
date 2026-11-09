import re

from django import forms

from .models import Topic, Word

BLANK_RE = re.compile(r"_{3,}")


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ("name", "description", "level", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        clash = Topic.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("Tên chủ đề đã tồn tại.")
        return name


class WordForm(forms.ModelForm):
    """Chủ đề được gán trong view (không cho chọn trong form)."""

    class Meta:
        model = Word
        fields = ("word", "phonetic", "part_of_speech", "meaning_vi", "example_sentence",
                  "gap_sentence", "gap_answer", "audio_file", "status")
        widgets = {
            "meaning_vi": forms.Textarea(attrs={"rows": 2}),
            "example_sentence": forms.Textarea(attrs={"rows": 2}),
            "gap_sentence": forms.Textarea(attrs={"rows": 2}),
        }
        help_texts = {
            "gap_sentence": "Dùng cho bài Kéo & Thả. Đặt đúng MỘT ô trống bằng ___ (ví dụ: She bought a ___ yesterday.)",
            "gap_answer": "Bắt buộc nếu có câu điền khuyết.",
            "audio_file": "Tùy chọn. Đường dẫn/URL file phát âm; để trống sẽ dùng giọng đọc của trình duyệt.",
        }

    def __init__(self, *args, topic=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic = topic or getattr(self.instance, "topic", None)

    def clean_word(self):
        word = self.cleaned_data["word"].strip()
        if self.topic is not None:
            clash = Word.objects.filter(topic=self.topic, word__iexact=word).exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError("Từ này đã có trong chủ đề.")
        return word

    def clean(self):
        cleaned = super().clean()
        gap = (cleaned.get("gap_sentence") or "").strip()
        answer = (cleaned.get("gap_answer") or "").strip()
        if gap:
            if len(BLANK_RE.findall(gap)) != 1:
                self.add_error("gap_sentence", "Câu điền khuyết phải có đúng một ô trống (___).")
            if not answer:
                self.add_error("gap_answer", "Hãy nhập đáp án cho ô trống.")
        elif answer:
            self.add_error("gap_sentence", "Có đáp án ô trống thì cần có câu điền khuyết.")
        cleaned["gap_sentence"], cleaned["gap_answer"] = gap, answer
        return cleaned
