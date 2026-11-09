from django import forms
from django.core.exceptions import ValidationError
from .models import ServiceFeedback


class ServiceFeedbackForm(forms.ModelForm):
    """
    Form tiếp nhận phản hồi / góp ý của học viên về trải nghiệm website (UC-FBK-01).
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 6,
            "placeholder": "Hãy chia sẻ cảm nghĩ, đóng góp ý kiến hoặc báo cáo vấn đề bạn gặp phải khi sử dụng website...",
        }),
        required=True,
        error_messages={
            "required": "Vui lòng nhập nội dung đánh giá trước khi gửi.",
        }
    )

    class Meta:
        model = ServiceFeedback
        fields = ["content"]

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise ValidationError("Nội dung đánh giá không được để trống.")
        if len(content) < 5:
            raise ValidationError("Nội dung đánh giá quá ngắn. Vui lòng nhập tối thiểu 5 ký tự.")
        return content
