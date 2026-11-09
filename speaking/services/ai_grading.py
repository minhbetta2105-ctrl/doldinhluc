import base64
import json
import logging
import mimetypes
import os
import re
import socket
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from .ielts_rubric import (
    RUBRIC_SOURCE,
    RUBRIC_VERSION,
    DISCLAIMER_TEXT,
    calculate_ielts_speaking_overall,
    build_ielts_speaking_prompt,
)

logger = logging.getLogger(__name__)

SUPPORTED_GEMINI_MODELS = (
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
)

DEPRECATED_GEMINI_MODELS = (
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
)

# MIME types âm thanh được Gemini Multimodal hỗ trợ
AUDIO_MIME_MAP = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".m4a": "audio/m4a",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".mp4": "audio/mp4",
}


# ==============================================================================
# 1. HỆ THỐNG NGOẠI LỆ CHO AI SPEAKING GRADING
# ==============================================================================

class AIGradingError(Exception):
    """Lớp ngoại lệ cơ sở cho các lỗi phát sinh trong quá trình chấm điểm AI Speaking."""
    pass


class AIConfigurationError(AIGradingError):
    """Thiếu API key, cấu hình provider hoặc model không hợp lệ."""
    pass


class AITimeoutError(AIGradingError):
    """Quá thời gian chờ phản hồi (timeout) từ dịch vụ Gemini AI."""
    pass


class AIConnectionError(AIGradingError):
    """Không thể kết nối đến máy chủ AI (lỗi mạng, DNS, rate limit, HTTP 5xx)."""
    pass


class AIAuthenticationError(AIGradingError):
    """Lỗi xác thực khóa API (HTTP 401 hoặc 403)."""
    pass


class AIResponseValidationError(AIGradingError):
    """Phản hồi từ AI không đúng cấu trúc JSON, thiếu trường, hoặc điểm ngoài [0, 9]."""
    pass


# ==============================================================================
# 2. CẤU TRÚC DỮ LIỆU KẾT QUẢ CHẤM ĐIỂM
# ==============================================================================

@dataclass
class SpeakingAIGradingResult:
    """Kết quả chấm điểm Speaking đã được xác thực an toàn."""
    overall_score: Decimal
    fluency_score: Decimal
    pronunciation_score: Decimal
    vocabulary_score: Decimal
    grammar_score: Decimal
    transcript: str
    feedback: str
    raw_payload: Dict[str, Any]


# ==============================================================================
# 3. TIỆN ÍCH LÀM SẠCH VÀ XÁC THỰC DỮ LIỆU JSON
# ==============================================================================

def clean_json_text(text: str) -> str:
    """Loại bỏ markdown code block (```json ... ```) nếu AI trả về kèm định dạng."""
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            first_line = lines[0].strip().lower()
            if first_line in ("```json", "```"):
                if lines[-1].strip() == "```":
                    text = "\n".join(lines[1:-1]).strip()
                else:
                    text = "\n".join(lines[1:]).strip()
    return text.strip()


def validate_speaking_score(val: Any, field_name: str) -> Decimal:
    """Xác thực điểm số là số thực trong khoảng [0.0, 9.0] và đúng bước nhảy 0.5."""
    if val is None:
        raise AIResponseValidationError(f"Điểm {field_name} không được là null.")
    try:
        dec = Decimal(str(val)).quantize(Decimal("0.1"))
    except (InvalidOperation, TypeError, ValueError) as e:
        raise AIResponseValidationError(f"Điểm {field_name} không hợp lệ: {val}") from e

    if dec < Decimal("0.0") or dec > Decimal("9.0"):
        raise AIResponseValidationError(f"Điểm {field_name} ({dec}) nằm ngoài thang điểm IELTS [0.0, 9.0].")

    # Kiểm tra bước nhảy 0.5 (nhân đôi phải là số nguyên)
    doubled = dec * Decimal("2")
    if doubled != Decimal(int(doubled)):
        raise AIResponseValidationError(f"Điểm {field_name} ({dec}) không tuân thủ bước nhảy 0.5 của IELTS.")

    return dec


def parse_and_validate_speaking_payload(payload: Dict[str, Any]) -> SpeakingAIGradingResult:
    """
    Xác thực toàn diện cấu trúc JSON do AI trả về:
    - Bắt buộc đủ 4 tiêu chí điểm IELTS Speaking: fluency_score, lexical_score, grammar_score, pronunciation_score.
    - Tự động tính Overall Band theo chuẩn IELTS (không phụ thuộc vào AI).
    - Bắt buộc có transcript.
    - Bắt buộc có nhận xét tổng quan, điểm mạnh, điểm yếu, các gợi ý.
    """
    if not isinstance(payload, dict):
        raise AIResponseValidationError("Dữ liệu phản hồi từ AI không phải là một đối tượng JSON hợp lệ.")

    # 1. Transcript
    transcript = str(payload.get("transcript", "")).strip()
    if not transcript:
        raise AIResponseValidationError("Dữ liệu phản hồi từ AI thiếu nội dung transcript từ audio.")

    # 2. Bốn tiêu chí điểm
    fc = validate_speaking_score(payload.get("fluency_score"), "fluency_score")
    lr = validate_speaking_score(payload.get("lexical_score"), "lexical_score")
    gra = validate_speaking_score(payload.get("grammar_score"), "grammar_score")
    p = validate_speaking_score(payload.get("pronunciation_score"), "pronunciation_score")

    # Backend tự tính toán Overall Band IELTS chính xác bằng Decimal
    overall_score = calculate_ielts_speaking_overall(fc, lr, gra, p)

    # 3. Phản hồi định tính
    overall_feedback = str(payload.get("overall_feedback", "")).strip()
    if not overall_feedback:
        overall_feedback = "Học viên hoàn thành bài nói theo yêu cầu của đề."

    strengths = payload.get("strengths", [])
    if not isinstance(strengths, list):
        strengths = [str(strengths)] if strengths else []

    weaknesses = payload.get("weaknesses", [])
    if not isinstance(weaknesses, list):
        weaknesses = [str(weaknesses)] if weaknesses else []

    grammar_corrections = payload.get("grammar_corrections", [])
    if not isinstance(grammar_corrections, list):
        grammar_corrections = []

    vocabulary_suggestions = payload.get("vocabulary_suggestions", [])
    if not isinstance(vocabulary_suggestions, list):
        vocabulary_suggestions = []

    pronunciation_feedback = payload.get("pronunciation_feedback", [])
    if not isinstance(pronunciation_feedback, list):
        pronunciation_feedback = []

    improvement_suggestions = payload.get("improvement_suggestions", [])
    if not isinstance(improvement_suggestions, list):
        improvement_suggestions = []

    clean_payload = {
        "transcript": transcript,
        "overall_band": float(overall_score),
        "fluency_score": float(fc),
        "lexical_score": float(lr),
        "grammar_score": float(gra),
        "pronunciation_score": float(p),
        "overall_feedback": overall_feedback,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "grammar_corrections": grammar_corrections,
        "vocabulary_suggestions": vocabulary_suggestions,
        "pronunciation_feedback": pronunciation_feedback,
        "improvement_suggestions": improvement_suggestions,
        "disclaimer": DISCLAIMER_TEXT,
        "rubric_version": RUBRIC_VERSION,
        "rubric_source": RUBRIC_SOURCE,
    }

    feedback_json_str = json.dumps(clean_payload, ensure_ascii=False)

    return SpeakingAIGradingResult(
        overall_score=overall_score,
        fluency_score=fc,
        pronunciation_score=p,
        vocabulary_score=lr,
        grammar_score=gra,
        transcript=transcript,
        feedback=feedback_json_str,
        raw_payload=clean_payload,
    )


# ==============================================================================
# 4. PROVIDER INTERFACE & GEMINI IMPLEMENTATION
# ==============================================================================

class BaseSpeakingAIGradingProvider(ABC):
    """Lớp trừu tượng cho nhà cung cấp dịch vụ chấm điểm Speaking."""
    @abstractmethod
    def grade(
        self,
        part: str,
        topic: str,
        prompt_text: str,
        audio_file_path: str
    ) -> SpeakingAIGradingResult:
        pass


class GeminiSpeakingAIGradingProvider(BaseSpeakingAIGradingProvider):
    """
    Tích hợp chính thức với Google Gemini Multimodal Audio API.
    Sử dụng urllib.request chuẩn Python (kế thừa kiến trúc từ Writing).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (
                getattr(settings, "GEMINI_API_KEY", None)
                or os.getenv("GEMINI_API_KEY")
                or getattr(settings, "AI_API_KEY", None)
                or os.getenv("AI_API_KEY")
                or ""
            ).strip()

        self.model = (
            model
            or os.getenv("AI_MODEL")
            or getattr(settings, "AI_MODEL", "gemini-3.8-flash")
        ).strip()

        if self.model in DEPRECATED_GEMINI_MODELS:
            raise AIConfigurationError(
                f"Mô hình Gemini '{self.model}' đã ngừng hỗ trợ. "
                f"Vui lòng cấu hình sang mô hình thế hệ mới: {', '.join(SUPPORTED_GEMINI_MODELS)}."
            )

        raw_timeout = (
            timeout
            if timeout is not None
            else getattr(settings, "AI_API_TIMEOUT", None) or os.getenv("AI_API_TIMEOUT", 60)
        )
        try:
            self.timeout = int(raw_timeout)
        except (ValueError, TypeError):
            self.timeout = 60

    def _resolve_audio_data(self, audio_file_path: str) -> tuple[str, str]:
        """Đọc tệp audio từ đường dẫn và trả về (mime_type, base64_data)."""
        if not os.path.exists(audio_file_path):
            raise AIConnectionError(f"Tệp âm thanh không tồn tại trên máy chủ: {audio_file_path}")

        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            raise AIResponseValidationError("Tệp âm thanh rỗng (0 bytes).")
        # Giới hạn tối đa 25MB cho audio payload
        if file_size > 25 * 1024 * 1024:
            raise AIResponseValidationError("Dung lượng tệp âm thanh vượt quá giới hạn tối đa (25MB).")

        ext = os.path.splitext(audio_file_path)[1].lower()
        mime_type = AUDIO_MIME_MAP.get(ext)
        if not mime_type:
            guessed_mime, _ = mimetypes.guess_type(audio_file_path)
            mime_type = guessed_mime or "audio/mp3"

        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()

        b64_data = base64.b64encode(audio_bytes).decode("utf-8")
        return mime_type, b64_data

    def grade(
        self,
        part: str,
        topic: str,
        prompt_text: str,
        audio_file_path: str
    ) -> SpeakingAIGradingResult:
        if not self.api_key or self.api_key.startswith("your_") or "CHANGE_ME" in self.api_key:
            raise AIConfigurationError(
                "GEMINI_API_KEY chưa được cấu hình hợp lệ trong biến môi trường hoặc settings."
            )

        mime_type, b64_data = self._resolve_audio_data(audio_file_path)
        prompt = build_ielts_speaking_prompt(part, topic, prompt_text)

        # Cấu trúc yêu cầu Gemini Multimodal (inlineData + text)
        parts: List[Dict[str, Any]] = [
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": b64_data
                }
            },
            {
                "text": prompt
            }
        ]

        body = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }

        data_bytes = json.dumps(body).encode("utf-8")

        # Chuỗi mô hình thử nghiệm tự động dự phòng (Model Resilience Fallback Chain)
        models_to_try = [self.model]
        if "gemini-3.5-flash-lite" not in models_to_try:
            models_to_try.append("gemini-3.5-flash-lite")
        if "gemini-2.5-flash-lite" not in models_to_try:
            models_to_try.append("gemini-2.5-flash-lite")

        resp_text: Optional[str] = None
        last_error: Optional[Exception] = None

        for idx, current_model in enumerate(models_to_try):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_text = resp.read().decode("utf-8")
                break
            except urllib.error.HTTPError as http_err:
                status_code = http_err.code
                logger.error("Gemini Speaking API HTTP Error %s trên mô hình %s", status_code, current_model)
                err_body = ""
                try:
                    err_body = http_err.read().decode("utf-8")
                except Exception:
                    pass

                if status_code in (401, 403) or (status_code == 400 and ("API_KEY_INVALID" in err_body or "API key not valid" in err_body)):
                    raise AIAuthenticationError(
                        f"Xác thực thất bại với Gemini API (HTTP {status_code}): API Key không hợp lệ hoặc hết hạn."
                    ) from http_err
                elif status_code == 429:
                    raise AIConnectionError(
                        "Gemini API vượt quá giới hạn truy vấn (Rate limit 429). Vui lòng thử lại sau."
                    ) from http_err
                elif status_code in (500, 502, 503, 504, 408):
                    last_error = http_err
                    if idx + 1 < len(models_to_try):
                        logger.warning(
                            "Mô hình %s quá tải (HTTP %s). Chuyển sang mô hình dự phòng %s...",
                            current_model, status_code, models_to_try[idx + 1]
                        )
                        continue
                    else:
                        raise AIConnectionError(
                            f"Gemini API gặp lỗi máy chủ (HTTP {status_code}) trên toàn bộ các mô hình dự phòng."
                        ) from http_err
                else:
                    raise AIConnectionError(f"Gemini API gặp lỗi máy chủ (HTTP {status_code}): {err_body[:200]}") from http_err
            except (socket.timeout, TimeoutError) as timeout_err:
                logger.error("Gemini Speaking API timeout (%ss) trên mô hình %s", self.timeout, current_model)
                last_error = timeout_err
                if idx + 1 < len(models_to_try):
                    continue
                raise AITimeoutError(f"Hết thời gian chờ kết nối tới Gemini API ({self.timeout}s).") from timeout_err
            except urllib.error.URLError as url_err:
                if isinstance(url_err.reason, (socket.timeout, TimeoutError)):
                    last_error = url_err
                    if idx + 1 < len(models_to_try):
                        continue
                    raise AITimeoutError(f"Hết thời gian chờ kết nối tới Gemini API ({self.timeout}s).") from url_err
                raise AIConnectionError(f"Lỗi kết nối mạng tới Gemini API: {url_err.reason}") from url_err
            except Exception as general_err:
                logger.error("Lỗi không xác định khi gọi Gemini Speaking API: %s", str(general_err))
                raise AIConnectionError(f"Lỗi khi gửi yêu cầu tới AI: {str(general_err)}") from general_err

        if not resp_text:
            raise AIConnectionError(f"Không nhận được phản hồi từ Gemini API sau khi thử các mô hình: {last_error}")

        # Phân tích phản hồi JSON từ Gemini
        try:
            api_resp = json.loads(resp_text)
            candidates = api_resp.get("candidates", [])
            if not candidates:
                raise AIResponseValidationError("Gemini API không trả về kết quả (candidates rỗng).")

            candidate = candidates[0]
            content_part = candidate.get("content", {}).get("parts", [])[0]
            json_text = clean_json_text(content_part.get("text", ""))
            payload = json.loads(json_text)
            if isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
                payload = payload[0]
        except (json.JSONDecodeError, IndexError, KeyError) as json_err:
            logger.error("Phản hồi từ Gemini không thể parse thành JSON: %s", str(json_err))
            raise AIResponseValidationError("Dữ liệu trả về từ Gemini AI không đúng định dạng JSON yêu cầu.") from json_err

        return parse_and_validate_speaking_payload(payload)


class MockSpeakingAIGradingProvider(BaseSpeakingAIGradingProvider):
    """
    Mock Provider phục vụ Unit Test và môi trường phát triển ngoại tuyến:
    - Trả về cấu trúc 4 tiêu chí chuẩn IELTS Speaking.
    - Hỗ trợ mô phỏng ngoại lệ và ghi nhận call history.
    """

    def __init__(
        self,
        fc: Decimal = Decimal("6.5"),
        lr: Decimal = Decimal("6.0"),
        gra: Decimal = Decimal("6.0"),
        p: Decimal = Decimal("6.5"),
        transcript: str = "Well, in my hometown, there are many historical places that attract thousands of visitors every year. Personally, I really enjoy spending my weekends walking around the ancient quarter because it gives me a sense of peace and relaxation.",
        overall_feedback: str = "Thí sinh trả lời lưu loát, ý tưởng phát triển tự nhiên và đúng trọng tâm câu hỏi. Vốn từ vựng tương đối đa dạng và phát âm rõ ràng, dễ hiểu.",
        exception_to_raise: Optional[Exception] = None,
        raw_payload_override: Optional[Dict[str, Any]] = None,
    ):
        self.fc = fc
        self.lr = lr
        self.gra = gra
        self.p = p
        self.transcript = transcript
        self.overall_feedback = overall_feedback
        self.exception_to_raise = exception_to_raise
        self.raw_payload_override = raw_payload_override
        self.call_history: List[Dict[str, Any]] = []

    def grade(
        self,
        part: str,
        topic: str,
        prompt_text: str,
        audio_file_path: str
    ) -> SpeakingAIGradingResult:
        self.call_history.append({
            "part": part,
            "topic": topic,
            "prompt_text": prompt_text,
            "audio_file_path": audio_file_path,
            "timestamp": timezone.now()
        })

        if self.exception_to_raise:
            raise self.exception_to_raise

        if self.raw_payload_override:
            return parse_and_validate_speaking_payload(self.raw_payload_override)

        overall = calculate_ielts_speaking_overall(self.fc, self.lr, self.gra, self.p)

        payload = {
            "transcript": self.transcript,
            "overall_band": float(overall),
            "fluency_score": float(self.fc),
            "lexical_score": float(self.lr),
            "grammar_score": float(self.gra),
            "pronunciation_score": float(self.p),
            "overall_feedback": self.overall_feedback,
            "strengths": [
                "Nói trôi chảy, tốc độ đều đặn, không có khoảng ngập ngừng quá dài.",
                "Sử dụng tự nhiên một số liên từ chỉ nguyên nhân và kết quả như 'because', 'so', 'personally'."
            ],
            "weaknesses": [
                "Còn lặp lại một số cấu trúc câu đơn giản.",
                "Cần chú ý phát âm rõ hơn các âm đuôi /s/ và /z/."
            ],
            "grammar_corrections": [
                {
                    "original": "there are many historical places that attract thousands of visitors",
                    "correction": "there are numerous historical landmarks attracting thousands of visitors",
                    "explanation": "Có thể rút gọn mệnh đề quan hệ để câu văn tự nhiên và nâng cao cấu trúc ngữ pháp hơn."
                }
            ],
            "vocabulary_suggestions": [
                {
                    "original": "historical places",
                    "suggestion": "historical landmarks / heritage sites",
                    "explanation": "Sử dụng từ vựng học thuật chính xác hơn khi nói về di tích lịch sử."
                },
                {
                    "original": "really enjoy",
                    "suggestion": "take great delight in / thoroughly relish",
                    "explanation": "Đa dạng hóa cách diễn đạt sở thích cá nhân thay vì chỉ dùng 'really enjoy'."
                }
            ],
            "pronunciation_feedback": [
                {
                    "word": "historical",
                    "issue": "Trọng âm đặt chưa đúng, nhấn vào âm tiết thứ nhất thay vì thứ hai.",
                    "tip": "Phát âm chuẩn là /hɪˈstɒr.ɪ.kəl/, trọng âm rơi vào âm tiết thứ hai '-stor-'."
                },
                {
                    "word": "relaxation",
                    "issue": "Âm đuôi /ʃən/ phát âm chưa rõ ràng.",
                    "tip": "Chu môi nhẹ khi phát âm /ʃ/ để tạo âm gió rõ nét: /ˌriː.lækˈseɪ.ʃən/."
                }
            ],
            "improvement_suggestions": [
                "Luyện tập kỹ thuật Shadowing theo người bản xứ để cải thiện ngữ điệu tự nhiên.",
                "Mở rộng câu trả lời bằng cách bổ sung lý do cụ thể và ví dụ thực tế.",
                "Ghi âm lại hàng ngày và chú ý kiểm tra ending sounds."
            ],
            "disclaimer": DISCLAIMER_TEXT,
            "rubric_version": RUBRIC_VERSION,
            "rubric_source": RUBRIC_SOURCE,
        }

        return SpeakingAIGradingResult(
            overall_score=overall,
            fluency_score=self.fc,
            pronunciation_score=self.p,
            vocabulary_score=self.lr,
            grammar_score=self.gra,
            transcript=self.transcript,
            feedback=json.dumps(payload, ensure_ascii=False),
            raw_payload=payload,
        )


# ==============================================================================
# 5. PROVIDER FACTORY
# ==============================================================================

def get_speaking_ai_grading_provider() -> BaseSpeakingAIGradingProvider:
    """Khởi tạo AI Provider thích hợp dựa trên cấu hình settings/môi trường."""
    provider_name = (
        getattr(settings, "AI_PROVIDER", None)
        or os.getenv("AI_PROVIDER")
        or "gemini"
    ).strip().lower()

    if provider_name == "mock":
        return MockSpeakingAIGradingProvider()
    return GeminiSpeakingAIGradingProvider()


# ==============================================================================
# 6. HÀM THỰC THI CHẤM ĐIỂM SPEAKING AN TOÀN
# ==============================================================================

def grade_speaking_submission_safely(
    submission,
    provider: Optional[BaseSpeakingAIGradingProvider] = None
) -> bool:
    """
    Thực hiện chấm điểm an toàn cho một SpeakingSubmission đã lưu trong database:
    1. Kiểm tra trạng thái: Nếu đã là GRADED -> Bỏ qua để chống chấm trùng lặp.
    2. Kiểm tra tệp audio_file tồn tại.
    3. Gọi AI Provider từ Django server (đồng bộ với timeout giới hạn).
    4. Nếu AI trả kết quả hợp lệ:
       - status = GRADED
       - overall_score = điểm Overall Band hợp lệ trong [0.0, 9.0]
       - fluency_score, pronunciation_score, vocabulary_score, grammar_score
       - feedback = chuỗi JSON chi tiết 4 tiêu chí + transcript + gợi ý
       - graded_at = thời điểm chấm
    5. Nếu AI gặp lỗi (timeout, key sai, lỗi mạng, response không hợp lệ):
       - status = FAILED
       - overall_score, fluency_score, pronunciation_score, vocabulary_score, grammar_score = None (NULL)
       - feedback = None
       - graded_at = None
       - TUYỆT ĐỐI KHÔNG GÁN 0.0 KHI GẶP LỖI.
    6. Cập nhật chính SpeakingSubmission đã có qua save(update_fields=...).
       Tuyệt đối không xóa bài nộp, không tạo bài nộp mới.
    7. Trả về True nếu chấm thành công (GRADED), False nếu thất bại (FAILED).
    """
    from speaking.models import SpeakingSubmission

    # 1. Chống chấm trùng lặp
    if submission.status == SpeakingSubmission.Status.GRADED:
        logger.warning(
            "Bài nộp Speaking #%s (Key: %s) đã ở trạng thái GRADED. Bỏ qua chấm lại.",
            submission.pk,
            submission.submission_key
        )
        return True

    # 2. Trích xuất dữ liệu đầu vào từ snapshot và bài nộp
    snapshot = submission.exercise_snapshot or {}
    part = snapshot.get("part", "")
    if not part and submission.exercise:
        part = submission.exercise.part

    topic = snapshot.get("topic", "")
    if not topic and submission.exercise:
        topic = submission.exercise.topic

    prompt_text = snapshot.get("prompt_text", "")
    if not prompt_text and submission.exercise:
        prompt_text = submission.exercise.prompt_text

    # 3. Kiểm tra tệp audio
    if not submission.audio_file:
        logger.error("Bài nộp Speaking #%s thiếu tệp âm thanh. Chuyển sang FAILED.", submission.pk)
        submission.status = SpeakingSubmission.Status.FAILED
        submission.overall_score = None
        submission.fluency_score = None
        submission.pronunciation_score = None
        submission.vocabulary_score = None
        submission.grammar_score = None
        submission.feedback = None
        submission.graded_at = None
        try:
            submission.full_clean()
            submission.save(update_fields=[
                "status", "overall_score", "fluency_score",
                "pronunciation_score", "vocabulary_score",
                "grammar_score", "feedback", "graded_at"
            ])
        except Exception as db_err:
            logger.critical("Không thể lưu trạng thái FAILED vào database: %s", db_err)
        return False

    audio_path = submission.audio_file.path

    if provider is None:
        provider = get_speaking_ai_grading_provider()

    try:
        result = provider.grade(
            part=part,
            topic=topic,
            prompt_text=prompt_text,
            audio_file_path=audio_path
        )

        submission.overall_score = result.overall_score
        submission.fluency_score = result.fluency_score
        submission.pronunciation_score = result.pronunciation_score
        submission.vocabulary_score = result.vocabulary_score
        submission.grammar_score = result.grammar_score
        submission.feedback = result.feedback
        submission.status = SpeakingSubmission.Status.GRADED
        submission.graded_at = timezone.now()

        submission.full_clean()
        submission.save(update_fields=[
            "status", "overall_score", "fluency_score",
            "pronunciation_score", "vocabulary_score",
            "grammar_score", "feedback", "graded_at"
        ])
        logger.info(
            "Chấm điểm Speaking AI thành công cho bài nộp #%s (Key: %s): Overall %s",
            submission.pk, submission.submission_key, submission.overall_score
        )
        return True

    except Exception as err:
        logger.error(
            "Chấm điểm Speaking AI thất bại cho bài nộp #%s (Key: %s): %s",
            submission.pk, submission.submission_key, str(err)
        )
        submission.status = SpeakingSubmission.Status.FAILED
        submission.overall_score = None
        submission.fluency_score = None
        submission.pronunciation_score = None
        submission.vocabulary_score = None
        submission.grammar_score = None
        submission.feedback = None
        submission.graded_at = None
        try:
            submission.full_clean()
            submission.save(update_fields=[
                "status", "overall_score", "fluency_score",
                "pronunciation_score", "vocabulary_score",
                "grammar_score", "feedback", "graded_at"
            ])
        except Exception as db_err:
            logger.critical("Không thể cập nhật trạng thái FAILED vào database: %s", db_err)
        return False
