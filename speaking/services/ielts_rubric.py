import math
from decimal import Decimal, InvalidOperation
from typing import Dict, Any

RUBRIC_VERSION = "IELTS Speaking Band Descriptors (Public Version)"
RUBRIC_SOURCE = "British Council / IDP / Cambridge English"

DISCLAIMER_TEXT = (
    "Lưu ý quan trọng: Kết quả đánh giá này do Trí tuệ Nhân tạo (Gemini AI) thực hiện dựa trên "
    f"Tiêu chí Khảo thí IELTS Speaking ({RUBRIC_VERSION}) nhằm mục đích học tập và tham khảo, "
    "không phải là điểm thi IELTS chính thức và không có giá trị pháp lý tương đương giám khảo chấm thi."
)


def calculate_ielts_speaking_overall(
    fc: Decimal,
    lr: Decimal,
    gra: Decimal,
    p: Decimal
) -> Decimal:
    """
    Tính điểm Overall Band cho bài thi IELTS Speaking từ 4 tiêu chí thành phần:
    1. Fluency and Coherence (fc)
    2. Lexical Resource (lr)
    3. Grammatical Range and Accuracy (gra)
    4. Pronunciation (p)

    Quy tắc chuẩn quốc tế của IELTS:
    - Bốn tiêu chí có trọng số bằng nhau (25% mỗi tiêu chí).
    - Điểm trung bình cộng = (fc + lr + gra + p) / 4.
    - Quy tắc làm tròn IELTS đến mức 0.5 gần nhất:
      + Nếu phần thập phân < 0.25 -> làm tròn xuống .0 (vd 6.125 -> 6.0)
      + Nếu 0.25 <= phần thập phân < 0.75 -> làm tròn thành .5 (vd 6.25 -> 6.5, 6.375 -> 6.5, 6.625 -> 6.5)
      + Nếu phần thập phân >= 0.75 -> làm tròn lên .0 tiếp theo (vd 6.75 -> 7.0, 6.875 -> 7.0)
    - Toàn bộ phép toán thực hiện bằng Decimal để chống sai số dấu phẩy động.
    """
    for name, val in [("Fluency", fc), ("Lexical", lr), ("Grammar", gra), ("Pronunciation", p)]:
        if val is None or not isinstance(val, Decimal):
            raise ValueError(f"Điểm tiêu chí {name} phải là Decimal hợp lệ, nhận được: {val}")
        if val < Decimal("0.0") or val > Decimal("9.0"):
            raise ValueError(f"Điểm tiêu chí {name} phải nằm trong khoảng [0.0, 9.0], nhận được: {val}")

    avg = (fc + lr + gra + p) / Decimal("4")
    integer_part = Decimal(int(avg))
    fraction = avg - integer_part

    if fraction < Decimal("0.25"):
        overall = integer_part
    elif fraction < Decimal("0.75"):
        overall = integer_part + Decimal("0.5")
    else:
        overall = integer_part + Decimal("1.0")

    # Giới hạn an toàn trong [0.0, 9.0]
    if overall > Decimal("9.0"):
        overall = Decimal("9.0")
    if overall < Decimal("0.0"):
        overall = Decimal("0.0")

    return overall.quantize(Decimal("0.1"))


def build_ielts_speaking_prompt(part: str, topic: str, prompt_text: str) -> str:
    """
    Xây dựng prompt chi tiết hướng dẫn Gemini AI chấm bài Speaking theo 4 tiêu chí IELTS.
    """
    return f"""Bạn là Giám khảo Khảo thí IELTS Chuyên nghiệp (Senior IELTS Speaking Examiner) được chứng nhận quốc tế.
Nhiệm vụ của bạn là nghe bản ghi âm câu trả lời của thí sinh (được gửi kèm trong file audio), chuyển âm thanh thành văn bản (transcribe), và chấm điểm chi tiết bài thi IELTS Speaking theo đúng tài liệu 'IELTS Speaking Band Descriptors (Public Version)'.

---
THÔNG TIN BÀI THI:
- Phần thi: {part}
- Chủ đề: {topic}
- Nội dung câu hỏi / Cue card:
\"\"\"{prompt_text}\"\"\"

---
TIÊU CHÍ ĐÁNH GIÁ (RUBRIC IELTS 4 TIÊU CHÍ):
1. Fluency and Coherence (Độ trôi chảy và mạch lạc):
   - Tốc độ nói, tính liên tục, khoảng ngập ngừng tự nhiên hay do tìm từ/ngữ pháp.
   - Khả năng duy trì câu trả lời dài và phát triển ý tưởng.
   - Sử dụng các từ nối (connectives), cụm từ liên kết và discourse markers phù hợp.

2. Lexical Resource (Vốn từ vựng):
   - Đa dạng và độ chuẩn xác của vốn từ sử dụng theo chủ đề.
   - Khả năng dùng collocations, idioms tự nhiên, paraphrasing linh hoạt.
   - Lưu ý: Không nhầm lẫn giữa việc cố nhồi nhét từ khó một cách gượng gạo và việc dùng từ chính xác.

3. Grammatical Range and Accuracy (Độ đa dạng và chính xác của ngữ pháp):
   - Sự kết hợp giữa câu đơn và cấu trúc câu phức.
   - Tần suất và mức độ nghiêm trọng của lỗi ngữ pháp (thời thì, số ít số nhiều, giới từ, trật tự từ).
   - Mức độ ảnh hưởng của lỗi ngữ pháp tới khả năng truyền đạt thông tin.

4. Pronunciation (Phát âm - BẮT BUỘC ĐÁNH GIÁ TRỰC TIẾP TỪ ÂM THANH):
   - Độ rõ ràng, dễ hiểu của các âm riêng lẻ (individual sounds).
   - Trọng âm từ (word stress) và trọng âm câu (sentence stress).
   - Ngữ điệu (intonation), nhịp điệu (rhythm), nối âm (connected speech).
   - Lưu ý: Không coi accent vùng miền/quốc gia khác (như giọng Việt Nam, Anh, Mỹ, Úc) là lỗi phát âm nếu người nghe vẫn hiểu rõ ràng và thông suốt.

---
QUY TẮC CHẤM ĐIỂM:
- Điểm mỗi tiêu chí là số thực trong khoảng từ 0.0 đến 9.0, bước nhảy 0.5 (ví dụ: 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0).
- Không tự ý nâng band điểm để làm hài lòng học viên. Đánh giá khách quan, chuẩn xác theo năng lực thực tế được ghi nhận trong audio.
- Không chấm điểm dựa thuần túy trên độ dài câu trả lời.
- Toàn bộ nhận xét, giải thích và gợi ý phải bằng TIẾNG VIỆT, giữ nguyên các trích dẫn và ví dụ câu tiếng Anh của thí sinh.
- Chỉ đưa ra các lỗi và bằng chứng CÓ THỰC trong câu trả lời của thí sinh. Tuyệt đối KHÔNG bịa ra lỗi hoặc câu nói mà thí sinh không hề nói.
- Nếu tệp âm thanh hoàn toàn im lặng, bị nhiễu không nghe được tiếng người nói, hoặc không có tiếng Anh, hãy ghi rõ vào overall_feedback và gán các điểm tiêu chí là null hoặc 0.0.

---
ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
Trả về DUY NHẤT một đối tượng JSON hợp lệ (không kèm Markdown code block ngoài json, không thêm văn bản dẫn dắt bên ngoài):
{{
  "transcript": "<Nội dung chuyển từ audio thành văn bản tiếng Anh đầy đủ và trung thực>",
  "fluency_score": <số thực từ 0.0 đến 9.0 theo bước 0.5, ví dụ 6.5>,
  "lexical_score": <số thực từ 0.0 đến 9.0 theo bước 0.5, ví dụ 6.0>,
  "grammar_score": <số thực từ 0.0 đến 9.0 theo bước 0.5, ví dụ 6.0>,
  "pronunciation_score": <số thực từ 0.0 đến 9.0 theo bước 0.5, ví dụ 6.5>,
  "overall_feedback": "<Nhận xét tổng quan bằng tiếng Việt về toàn bộ phần thể hiện của thí sinh>",
  "strengths": [
    "<Điểm mạnh 1>",
    "<Điểm mạnh 2>"
  ],
  "weaknesses": [
    "<Điểm cần cải thiện 1>",
    "<Điểm cần cải thiện 2>"
  ],
  "grammar_corrections": [
    {{
      "original": "<Câu hoặc cụm từ học viên nói mắc lỗi>",
      "correction": "<Cách sửa chuẩn ngữ pháp>",
      "explanation": "<Giải thích lỗi và lý do sửa bằng tiếng Việt>"
    }}
  ],
  "vocabulary_suggestions": [
    {{
      "original": "<Từ hoặc cách diễn đạt học viên đã dùng>",
      "suggestion": "<Từ vựng nâng cao/tự nhiên hơn hoặc collocation phù hợp>",
      "explanation": "<Giải thích vì sao cách dùng này tốt hơn>"
    }}
  ],
  "pronunciation_feedback": [
    {{
      "word": "<Từ phát âm chưa chuẩn hoặc cần lưu ý>",
      "issue": "<Vấn đề phát âm nghe được từ audio, ví dụ: thiếu ending sound /s/, sai trọng âm>",
      "tip": "<Hướng dẫn cách phát âm chuẩn>"
    }}
  ],
  "improvement_suggestions": [
    "<Gợi ý phương pháp luyện tập 1>",
    "<Gợi ý phương pháp luyện tập 2>"
  ]
}}
"""
