import uuid

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

User = get_user_model()


class RegisterForm(UserCreationForm):
    """UC-ACC-01: đăng ký theo Figma (Họ và tên, Email, Mật khẩu, Xác nhận mật khẩu).

    Mã đăng nhập (username) do hệ thống tự cấp dạng DOL-HV-00001. Tài khoản mới KHÔNG thuộc
    Group HOC_VIEN và không tự đăng nhập.
    """

    full_name = forms.CharField(label="Họ và tên", max_length=150,
                                widget=forms.TextInput(attrs={"placeholder": "Nhập họ và tên của bạn"}))
    email = forms.EmailField(label="Email", max_length=254,
                             widget=forms.EmailInput(attrs={"placeholder": "Nhập địa chỉ email"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    field_order = ["full_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password1"].help_text = "Sử dụng ít nhất 8 ký tự."
        self.fields["password1"].widget.attrs["placeholder"] = "Nhập mật khẩu"
        self.fields["password2"].label = "Xác nhận mật khẩu"
        self.fields["password2"].help_text = ""
        self.fields["password2"].widget.attrs["placeholder"] = "Nhập lại mật khẩu"

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email này đã được sử dụng. Hãy dùng email khác hoặc đăng nhập."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"].strip()  # lưu nguyên họ và tên
        user.last_name = ""
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.username = uuid.uuid4().hex[:30]  # tạm, đổi sang mã DOL-HV ngay sau khi có id
        if commit:
            with transaction.atomic():
                user.save()
                user.username = f"DOL-HV-{user.pk:05d}"
                user.save(update_fields=["username"])
        return user


class LoginForm(forms.Form):
    """UC-ACC-02: đăng nhập bằng tên đăng nhập hoặc email.

    Có phân biệt 3 lỗi theo đặc tả: không tìm thấy (E1), sai mật khẩu (E2), bị khóa (E3).
    """

    identifier = forms.CharField(
        label="Email", max_length=254,
        widget=forms.TextInput(attrs={"placeholder": "Nhập địa chỉ email", "autocomplete": "username"}),
        help_text="Có thể nhập mã đăng nhập (ví dụ DOL-HV-02468) thay cho email.",
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={"placeholder": "Nhập mật khẩu", "autocomplete": "current-password"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def _find_user(self, identifier):
        user = User.objects.filter(username=identifier).first()
        if user is None:
            user = User.objects.filter(username__iexact=identifier).first()
        if user is not None:
            return user
        by_email = list(User.objects.filter(email__iexact=identifier)[:2])
        if len(by_email) > 1:
            raise forms.ValidationError(
                "Email này gắn với nhiều tài khoản. Hãy đăng nhập bằng tên đăng nhập."
            )
        return by_email[0] if by_email else None

    def clean(self):
        cleaned = super().clean()
        identifier = (cleaned.get("identifier") or "").strip()
        password = cleaned.get("password")
        if not identifier or not password:
            return cleaned

        user = self._find_user(identifier)
        if user is None:
            raise forms.ValidationError(
                "Tên đăng nhập hoặc email không tồn tại. Vui lòng kiểm tra lại."
            )
        if not user.check_password(password):
            raise forms.ValidationError(
                "Tên đăng nhập/email hoặc mật khẩu không chính xác. Vui lòng nhập lại."
            )
        if not user.is_active:
            raise forms.ValidationError(
                "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."
            )
        authenticated = authenticate(
            self.request, username=user.get_username(), password=password
        )
        if authenticated is None:
            raise forms.ValidationError(
                "Tên đăng nhập/email hoặc mật khẩu không chính xác. Vui lòng nhập lại."
            )
        self.user = authenticated
        return cleaned


class ProfileForm(forms.ModelForm):
    """UC-ACC-05: chỉ cho sửa Họ và tên + Email. Không có trường quyền/khóa nên không tự cấp quyền được."""

    full_name = forms.CharField(label="Họ và tên", max_length=150)

    class Meta:
        model = User
        fields = ("email",)
        labels = {"email": "Email"}

    field_order = ["full_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["full_name"].initial = self.instance.get_full_name()

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        clash = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("Email này đã được tài khoản khác sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"].strip()
        user.last_name = ""
        if commit:
            user.save()
        return user
