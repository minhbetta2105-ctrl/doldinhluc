import os
import zipfile
import html

def escape_xml(text):
    if text is None:
        return ""
    return html.escape(str(text), quote=False).replace('"', "&quot;")

class DocxBuilder:
    def __init__(self):
        self.body_elements = []

    def add_title(self, text, subtitle=None):
        xml = f"""
        <w:p>
            <w:pPr>
                <w:jc w:val="center"/>
                <w:spacing w:before="360" w:after="120"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="38"/>
                    <w:color w:val="C92127"/>
                </w:rPr>
                <w:t>{escape_xml(text)}</w:t>
            </w:r>
        </w:p>
        """
        self.body_elements.append(xml)
        if subtitle:
            sub_xml = f"""
            <w:p>
                <w:pPr>
                    <w:jc w:val="center"/>
                    <w:spacing w:after="360"/>
                </w:pPr>
                <w:r>
                    <w:rPr>
                        <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                        <w:i/>
                        <w:sz w:val="24"/>
                        <w:color w:val="64748B"/>
                    </w:rPr>
                    <w:t>{escape_xml(subtitle)}</w:t>
                </w:r>
            </w:p>
            """
            self.body_elements.append(sub_xml)

    def add_heading_1(self, text):
        xml = f"""
        <w:p>
            <w:pPr>
                <w:spacing w:before="320" w:after="120"/>
                <w:pBdr>
                    <w:bottom w:val="single" w:sz="12" w:space="4" w:color="C92127"/>
                </w:pBdr>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="28"/>
                    <w:color w:val="1E293B"/>
                </w:rPr>
                <w:t>{escape_xml(text)}</w:t>
            </w:r>
        </w:p>
        """
        self.body_elements.append(xml)

    def add_heading_2(self, text):
        xml = f"""
        <w:p>
            <w:pPr>
                <w:spacing w:before="240" w:after="80"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="24"/>
                    <w:color w:val="2563EB"/>
                </w:rPr>
                <w:t>{escape_xml(text)}</w:t>
            </w:r>
        </w:p>
        """
        self.body_elements.append(xml)

    def add_paragraph(self, text, bold_prefix="", italic=False, color="1E293B"):
        p_xml = ["<w:p><w:pPr><w:spacing w:after=\"100\"/></w:pPr>"]
        if bold_prefix:
            p_xml.append(f"""
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:b/>
                    <w:sz w:val="22"/>
                    <w:color w:val="{color}"/>
                </w:rPr>
                <w:t xml:space="preserve">{escape_xml(bold_prefix)} </w:t>
            </w:r>
            """)
        italic_tag = "<w:i/>" if italic else ""
        p_xml.append(f"""
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                {italic_tag}
                <w:sz w:val="22"/>
                <w:color w:val="{color}"/>
            </w:rPr>
            <w:t xml:space="preserve">{escape_xml(text)}</w:t>
        </w:r>
        </w:p>
        """)
        self.body_elements.append("".join(p_xml))

    def add_callout(self, text):
        xml = f"""
        <w:p>
            <w:pPr>
                <w:pBdr>
                    <w:left w:val="single" w:sz="24" w:space="12" w:color="2563EB"/>
                </w:pBdr>
                <w:shd w:val="clear" w:color="auto" w:fill="EFF6FF"/>
                <w:spacing w:before="120" w:after="120"/>
                <w:ind w:left="200" w:right="200"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                    <w:sz w:val="21"/>
                    <w:color w:val="1E3A8A"/>
                </w:rPr>
                <w:t>{escape_xml(text)}</w:t>
            </w:r>
        </w:p>
        """
        self.body_elements.append(xml)

    def add_table(self, headers, rows):
        tbl_xml = ["""
        <w:tbl>
            <w:tblPr>
                <w:tblW w:w="5000" w:type="pct"/>
                <w:tblBorders>
                    <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                    <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                    <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                    <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                    <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                    <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                </w:tblBorders>
            </w:tblPr>
        """]

        # Header row
        tbl_xml.append("<w:tr><w:trPr><w:tblHeader/></w:trPr>")
        for h in headers:
            tbl_xml.append(f"""
            <w:tc>
                <w:tcPr>
                    <w:shd w:val="clear" w:color="auto" w:fill="F1F5F9"/>
                    <w:tcMar>
                        <w:top w:w="120" w:type="dxa"/>
                        <w:bottom w:w="120" w:type="dxa"/>
                        <w:left w:w="160" w:type="dxa"/>
                        <w:right w:w="160" w:type="dxa"/>
                    </w:tcMar>
                </w:tcPr>
                <w:p>
                    <w:pPr><w:spacing w:after="0"/></w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                            <w:b/>
                            <w:sz w:val="20"/>
                            <w:color w:val="1E293B"/>
                        </w:rPr>
                        <w:t>{escape_xml(h)}</w:t>
                    </w:r>
                </w:p>
            </w:tc>
            """)
        tbl_xml.append("</w:tr>")

        # Data rows
        for row in rows:
            tbl_xml.append("<w:tr>")
            for cell in row:
                tbl_xml.append(f"""
                <w:tc>
                    <w:tcPr>
                        <w:tcMar>
                            <w:top w:w="100" w:type="dxa"/>
                            <w:bottom w:w="100" w:type="dxa"/>
                            <w:left w:w="140" w:type="dxa"/>
                            <w:right w:w="140" w:type="dxa"/>
                        </w:tcMar>
                    </w:tcPr>
                    <w:p>
                        <w:pPr><w:spacing w:after="0"/></w:pPr>
                        <w:r>
                            <w:rPr>
                                <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                                <w:sz w:val="20"/>
                                <w:color w:val="334155"/>
                            </w:rPr>
                            <w:t>{escape_xml(cell)}</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                """)
            tbl_xml.append("</w:tr>")

        tbl_xml.append("</w:tbl>")
        self.body_elements.append("".join(tbl_xml))

    def add_code_block(self, code_str, filename=""):
        if filename:
            self.add_paragraph(f"Đường dẫn: {filename}", bold_prefix="📄 FILE:", color="C92127")

        lines = code_str.split("\n")
        code_p_list = []
        for line in lines:
            line_xml = f"""
            <w:p>
                <w:pPr>
                    <w:shd w:val="clear" w:color="auto" w:fill="F8FAFC"/>
                    <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
                    <w:ind w:left="160" w:right="160"/>
                    <w:pBdr>
                        <w:left w:val="single" w:sz="16" w:space="8" w:color="CBD5E1"/>
                    </w:pBdr>
                </w:pPr>
                <w:r>
                    <w:rPr>
                        <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
                        <w:sz w:val="18"/>
                        <w:color w:val="0F172A"/>
                    </w:rPr>
                    <w:t xml:space="preserve">{escape_xml(line)}</w:t>
                </w:r>
            </w:p>
            """
            code_p_list.append(line_xml)

        self.body_elements.append("".join(code_p_list))
        # Empty space after code
        self.body_elements.append("<w:p><w:pPr><w:spacing w:after=\"120\"/></w:pPr></w:p>")

    def save(self, filepath):
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

        doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

        styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="22"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>"""

        body_inner = "".join(self.body_elements)
        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_inner}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", content_types)
            docx.writestr("_rels/.rels", rels)
            docx.writestr("word/_rels/document.xml.rels", doc_rels)
            docx.writestr("word/styles.xml", styles_xml)
            docx.writestr("word/document.xml", document_xml)

def read_file_safely(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"# Error reading file {path}: {e}"

def generate_report():
    doc = DocxBuilder()
    doc.add_title(
        "BÁO CÁO TOÀN BỘ MÃ NGUỒN PHÁT TRIỂN & BỔ SUNG",
        "Dự án Nền tảng luyện thi trực tuyến DOL IELTS Đình Lực — Module Reading & Listening"
    )

    doc.add_callout(
        "Tài liệu này tổng hợp toàn bộ các file mã nguồn (Backend, Frontend Templates, Database Migrations & Seed Data, Unit Tests) "
        "đã được phát triển mới hoặc bổ sung hoàn thiện so với dự án khung ban đầu, bám sát 100% đặc tả Use Case nhóm 6."
    )

    # I. TỔNG QUAN
    doc.add_heading_1("I. BẢNG TỔNG KẾT TOÀN BỘ FILE THAY ĐỔI / TẠO MỚI")
    headers = ["STT", "Đường dẫn File", "Trạng thái", "Mô tả vai trò trong hệ thống"]
    rows = [
        ["1", "listening/urls.py", "Tạo mới", "Routing phân luồng cho danh sách, làm bài, nộp bài, xem kết quả Listening"],
        ["2", "listening/views.py", "Viết mới (100%)", "Xử lý logic 5 Use Case Listening (UC-LIS-01 đến UC-LIS-05)"],
        ["3", "core/decorators.py", "Chỉnh sửa", "Kiểm tra an toàn resolver_match để bảo vệ endpoint Học viên"],
        ["4", "config/settings.py", "Chỉnh sửa", "Cấu hình database SQLite/PostgreSQL linh hoạt và múi giờ Việt Nam"],
        ["5", "templates/base.html", "Chỉnh sửa", "Tích hợp static logo chính thức DOL IELTS Đình Lực vào thanh Navbar"],
        ["6", "templates/reading/attempt_result.html", "Tạo mới", "Giao diện kết quả Reading kèm vòng tròn tỷ lệ % và giải thích"],
        ["7", "templates/reading/error.html", "Tạo mới", "Trang thông báo lỗi ngoại lệ cho Reading"],
        ["8", "templates/listening/exercise_list.html", "Tạo mới", "Giao diện danh sách bài Listening kèm tìm kiếm, lọc theo level"],
        ["9", "templates/listening/exercise_detail.html", "Tạo mới", "Giao diện làm bài nghe kèm Audio Player & Question Palette"],
        ["10", "templates/listening/attempt_result.html", "Tạo mới", "Giao diện kết quả Listening kèm khung nghe lại audio và giải thích tiếng Anh"],
        ["11", "templates/listening/error.html", "Tạo mới", "Trang thông báo lỗi ngoại lệ cho Listening"],
        ["12", "receptive/management/commands/seed_data.py", "Tạo mới", "Command nạp 12 bài luyện, 60 câu hỏi kèm giải thích tiếng Anh chuẩn"],
        ["13", "receptive/tests.py", "Viết mới", "Unit Test kiểm thử thuật toán chuẩn hoá chuỗi và chấm điểm tự động"],
        ["14", "listening/tests.py & reading/tests.py", "Viết mới", "Unit Test kiểm thử hệ thống định tuyến và chuyển hướng bảo mật"],
    ]
    doc.add_table(headers, rows)

    # II. LOGIC BACKEND
    doc.add_heading_1("II. CHI TIẾT CÁC FILE LOGIC BACKEND")

    doc.add_heading_2("2.1. File: listening/urls.py (Tạo mới)")
    doc.add_paragraph("Khai báo URL patterns cho app listening, định danh namespace 'listening'.")
    urls_code = read_file_safely("listening/urls.py")
    doc.add_code_block(urls_code, "dol-ielts-web-main/listening/urls.py")

    doc.add_heading_2("2.2. File: listening/views.py (Viết mới hoàn chỉnh)")
    doc.add_paragraph("Triển khai toàn bộ các views cho UC-LIS-01 (danh sách), UC-LIS-02 (làm bài), UC-LIS-03/04 (nộp & chấm điểm), UC-LIS-05 (xem kết quả).")
    views_code = read_file_safely("listening/views.py")
    doc.add_code_block(views_code, "dol-ielts-web-main/listening/views.py")

    doc.add_heading_2("2.3. File: core/decorators.py (Chỉnh sửa an toàn)")
    doc.add_paragraph("Tối ưu hoá hàm decorator hoc_vien_required tránh phát sinh lỗi khi request chưa gắn resolver_match:")
    decorators_code = read_file_safely("core/decorators.py")
    doc.add_code_block(decorators_code, "dol-ielts-web-main/core/decorators.py")

    doc.add_heading_2("2.4. File: config/settings.py (Chỉnh sửa)")
    doc.add_paragraph("Hỗ trợ tự động chuyển đổi giữa SQLite và PostgreSQL, cấu hình static files:")
    settings_code = read_file_safely("config/settings.py")
    doc.add_code_block(settings_code, "dol-ielts-web-main/config/settings.py")

    # III. TEMPLATES GIAO DIỆN
    doc.add_heading_1("III. CHI TIẾT CÁC FILE GIAO DIỆN (TEMPLATES HTML/CSS)")

    doc.add_heading_2("3.1. File: templates/base.html (Chỉnh sửa Logo)")
    doc.add_paragraph("Cập nhật thẻ logo thương hiệu DOL IELTS Đình Lực tại thanh điều hướng header:")
    base_code = read_file_safely("templates/base.html")
    doc.add_code_block(base_code, "dol-ielts-web-main/templates/base.html")

    doc.add_heading_2("3.2. File: templates/reading/attempt_result.html (Tạo mới)")
    doc.add_paragraph("Giao diện trang xem kết quả bài làm Reading theo Hình 24 trong tài liệu đặc tả:")
    r_res_code = read_file_safely("templates/reading/attempt_result.html")
    doc.add_code_block(r_res_code, "dol-ielts-web-main/templates/reading/attempt_result.html")

    doc.add_heading_2("3.3. File: templates/listening/exercise_list.html (Tạo mới)")
    doc.add_paragraph("Giao diện danh sách bài nghe Listening theo Hình 47 và 48:")
    l_list_code = read_file_safely("templates/listening/exercise_list.html")
    doc.add_code_block(l_list_code, "dol-ielts-web-main/templates/listening/exercise_list.html")

    doc.add_heading_2("3.4. File: templates/listening/exercise_detail.html (Tạo mới)")
    doc.add_paragraph("Giao diện làm bài nghe Listening tích hợp Audio Player và Question Palette theo Hình 49:")
    l_det_code = read_file_safely("templates/listening/exercise_detail.html")
    doc.add_code_block(l_det_code, "dol-ielts-web-main/templates/listening/exercise_detail.html")

    doc.add_heading_2("3.5. File: templates/listening/attempt_result.html (Tạo mới)")
    doc.add_paragraph("Giao diện xem kết quả bài Listening có khung nghe lại audio theo Hình 54:")
    l_res_code = read_file_safely("templates/listening/attempt_result.html")
    doc.add_code_block(l_res_code, "dol-ielts-web-main/templates/listening/attempt_result.html")

    # IV. SEED DATA COMMAND
    doc.add_heading_1("IV. MANAGEMENT COMMAND KHỞI TẠO CƠ SỞ DỮ LIỆU")
    doc.add_paragraph("Khởi tạo 12 bài luyện Reading & Listening, 60 câu hỏi với giải thích tiếng Anh dễ hiểu:")
    seed_code = read_file_safely("receptive/management/commands/seed_data.py")
    doc.add_code_block(seed_code, "dol-ielts-web-main/receptive/management/commands/seed_data.py")

    # V. UNIT TESTS
    doc.add_heading_1("V. BỘ KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)")
    doc.add_heading_2("5.1. File: receptive/tests.py")
    rec_test_code = read_file_safely("receptive/tests.py")
    doc.add_code_block(rec_test_code, "dol-ielts-web-main/receptive/tests.py")

    doc.add_heading_2("5.2. File: listening/tests.py")
    lis_test_code = read_file_safely("listening/tests.py")
    doc.add_code_block(lis_test_code, "dol-ielts-web-main/listening/tests.py")

    doc.add_heading_2("5.3. File: reading/tests.py")
    read_test_code = read_file_safely("reading/tests.py")
    doc.add_code_block(read_test_code, "dol-ielts-web-main/reading/tests.py")

    out_path = os.path.abspath("BAO_CAO_MA_NGUON_DOL_IELTS.docx")
    doc.save(out_path)
    print(f"File DOCX exported successfully to: {out_path}")

if __name__ == "__main__":
    generate_report()
