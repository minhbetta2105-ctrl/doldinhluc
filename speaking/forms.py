import os
from django import forms
from django.core.exceptions import ValidationError

from .models import SpeakingExercise, SpeakingSupport, SpeakingSubmission

ALLOWED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".webm", ".ogg", ".m4a", ".aac", ".flac")
MAX_AUDIO_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


class SpeakingSubmissionForm(forms.Form):
    """
    Form tiếp nhận và xác thực bài nộp Speaking phía server (UC-SPK-03).
    """
    submission_key = forms.UUIDField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={
            "required": "Thiếu mã định danh bài nộp (submission_key).",
            "invalid": "Mã định danh bài nộp không đúng định dạng UUID.",
        }
    )

    audio_file = forms.FileField(
        required=True,
        error_messages={
            "required": "Vui lòng ghi âm trực tiếp hoặc chọn tệp âm thanh từ máy tính trước khi nộp bài.",
        }
    )

    def clean_audio_file(self):
        audio = self.cleaned_data.get("audio_file")
        if not audio:
            raise ValidationError("Vui lòng tải lên hoặc ghi âm tệp âm thanh bài nói.")

        # Kiểm tra dung lượng
        if audio.size > MAX_AUDIO_SIZE_BYTES:
            max_mb = MAX_AUDIO_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(
                f"Dung lượng tệp âm thanh ({audio.size / (1024 * 1024):.1f}MB) vượt quá giới hạn cho phép ({max_mb:.0f}MB)."
            )

        if audio.size == 0:
            raise ValidationError("Tệp âm thanh rỗng (0 bytes). Vui lòng thử ghi âm lại.")

        # Kiểm tra phần mở rộng tệp
        name = audio.name.lower()
        ext = os.path.splitext(name)[1]
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            allowed_str = ", ".join(ALLOWED_AUDIO_EXTENSIONS)
            raise ValidationError(
                f"Định dạng tệp âm thanh '{ext}' không được hỗ trợ. Các định dạng cho phép: {allowed_str}."
            )

        return audio


class SpeakingExerciseAdminForm(forms.ModelForm):
    """Form quản trị tạo / sửa bài Speaking (UC-SPK-05)."""
    class Meta:
        model = SpeakingExercise
        fields = ["title", "part", "topic", "prompt_text", "level", "status"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nhập tiêu đề bài luyện Speaking...",
            }),
            "part": forms.Select(attrs={"class": "form-control"}),
            "topic": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Hometown, Education, Technology, Environment...",
            }),
            "prompt_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Nội dung câu hỏi Speaking hoặc nội dung Cue Card Part 2...",
            }),
            "level": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class SpeakingSupportAdminForm(forms.ModelForm):
    """Form quản trị nội dung hỗ trợ Speaking (UC-SPK-06)."""
    class Meta:
        model = SpeakingSupport
        fields = ["idea_hint", "sample_answer", "suggested_vocabulary", "sample_audio_file"]
        widgets = {
            "idea_hint": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Gợi ý các ý tưởng trả lời (Idea hint)...",
            }),
            "sample_answer": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Bài mẫu tham khảo đạt Band 7.5 - 8.0+...",
            }),
            "suggested_vocabulary": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Từ vựng, cụm từ, collocations hoặc thành ngữ gợi ý...",
            }),
        }
