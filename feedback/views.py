import logging

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import hoc_vien_required, staff_required
from .forms import ServiceFeedbackForm
from .models import ServiceFeedback

logger = logging.getLogger(__name__)


@hoc_vien_required
def feedback_submit(request):
    """
    UC-FBK-01: Học viên gửi đánh giá / góp ý về trải nghiệm website.
    - Chỉ tài khoản đang hoạt động thuộc Group HOC_VIEN mới được gửi.
    - Không có chấm sao 1-5 sao (đúng use case và schema).
    - Lưu user, content, status mặc định VISIBLE, created_at.
    """
    if request.method == "POST":
        form = ServiceFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.status = ServiceFeedback.Status.VISIBLE
            feedback.save()
            messages.success(
                request,
                "Cảm ơn bạn đã gửi đánh giá! Ý kiến đóng góp quý báu của bạn giúp chúng tôi không ngừng hoàn thiện trải nghiệm luyện thi."
            )
            return redirect("feedback:feedback_submit")
        else:
            messages.error(request, "Vui lòng kiểm tra lại nội dung đánh giá.")
    else:
        form = ServiceFeedbackForm()

    # Lấy lịch sử các đánh giá gần nhất của chính học viên này để hiển thị tiện theo dõi
    user_feedbacks = ServiceFeedback.objects.filter(
        user=request.user
    ).order_by("-created_at")[:5]

    context = {
        "form": form,
        "user_feedbacks": user_feedbacks,
        "active_nav": "feedback",
    }
    return render(request, "feedback/feedback_form.html", context)


@staff_required
def feedback_list(request):
    """
    UC-FBK-02: Quản trị viên xem danh sách đánh giá / góp ý.
    - Hiển thị danh sách phản hồi, người gửi, nội dung, thời gian, trạng thái.
    - Lọc theo VISIBLE và HIDDEN (hoặc tất cả).
    - Mặc định chỉ lọc VISIBLE nếu chọn, hoặc xem toàn bộ.
    """
    status_filter = request.GET.get("status", "").strip().upper()
    search_q = request.GET.get("q", "").strip()

    qs = ServiceFeedback.objects.select_related("user").order_by("-created_at")

    if status_filter in [ServiceFeedback.Status.VISIBLE, ServiceFeedback.Status.HIDDEN]:
        qs = qs.filter(status=status_filter)

    if search_q:
        qs = qs.filter(
            Q(content__icontains=search_q) |
            Q(user__username__icontains=search_q) |
            Q(user__first_name__icontains=search_q) |
            Q(user__last_name__icontains=search_q)
        )

    total_count = ServiceFeedback.objects.count()
    visible_count = ServiceFeedback.objects.filter(status=ServiceFeedback.Status.VISIBLE).count()
    hidden_count = ServiceFeedback.objects.filter(status=ServiceFeedback.Status.HIDDEN).count()

    context = {
        "feedbacks": qs,
        "status_filter": status_filter,
        "search_q": search_q,
        "total_count": total_count,
        "visible_count": visible_count,
        "hidden_count": hidden_count,
        "active_nav": "feedback_manage",
    }
    return render(request, "feedback/feedback_list.html", context)


@require_POST
@staff_required
def feedback_status_toggle(request, pk):
    """
    UC-FBK-03: Ẩn hoặc Hiện lại đánh giá / góp ý.
    - Nếu đang VISIBLE -> chuyển sang HIDDEN (không xóa dữ liệu).
    - Nếu đang HIDDEN -> chuyển sang VISIBLE.
    """
    feedback = get_object_or_404(ServiceFeedback, pk=pk)
    if feedback.status == ServiceFeedback.Status.VISIBLE:
        feedback.status = ServiceFeedback.Status.HIDDEN
        msg = f"Đã ẩn đánh giá #{feedback.id} thành công (vẫn được lưu trong cơ sở dữ liệu)."
    else:
        feedback.status = ServiceFeedback.Status.VISIBLE
        msg = f"Đã hiển thị lại đánh giá #{feedback.id} thành công."

    feedback.save(update_fields=["status", "updated_at"])
    messages.success(request, msg)
    return redirect("feedback:feedback_list")


@require_POST
@staff_required
def feedback_delete(request, pk):
    """
    UC-FBK-03: Xóa đánh giá / góp ý (yêu cầu xác nhận từ hộp thoại trước khi xóa).
    """
    feedback = get_object_or_404(ServiceFeedback, pk=pk)
    feedback_id = feedback.id
    feedback.delete()
    messages.success(request, f"Đã xóa vĩnh viễn đánh giá #{feedback_id}.")
    return redirect("feedback:feedback_list")
