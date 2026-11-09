from django import forms
from django.core.exceptions import ValidationError
from writing.models import WritingPrompt, WritingSupport
from speaking.models import SpeakingExercise, SpeakingSupport


class WritingPromptAdminForm(forms.ModelForm):
    """
    Form quản trị thêm mới và chỉnh sửa đề Writing (UC-WRI-05).
    Bảo vệ tính toàn vẹn dữ liệu: Khi đề đã có bài nộp của học viên,
    server tuyệt đối từ chối thay đổi các trường nội dung cốt lõi.
    """
    class Meta:
        model = WritingPrompt
        fields = ["title", "task_type", "prompt_text", "image_file", "level", "status"]
        labels = {
            "title": "Tiêu đề đề bài (Task Title)",
            "task_type": "Dạng bài (Task Type)",
            "level": "Trình độ (Level / Band Target)",
            "prompt_text": "Nội dung câu hỏi đề bài (Full Question)",
            "image_file": "Đường dẫn tư liệu hình ảnh / biểu đồ (Visual Material)",
            "status": "Trạng thái hiển thị (Visibility Status)",
        }
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Technology and Education - Opinion Essay",
                "required": True,
            }),
            "task_type": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "level": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "prompt_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Nhập nội dung câu hỏi đề thi IELTS Writing...",
                "required": True,
            }),
            "image_file": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Đường dẫn file ảnh (ví dụ: images/writing/task1_chart.png hoặc URL)",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields["status"].initial = WritingPrompt.Status.HIDDEN

        if self.instance and self.instance.pk and self.instance.submissions.exists():
            for field_name in ["title", "task_type", "prompt_text", "image_file", "level"]:
                self.fields[field_name].disabled = True
                self.fields[field_name].help_text = (
                    "Trường này đã bị khóa vì đề đã có bài nộp của học viên."
                )

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance

        if instance and instance.pk and instance.submissions.exists():
            orig = WritingPrompt.objects.filter(pk=instance.pk).values(
                "title", "task_type", "prompt_text", "image_file", "level"
            ).first()

            if orig:
                locked_fields = {
                    "title": "Tiêu đề",
                    "task_type": "Dạng bài",
                    "prompt_text": "Nội dung câu hỏi",
                    "image_file": "Hình ảnh tư liệu",
                    "level": "Trình độ",
                }
                violations = []
                for field, field_label in locked_fields.items():
                    if field in self.data:
                        raw_val = str(self.data[field]).strip()
                        orig_val = str(orig[field] or "").strip()
                        if raw_val != orig_val:
                            violations.append(field_label)
                    elif field in cleaned_data:
                        val = str(cleaned_data[field] or "").strip()
                        orig_val = str(orig[field] or "").strip()
                        if val != orig_val:
                            violations.append(field_label)

                if violations:
                    raise ValidationError(
                        f"Không thể thay đổi các trường cốt lõi ({', '.join(violations)}) "
                        f"của đề bài đã có bài nộp của học viên. "
                        f"Bạn chỉ có thể chuyển đổi Trạng thái hiển thị (Ẩn/Hiện). "
                        f"Để thay đổi nội dung, vui lòng tạo một đề luyện mới."
                    )

        return cleaned_data


class WritingSupportAdminForm(forms.ModelForm):
    """
    Form quản lý nội dung hỗ trợ Writing (UC-WRI-06):
    - Dàn ý gợi ý (outline_text)
    - Bài viết mẫu (sample_answer)
    - Từ vựng gợi ý (suggested_vocabulary)
    """
    class Meta:
        model = WritingSupport
        fields = ["outline_text", "sample_answer", "suggested_vocabulary"]
        labels = {
            "outline_text": "Gợi ý dàn ý (Essay Outline)",
            "sample_answer": "Bài viết mẫu (Sample Answer)",
            "suggested_vocabulary": "Từ vựng gợi ý (Suggested Vocabulary)",
        }
        widgets = {
            "outline_text": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 12,
                "placeholder": "1. Introduction...\n2. Body Paragraph 1...\n3. Body Paragraph 2...\n4. Conclusion...",
            }),
            "sample_answer": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 14,
                "placeholder": "Nhập bài viết mẫu chất lượng cao đạt band mục tiêu...",
            }),
            "suggested_vocabulary": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 10,
                "placeholder": "- infrastructure (n): cơ sở hạ tầng\n- allocate resources (v): phân bổ nguồn lực...",
            }),
        }


class SpeakingExerciseAdminForm(forms.ModelForm):
    """
    Form quản trị thêm mới và chỉnh sửa bài Speaking (UC-SPK-05).
    Bảo vệ tính toàn vẹn dữ liệu: Khi bài đã có bài nộp của học viên,
    server tuyệt đối từ chối thay đổi các trường nội dung cốt lõi.
    """
    class Meta:
        model = SpeakingExercise
        fields = ["title", "part", "topic", "prompt_text", "level", "status"]
        labels = {
            "title": "Tiêu đề bài Speaking",
            "part": "Phần thi (Part 1, 2, 3)",
            "topic": "Chủ đề (Topic)",
            "level": "Trình độ mục tiêu",
            "prompt_text": "Nội dung câu hỏi / Cue Card",
            "status": "Trạng thái hiển thị",
        }
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Describe a memorable journey you took...",
                "required": True,
            }),
            "part": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "topic": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Travel, Technology, Education, Music...",
                "required": True,
            }),
            "level": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "prompt_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Nhập nội dung câu hỏi hoặc Cue Card cho phần thi Speaking...",
                "required": True,
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields["status"].initial = SpeakingExercise.Status.HIDDEN

        if self.instance and self.instance.pk and self.instance.submissions.exists():
            for field_name in ["title", "part", "topic", "prompt_text", "level"]:
                self.fields[field_name].disabled = True
                self.fields[field_name].help_text = (
                    "Trường này đã bị khóa vì bài luyện đã có bài nộp của học viên."
                )

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance

        if instance and instance.pk and instance.submissions.exists():
            orig = SpeakingExercise.objects.filter(pk=instance.pk).values(
                "title", "part", "topic", "prompt_text", "level"
            ).first()

            if orig:
                locked_fields = {
                    "title": "Tiêu đề",
                    "part": "Phần thi",
                    "topic": "Chủ đề",
                    "prompt_text": "Nội dung câu hỏi",
                    "level": "Trình độ",
                }
                violations = []
                for field, field_label in locked_fields.items():
                    if field in self.data:
                        raw_val = str(self.data[field]).strip()
                        orig_val = str(orig[field] or "").strip()
                        if raw_val != orig_val:
                            violations.append(field_label)
                    elif field in cleaned_data:
                        val = str(cleaned_data[field] or "").strip()
                        orig_val = str(orig[field] or "").strip()
                        if val != orig_val:
                            violations.append(field_label)

                if violations:
                    raise ValidationError(
                        f"Không thể thay đổi các trường cốt lõi ({', '.join(violations)}) "
                        f"của bài luyện đã có bài nộp của học viên. "
                        f"Bạn chỉ có thể chuyển đổi Trạng thái hiển thị (Ẩn/Hiện)."
                    )

        return cleaned_data


class SpeakingSupportAdminForm(forms.ModelForm):
    """
    Form quản lý nội dung hỗ trợ Speaking (UC-SPK-06):
    - Gợi ý ý tưởng (idea_hint)
    - Bài mẫu tham khảo (sample_answer)
    - Từ vựng gợi ý (suggested_vocabulary)
    - Tệp âm thanh bài mẫu (sample_audio_file)
    """
    class Meta:
        model = SpeakingSupport
        fields = ["idea_hint", "sample_answer", "suggested_vocabulary", "sample_audio_file"]
        labels = {
            "idea_hint": "Gợi ý ý tưởng trả lời (Idea Hint)",
            "sample_answer": "Bài mẫu tham khảo (Sample Answer)",
            "suggested_vocabulary": "Từ vựng gợi ý (Suggested Vocabulary)",
            "sample_audio_file": "Tệp âm thanh mẫu (Sample Audio File)",
        }
        widgets = {
            "idea_hint": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 8,
                "placeholder": "Gợi ý các ý chính phát triển bài nói theo cấu trúc mở - thân - kết...",
            }),
            "sample_answer": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 12,
                "placeholder": "Nội dung bài nói mẫu chất lượng cao đạt Band 7.5 - 8.0+...",
            }),
            "suggested_vocabulary": forms.Textarea(attrs={
                "class": "form-control font-monospace",
                "rows": 8,
                "placeholder": "- picturesque scenery (n): phong cảnh đẹp như tranh\n- hospitable locals (adj): người dân hiếu khách...",
            }),
        }


# UI quản lý nghiệp vụ Reading/Listening dùng ModelForm, KHÔNG tạo model/bảng mới.
from receptive.models import Exercise as ReceptiveExercise, Question as ReceptiveQuestion, Option as ReceptiveOption


class ReceptiveExerciseForm(forms.ModelForm):
    class Meta:
        model = ReceptiveExercise
        fields = ['title', 'description', 'topic', 'level', 'passage', 'audio_file', 'status']
        widgets = {'description': forms.Textarea(attrs={'rows': 3}), 'passage': forms.Textarea(attrs={'rows': 9})}


class ReceptiveQuestionForm(forms.ModelForm):
    class Meta:
        model = ReceptiveQuestion
        fields = ['order_no', 'question_type', 'question_text', 'correct_answers', 'explanation', 'status']
        widgets = {'question_text': forms.Textarea(attrs={'rows': 3}), 'explanation': forms.Textarea(attrs={'rows': 3})}


class ReceptiveOptionForm(forms.ModelForm):
    class Meta:
        model = ReceptiveOption
        fields = ['order_no', 'option_key', 'option_text']
        widgets = {'option_text': forms.Textarea(attrs={'rows': 2})}
