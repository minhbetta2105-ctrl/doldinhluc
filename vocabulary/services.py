"""Tạo bộ câu hỏi và chấm bài Vocabulary (không phụ thuộc request/template).

Đơn vị chấm (theo báo cáo):
  - MCQ  : 1 câu = 1 điểm (xen kẽ chọn nghĩa / điền từ)
  - MATCH: 1 cặp từ-nghĩa = 1 điểm
  - DRAG : 1 ô trống = 1 điểm
Bộ câu hỏi + đáp án được sinh ở máy chủ và giữ cố định trong session cho tới khi nộp.
"""
import random
import re
import uuid

from django.utils import timezone

BLANK = "_____"
BLANK_RE = re.compile(r"_{3,}")

MIN_WORDS = {"MCQ": 4, "MATCH": 4, "DRAG": 3}
MAX_ITEMS = {"MCQ": 10, "MATCH": 8, "DRAG": 8}


class NotEnoughData(Exception):
    """Chủ đề chưa đủ dữ liệu để tạo bài luyện đúng dạng."""


class InvalidSubmission(Exception):
    """Dữ liệu nộp sai cấu trúc."""


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()


# ---------------------------------------------------------------------------
# Lọc dữ liệu để không sinh câu hỏi mơ hồ
# ---------------------------------------------------------------------------
def _usable_words(words):
    """Từ có đủ từ + nghĩa, và nghĩa không trùng với từ khác (tránh đáp án mơ hồ)."""
    counts = {}
    for w in words:
        counts[normalize(w.meaning_vi)] = counts.get(normalize(w.meaning_vi), 0) + 1
    return [
        w for w in words
        if normalize(w.word) and normalize(w.meaning_vi) and counts[normalize(w.meaning_vi)] == 1
    ]


def _gap_candidates(words):
    """Từ có câu điền khuyết hợp lệ (đúng 1 ô trống) và đáp án không trùng nhau."""
    seen, result = set(), []
    for w in words:
        if not (w.gap_sentence and normalize(w.gap_answer)):
            continue
        parts = BLANK_RE.split(w.gap_sentence)
        if len(parts) != 2:
            continue
        key = normalize(w.gap_answer)
        if key in seen:
            continue
        seen.add(key)
        result.append((w, parts))
    return result


def _blank_sentence(word):
    """Trả về (câu có ô trống, đáp án) hoặc None."""
    if word.gap_sentence and normalize(word.gap_answer):
        parts = BLANK_RE.split(word.gap_sentence)
        if len(parts) == 2:
            return parts[0] + BLANK + parts[1], word.gap_answer.strip()
    if word.example_sentence:
        pattern = re.compile(re.escape(word.word.strip()), re.IGNORECASE)
        if pattern.search(word.example_sentence):
            return pattern.sub(BLANK, word.example_sentence, count=1), word.word.strip()
    return None


def _pick_distractors(candidates, exclude, k):
    """Chọn k phương án nhiễu khác nhau (so sánh sau chuẩn hóa), khác đáp án đúng."""
    pool, seen = [], {normalize(exclude)}
    for c in candidates:
        n = normalize(c)
        if n and n not in seen:
            seen.add(n)
            pool.append(c)
    if len(pool) < k:
        return None
    return random.sample(pool, k)


# ---------------------------------------------------------------------------
# Tạo bài
# ---------------------------------------------------------------------------
def available_types(words):
    """Dạng bài nào của chủ đề này đủ dữ liệu: {'MCQ': True, ...}."""
    usable = _usable_words(words)
    return {
        "MCQ": len(usable) >= MIN_WORDS["MCQ"],
        "MATCH": len(usable) >= MIN_WORDS["MATCH"],
        "DRAG": len(_gap_candidates(words)) >= MIN_WORDS["DRAG"],
    }


def build_run(topic, exercise_type, user_id):
    """Sinh một 'run' (lưu trong session) cho chủ đề + dạng bài."""
    if exercise_type not in MIN_WORDS:
        raise NotEnoughData("Dạng bài không hợp lệ.")
    words = list(topic.words.filter(status="PUBLISHED"))

    run = {
        "key": str(uuid.uuid4()),
        "user_id": user_id,
        "topic_id": topic.pk,
        "exercise_type": exercise_type,
        "started_at": timezone.now().isoformat(),
        "topic_snapshot": {"name": topic.name, "level": topic.level},
        "questions": [],
        "bank": [],
    }

    if exercise_type == "MCQ":
        pool = _usable_words(words)
        if len(pool) < MIN_WORDS["MCQ"]:
            raise NotEnoughData()
        random.shuffle(pool)
        chosen = pool[: MAX_ITEMS["MCQ"]]
        all_meanings = [w.meaning_vi.strip() for w in pool]
        all_words = [w.word.strip() for w in pool]
        for idx, w in enumerate(chosen):
            question = None
            blanked = _blank_sentence(w) if idx % 2 == 1 else None
            if blanked:
                sentence, answer = blanked
                wrong = _pick_distractors(all_words, answer, 3)
                if wrong:
                    options = [answer] + wrong
                    random.shuffle(options)
                    question = {"type": "MCQ_WORD", "prompt": sentence, "phonetic": "",
                                "options": options, "answer": answer}
            if question is None:
                answer = w.meaning_vi.strip()
                wrong = _pick_distractors(all_meanings, answer, 3)
                if not wrong:
                    continue
                options = [answer] + wrong
                random.shuffle(options)
                question = {"type": "MCQ_MEANING", "prompt": w.word.strip(),
                            "phonetic": w.phonetic, "options": options, "answer": answer}
            question["word_id"] = w.pk
            run["questions"].append(question)

    elif exercise_type == "MATCH":
        pool = _usable_words(words)
        if len(pool) < MIN_WORDS["MATCH"]:
            raise NotEnoughData()
        random.shuffle(pool)
        chosen = pool[: MAX_ITEMS["MATCH"]]
        meanings = [w.meaning_vi.strip() for w in chosen]
        random.shuffle(meanings)
        for w in chosen:
            run["questions"].append({
                "word_id": w.pk, "type": "MATCH", "prompt": w.word.strip(),
                "phonetic": w.phonetic, "options": meanings,
                "answer": w.meaning_vi.strip(),
            })

    else:  # DRAG
        cands = _gap_candidates(words)
        if len(cands) < MIN_WORDS["DRAG"]:
            raise NotEnoughData()
        random.shuffle(cands)
        for w, parts in cands[: MAX_ITEMS["DRAG"]]:
            run["questions"].append({
                "word_id": w.pk, "type": "DRAG", "before": parts[0], "after": parts[1],
                "answer": w.gap_answer.strip(),
            })
        run["bank"] = [q["answer"] for q in run["questions"]]
        random.shuffle(run["bank"])

    if len(run["questions"]) < MIN_WORDS[exercise_type]:
        raise NotEnoughData()
    for no, q in enumerate(run["questions"], start=1):
        q["no"] = no
    return run


def public_questions(run):
    """Bản gửi ra trình duyệt: KHÔNG chứa đáp án đúng."""
    return [{k: v for k, v in q.items() if k != "answer"} for q in run["questions"]]


# ---------------------------------------------------------------------------
# Chấm bài
# ---------------------------------------------------------------------------
def grade(run, post):
    """Đối chiếu câu trả lời (POST: q1, q2, ...) với đáp án của run. Bỏ trống = sai."""
    if run["exercise_type"] == "DRAG":
        allowed = {normalize(x) for x in run["bank"]}
    results = []
    for q in run["questions"]:
        user_answer = (post.get(f"q{q['no']}") or "").strip()
        if user_answer:
            if run["exercise_type"] == "DRAG":
                valid = normalize(user_answer) in allowed
            else:
                valid = normalize(user_answer) in {normalize(o) for o in q["options"]}
            if not valid:
                raise InvalidSubmission("Đáp án không thuộc bộ câu hỏi.")
        results.append({
            "question": q,
            "user_answer": user_answer,
            "is_correct": bool(user_answer) and normalize(user_answer) == normalize(q["answer"]),
        })
    return results
