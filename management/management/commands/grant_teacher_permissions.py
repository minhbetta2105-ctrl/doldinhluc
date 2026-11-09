"""Grant business admin (teacher) permissions to an EXISTING staff account.

No role or database schema changes. Must be invoked explicitly by project owner:
    python manage.py grant_teacher_permissions <username>
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError

# Business content management and observation only. Never modify user/groups.
ALLOWED = {
    'writing': {'writingprompt': ('view', 'add', 'change'), 'writingsupport': ('view', 'add', 'change')},
    'speaking': {'speakingexercise': ('view', 'add', 'change'), 'speakingsupport': ('view', 'add', 'change')},
    'receptive': {'exercise': ('view', 'add', 'change'), 'question': ('view', 'add', 'change'), 'option': ('view', 'add', 'change')},
    'reading': {'readingexercise': ('view',)},
    'listening': {'listeningexercise': ('view',)},
    'vocabulary': {'topic': ('view', 'add', 'change', 'delete'), 'word': ('view', 'add', 'change', 'delete')},
    'feedback': {'servicefeedback': ('view', 'change', 'delete')},
    'auth': {'user': ('view',)},
}

class Command(BaseCommand):
    help = 'Grant management permissions to an existing teacher/staff, not lock/grant-user rights.'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Exact username of an existing staff user')

    def handle(self, *args, **options):
        username = options['username']
        user = get_user_model().objects.filter(username=username).first()
        if user is None:
            raise CommandError('Tài khoản không tồn tại. Tạo tài khoản trước.')
        if not user.is_staff or not user.is_active or user.is_superuser:
            raise CommandError('Chỉ áp dụng cho tài khoản giáo viên is_staff=True, đang hoạt động, không phải superuser.')
        grants = []
        for app, models in ALLOWED.items():
            for model, actions in models.items():
                for action in actions:
                    codename = f'{action}_{model}'
                    permission = Permission.objects.filter(content_type__app_label=app, codename=codename).first()
                    if permission is None:
                        raise CommandError(f'Thiếu Permission {app}.{codename}; kiểm tra migrate.')
                    grants.append(permission)
        user.user_permissions.add(*grants)
        self.stdout.write(self.style.SUCCESS(
            f'Đã cấp {len(grants)} quyền quản lý nội dung cho {username}. '
            'Không cấp quyền khóa tài khoản, quản lý Group hoặc cấp/thu hồi HOC_VIEN.'
        ))
