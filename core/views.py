"""Trang chủ public; giới thiệu module mà không công khai dữ liệu bài luyện."""
from django.shortcuts import render
from django.urls import reverse
from accounts.permissions import is_hoc_vien
from management.permissions import can_enter_teacher_dashboard


def home(request):
    user = request.user
    student = is_hoc_vien(user)
    admin = can_enter_teacher_dashboard(user)
    modules = [
        {"name":"Listening", "caption":"Luyện nghe và kiểm tra kết quả", "path":reverse("listening:exercise_list"), "available": True, "icon":"🎧"},
        {"name":"Reading", "caption":"Luyện đọc với bộ câu hỏi", "path":reverse("reading:exercise_list"), "available": True, "icon":"📖"},
        {"name":"Writing", "caption":"Viết bài và nhận đánh giá tham khảo", "path":reverse("writing:prompt_list"), "available": True, "icon":"✍️"},
        {"name":"Speaking", "caption":"Luyện nói và nhận đánh giá từ AI", "path":reverse("speaking:exercise_list"), "available": True, "icon":"🎙️"},
        {"name":"Vocabulary", "caption":"Học và luyện từ vựng theo chủ đề", "path":reverse("vocabulary:topic_list"), "available": True, "icon":"📚"},
    ]
    admin_links = []
    if admin:
        if user.has_perm('auth.view_user') or user.has_perm('auth.change_user'):
            admin_links.append(('Quản lý tài khoản', reverse('accounts:manage_users')))
        if user.has_perm('vocabulary.view_topic') or user.has_perm('vocabulary.view_word'):
            admin_links.append(('Quản lý từ vựng', reverse('vocabulary:manage_topics')))
        if user.has_perm('writing.view_writingprompt'):
            admin_links.append(('Quản lý Writing', reverse('management:writing_prompt_list')))
        if user.has_perm('speaking.view_speakingexercise') or user.is_staff:
            admin_links.append(('Quản lý Speaking', reverse('management:speaking_exercise_list')))
        if user.is_staff:
            admin_links.append(('Quản lý Đánh giá / Góp ý', reverse('feedback:feedback_list')))
    return render(request, 'core/home.html', {
        'student':student, 'admin_user':admin, 'modules':modules, 'admin_links':admin_links, 'active_nav':'home',
    })
