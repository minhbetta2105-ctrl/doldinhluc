"""Business-admin view of student practice, based on existing submission tables.

Implements the GĐ2 system-wide progress actor without creating a Progress model.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from accounts.permissions import HOC_VIEN_GROUP
from .permissions import teacher_dashboard_required
from receptive.models import Attempt as ReceptiveAttempt
from writing.models import WritingSubmission
from speaking.models import SpeakingSubmission
from vocabulary.models import Attempt as VocabularyAttempt


def _require_student_view_perm(request):
    if not (request.user.is_superuser or request.user.has_perm('auth.view_user')):
        raise PermissionDenied('Tài khoản chưa được cấp quyền xem tiến độ học viên.')


@teacher_dashboard_required
def student_progress_list(request):
    """UC-PRG-02/03: current students or former students with recorded attempts."""
    _require_student_view_perm(request)
    User = get_user_model()
    q = request.GET.get('q', '').strip()
    student_ids = set(User.objects.filter(groups__name=HOC_VIEN_GROUP).values_list('pk', flat=True))
    for model in (ReceptiveAttempt, WritingSubmission, SpeakingSubmission, VocabularyAttempt):
        student_ids.update(model.objects.values_list('user_id', flat=True).distinct())
    users = User.objects.filter(pk__in=student_ids).order_by('username')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) |
                             Q(first_name__icontains=q) | Q(last_name__icontains=q))
    users = list(users[:100])  # bounded page; no performance surprises for a course project
    records = []
    active_ids = set(User.objects.filter(pk__in=[u.pk for u in users], groups__name=HOC_VIEN_GROUP).values_list('pk', flat=True))
    for user in users:
        counts = {
            'Reading': ReceptiveAttempt.objects.filter(user=user,exercise__skill='READING').count(),
            'Listening': ReceptiveAttempt.objects.filter(user=user,exercise__skill='LISTENING').count(),
            'Writing': WritingSubmission.objects.filter(user=user).count(),
            'Speaking': SpeakingSubmission.objects.filter(user=user).count(),
            'Vocabulary': VocabularyAttempt.objects.filter(user=user).count(),
        }
        records.append({'user': user, 'is_student': user.pk in active_ids,
                        'total': sum(counts.values()), 'counts': counts})
    return render(request, 'management/student_progress_list.html', {
        'records': records, 'q': q, 'active_nav': 'student_progress', 'count': len(records)
    })


@teacher_dashboard_required
def student_progress_detail(request, user_id):
    """UC-PRG-04/05: existing attempts and statuses (no change to grading)."""
    _require_student_view_perm(request)
    student = get_object_or_404(get_user_model(), pk=user_id)
    reading = ReceptiveAttempt.objects.filter(user=student, exercise__skill='READING').select_related('exercise').order_by('-submitted_at')[:10]
    listening = ReceptiveAttempt.objects.filter(user=student, exercise__skill='LISTENING').select_related('exercise').order_by('-submitted_at')[:10]
    writing = WritingSubmission.objects.filter(user=student).select_related('prompt').order_by('-submitted_at')[:10]
    speaking = SpeakingSubmission.objects.filter(user=student).select_related('exercise').order_by('-submitted_at')[:10]
    vocab = VocabularyAttempt.objects.filter(user=student).select_related('topic').order_by('-submitted_at')[:10]
    return render(request, 'management/student_progress_detail.html', {
        'student': student, 'reading_attempts': reading, 'listening_attempts': listening,
        'writing_attempts': writing, 'speaking_attempts': speaking, 'vocabulary_attempts': vocab,
        'active_nav': 'student_progress',
    })
