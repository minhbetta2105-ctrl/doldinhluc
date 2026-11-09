"""
Submission Service dùng chung cho cả Reading và Listening theo UC-REA-03 và UC-LIS-03.
Thực hiện lưu Attempt và Answer trong một Atomic Transaction kèm Snapshot dữ liệu.
Hỗ trợ Idempotent qua submission_key (UUID v4) chống tạo lượt trùng khi gửi lặp.
"""

import uuid
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from receptive.models import Attempt, Answer, Exercise
from receptive.services.grading import grade_exercise_submission


def build_exercise_snapshot(exercise: Exercise) -> dict:
    """Tạo bản chụp JSON của Exercise tại thời điểm nộp bài."""
    return {
        "id": exercise.id,
        "title": exercise.title,
        "description": exercise.description,
        "topic": exercise.topic,
        "level": exercise.level,
        "skill": exercise.skill,
        "passage": exercise.passage,
        "audio_file": exercise.audio_file.url if exercise.audio_file else None,
    }


def build_question_snapshot(question) -> dict:
    """Tạo bản chụp JSON của Question và các Option đi kèm."""
    options_data = [
        {
            "id": opt.id,
            "option_key": opt.option_key,
            "option_text": opt.option_text,
            "order_no": opt.order_no,
        }
        for opt in question.options.all().order_by("order_no", "id")
    ]

    return {
        "id": question.id,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "correct_answers": question.correct_answers,
        "explanation": question.explanation,
        "order_no": question.order_no,
        "options": options_data,
    }


def submit_receptive_exercise(
    user,
    exercise: Exercise,
    answers_dict: dict,
    started_at=None,
    submission_key=None,
) -> tuple[Attempt, bool]:
    """Nộp bài và chấm điểm một Exercise.
    
    Args:
        user: User Django đang nộp bài
        exercise: Đối tượng Exercise
        answers_dict: dict mapping str(question_id) -> user_answer
        started_at: datetime thời điểm bắt đầu làm bài (nếu None sẽ lấy submitted_at)
        submission_key: UUIDv4 hoặc chuỗi UUID để chống gửi lặp. Nếu None sẽ tự sinh.

    Returns:
        (attempt, created): tuple đối tượng Attempt và boolean created.
    """
    if exercise.status != Exercise.Status.PUBLISHED:
        raise ValidationError("Bài luyện này hiện đang bị ẩn hoặc không còn khả dụng.")

    # Kiểm tra submission_key chống nộp lặp (Idempotency)
    if submission_key:
        existing_attempt = Attempt.objects.filter(submission_key=submission_key).first()
        if existing_attempt:
            return existing_attempt, False

    submitted_at = timezone.now()
    if not started_at or started_at > submitted_at:
        started_at = submitted_at

    # Chấm điểm bài làm
    grade_data = grade_exercise_submission(exercise, answers_dict)
    total_questions = grade_data["total_questions"]
    correct_count = grade_data["correct_count"]
    results = grade_data["results"]

    if total_questions < 1:
        raise ValidationError("Bài luyện chưa có câu hỏi nào được công bố để làm bài.")

    # Thực hiện lưu toàn bộ dữ liệu trong giao dịch nguyên tử
    with transaction.atomic():
        attempt = Attempt.objects.create(
            submission_key=submission_key or uuid.uuid4(),
            user=user,
            exercise=exercise,
            exercise_snapshot=build_exercise_snapshot(exercise),
            total_questions=total_questions,
            correct_answers=correct_count,
            started_at=started_at,
            submitted_at=submitted_at,
        )

        answer_objs = []
        for q_id, res in results.items():
            question = res["question"]
            answer_objs.append(
                Answer(
                    attempt=attempt,
                    question=question,
                    question_snapshot=build_question_snapshot(question),
                    user_answer=res["user_answer"],
                    is_correct=res["is_correct"],
                )
            )

        Answer.objects.bulk_create(answer_objs)

    return attempt, True
