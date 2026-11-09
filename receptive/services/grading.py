"""
Grading Engine dùng chung cho cả Reading và Listening theo UC-REA-04 và UC-LIS-04.
Chấm điểm theo đáp án hệ thống (correct_answers trong Question).
Không lộ Answer Key ra giao diện client trước khi nộp.
"""

import re


def normalize_answer_string(text: str) -> str:
    """Chuẩn hóa chuỗi trả lời: loại bỏ khoảng trắng thừa, đưa về chữ thường."""
    if text is None:
        return ""
    # Chuyển về chữ thường, thay thế nhiều khoảng trắng liên tiếp bằng 1 dấu cách đơn
    cleaned = re.sub(r"\s+", " ", str(text).strip().lower())
    return cleaned


def is_answer_correct(question_type: str, user_answer: str, correct_answers: list) -> bool:
    """Đối chiếu một câu trả lời của học viên với danh sách đáp án đúng.
    
    Quy tắc:
    - Nếu câu trả lời bỏ trống (rỗng): không tính đúng.
    - correct_answers là một list các phương án được chấp nhận (JSONB).
    - So sánh chuẩn hóa không phân biệt hoa thường và khoảng trắng dư thừa.
    """
    if not user_answer or not str(user_answer).strip():
        return False

    if not correct_answers or not isinstance(correct_answers, list):
        return False

    norm_user = normalize_answer_string(user_answer)
    norm_correct = [normalize_answer_string(ans) for ans in correct_answers]

    if question_type in ["MCQ", "TFNG", "YNNG", "MATCHING"]:
        # So khớp trực tiếp sau chuẩn hóa
        return norm_user in norm_correct
    elif question_type == "SHORT_TEXT":
        # Với điền từ: cho phép khớp với bất kỳ biến thể hợp lệ nào trong correct_answers
        return norm_user in norm_correct
    else:
        return norm_user in norm_correct


def grade_exercise_submission(exercise, answers_dict: dict) -> dict:
    """Chấm điểm toàn bộ bài làm của một Exercise.
    
    Args:
        exercise: Đối tượng Exercise
        answers_dict: dict mapping str(question_id) -> user_answer (str)
        
    Returns:
        dict chứa:
            - total_questions: tổng số câu hỏi được công bố của bài
            - correct_count: số câu đúng
            - results: dict mapping question_id -> {'is_correct': bool, 'user_answer': str}
    """
    questions = exercise.questions.filter(status="PUBLISHED").order_by("order_no", "id")
    total_questions = questions.count()

    correct_count = 0
    results = {}

    for question in questions:
        q_id_str = str(question.id)
        user_ans = answers_dict.get(q_id_str, "").strip() if answers_dict else ""
        correct = is_answer_correct(question.question_type, user_ans, question.correct_answers)

        if correct:
            correct_count += 1

        results[question.id] = {
            "question": question,
            "user_answer": user_ans,
            "is_correct": correct,
        }

    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "results": results,
    }
