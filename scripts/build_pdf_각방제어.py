#!/usr/bin/env python3
"""
각방제어 온도조절 시스템 완전 가이드 - PDF 생성 스크립트
마크다운 콘텐츠를 PDF 전자책으로 변환합니다.
fpdf2 라이브러리 사용 (한글 지원)
"""

import json
import re
import sys
from pathlib import Path

import yaml
from fpdf import FPDF

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
MARKDOWN_DIR = PROJECT_ROOT / "markdown"
PDF_DIR = PROJECT_ROOT / "pdf"

# 폰트 경로
FONT_PATH = Path("C:/Windows/Fonts")

# 테마 색상 (파란 계열 - 기술 매뉴얼)
COLOR_PRIMARY   = (30, 80, 160)   # 진파랑
COLOR_SECONDARY = (52, 120, 190)  # 중간파랑
COLOR_LIGHT     = (230, 238, 250) # 연파랑 배경
COLOR_ACCENT    = (220, 60, 50)   # 강조 빨강
COLOR_TEXT      = (30, 30, 30)    # 본문 텍스트
COLOR_SUBTLE    = (100, 100, 100) # 보조 텍스트
COLOR_BORDER    = (180, 200, 230) # 테두리


class KoreanPDF(FPDF):
    """한글 지원 PDF 클래스 (기술 매뉴얼 테마)"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=22)
        self.book_title = "각방제어 온도조절 시스템 완전 가이드"

        # 맑은 고딕 폰트 등록
        self.add_font("malgun", "",  str(FONT_PATH / "malgun.ttf"))
        self.add_font("malgun", "B", str(FONT_PATH / "malgunbd.ttf"))

    def header(self):
        """페이지 헤더"""
        if self.page_no() > 1:
            r, g, b = COLOR_PRIMARY
            self.set_draw_color(r, g, b)
            self.set_line_width(0.4)
            self.line(10, 14, 200, 14)
            self.set_font("malgun", "", 8)
            self.set_text_color(*COLOR_SUBTLE)
            self.set_y(8)
            self.cell(0, 6, self.book_title, align="C")
            self.ln(8)

    def footer(self):
        """페이지 푸터"""
        self.set_y(-14)
        r, g, b = COLOR_PRIMARY
        self.set_draw_color(r, g, b)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("malgun", "", 8)
        self.set_text_color(*COLOR_SUBTLE)
        self.cell(0, 8, f"— {self.page_no()} —", align="C")

    def chapter_title(self, title, level=1):
        """제목 렌더링"""
        if level == 1:
            self.set_font("malgun", "B", 17)
            self.set_text_color(*COLOR_PRIMARY)
            self.ln(4)
            self.multi_cell(0, 10, title)
            self.ln(1)
            self.set_draw_color(*COLOR_PRIMARY)
            self.set_line_width(0.6)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)
        elif level == 2:
            self.set_font("malgun", "B", 13)
            self.set_text_color(*COLOR_SECONDARY)
            self.ln(4)
            self.multi_cell(0, 8, title)
            self.ln(2)
        elif level == 3:
            self.set_font("malgun", "B", 11)
            self.set_text_color(*COLOR_TEXT)
            self.ln(3)
            # 왼쪽 강조 마크
            x = self.get_x()
            y = self.get_y()
            self.set_fill_color(*COLOR_PRIMARY)
            self.rect(10, y, 2, 6, style="F")
            self.set_x(14)
            self.multi_cell(0, 6, title)
            self.ln(2)
        else:
            self.set_font("malgun", "B", 10)
            self.set_text_color(*COLOR_SUBTLE)
            self.ln(2)
            self.multi_cell(0, 6, "  ▸ " + title)
            self.ln(1)

    def body_text(self, text):
        """본문 텍스트"""
        self.set_font("malgun", "", 10)
        self.set_text_color(*COLOR_TEXT)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def blockquote(self, text):
        """인용/강조 박스"""
        y = self.get_y()
        self.set_fill_color(*COLOR_LIGHT)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.8)
        self.line(12, y, 12, y + 12)
        self.set_x(16)
        self.set_font("malgun", "", 9)
        self.set_text_color(*COLOR_SUBTLE)
        self.multi_cell(178, 5.5, text, fill=True)
        self.ln(3)

    def section_title(self, title):
        """섹션 구분 페이지"""
        self.add_page()
        # 배경 사각형
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 80, 210, 50, style="F")
        self.set_font("malgun", "B", 22)
        self.set_text_color(255, 255, 255)
        self.set_y(88)
        self.multi_cell(0, 14, title, align="C")
        self.set_y(140)
        self.set_font("malgun", "", 10)
        self.set_text_color(*COLOR_SUBTLE)


def load_metadata():
    with open(MARKDOWN_DIR / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_toc():
    with open(MARKDOWN_DIR / "toc.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_markdown(content):
    """마크다운을 구조화된 요소 리스트로 파싱"""
    lines = content.split('\n')
    elements = []
    current_text = []
    in_table = False
    table_data = []
    in_code = False

    for line in lines:
        # 코드 블록 (``` ... ```)
        if line.strip().startswith('```'):
            if in_code:
                in_code = False
            else:
                if current_text:
                    elements.append(('text', '\n'.join(current_text)))
                    current_text = []
                in_code = True
            continue
        if in_code:
            current_text.append(line)
            continue

        # 헤더
        if line.startswith('# '):
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('h1', line[2:].strip()))
        elif line.startswith('## '):
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('#### '):
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('h4', line[5:].strip()))
        # 인용문
        elif line.startswith('> '):
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('quote', line[2:].strip()))
        # 수평선
        elif line.strip() in ['---', '***', '___']:
            if current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []
            elements.append(('hr', ''))
        # 표
        elif '|' in line and line.strip().startswith('|'):
            if not in_table:
                if current_text:
                    elements.append(('text', '\n'.join(current_text)))
                    current_text = []
                in_table = True
                table_data = []
            if not re.match(r'^[\|\s\-:]+$', line):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                table_data.append(cells)
        else:
            if in_table:
                elements.append(('table', table_data))
                in_table = False
                table_data = []

            if line.strip():
                clean = line.strip()
                clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)
                clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
                clean = re.sub(r'`([^`]+)`', r'\1', clean)
                clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
                current_text.append(clean)
            elif current_text:
                elements.append(('text', '\n'.join(current_text)))
                current_text = []

    if current_text:
        elements.append(('text', '\n'.join(current_text)))
    if in_table and table_data:
        elements.append(('table', table_data))

    return elements


def render_table(pdf, data):
    """표 렌더링"""
    if not data:
        return

    col_count = len(data[0]) if data else 0
    if col_count == 0:
        return

    col_width = 180 / col_count

    # 헤더 행
    if data:
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("malgun", "B", 8)
        for cell in data[0]:
            txt = cell[:22] if cell else ""
            pdf.cell(col_width, 7, txt, border=1, fill=True, align="C")
        pdf.ln()

        # 데이터 행
        pdf.set_font("malgun", "", 8)
        for i, row in enumerate(data[1:]):
            if i % 2 == 0:
                pdf.set_fill_color(*COLOR_LIGHT)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(*COLOR_TEXT)

            for j, cell in enumerate(row):
                txt = cell[:28] if cell else ""
                align = "C" if j == 0 else "L"
                pdf.cell(col_width, 6, txt, border=1, fill=True, align=align)
            pdf.ln()

    pdf.ln(3)


def build_cover(pdf, metadata):
    """표지 페이지 생성"""
    pdf.add_page()

    # 상단 색상 바
    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.rect(0, 0, 210, 12, style="F")

    # 제목 영역
    pdf.set_fill_color(*COLOR_LIGHT)
    pdf.rect(10, 40, 190, 70, style="F")

    pdf.set_xy(10, 50)
    pdf.set_font("malgun", "B", 26)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.multi_cell(190, 14, metadata["title"], align="C")

    pdf.ln(6)
    pdf.set_x(10)
    pdf.set_font("malgun", "", 13)
    pdf.set_text_color(*COLOR_SECONDARY)
    pdf.multi_cell(190, 8, metadata.get("subtitle", ""), align="C")

    # 구분선
    pdf.set_y(125)
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.5)
    pdf.line(40, 125, 170, 125)

    # 저자/날짜
    pdf.set_font("malgun", "", 12)
    pdf.set_text_color(*COLOR_SUBTLE)
    pdf.set_xy(10, 132)
    pdf.cell(190, 8, metadata["author"], align="C")
    pdf.ln(9)
    pdf.set_x(10)
    pdf.cell(190, 8, metadata["date"], align="C")

    # 하단 색상 바
    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.rect(0, 285, 210, 12, style="F")


def build_toc_page(pdf, toc_data):
    """목차 페이지 생성"""
    pdf.add_page()
    pdf.set_font("malgun", "B", 16)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.ln(5)
    pdf.cell(0, 10, "목  차", align="C")
    pdf.ln(8)
    pdf.set_draw_color(*COLOR_PRIMARY)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    for section in toc_data["toc"]:
        # 섹션 제목
        pdf.set_font("malgun", "B", 11)
        pdf.set_fill_color(*COLOR_LIGHT)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, "  " + section["section"], fill=True)
        pdf.ln(9)

        for item in section["items"]:
            pdf.set_font("malgun", "", 10)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.cell(8)
            title = item["title"]
            pdf.cell(0, 7, "  · " + title)
            pdf.ln(7)

        pdf.ln(2)


def build_pdf():
    print("=" * 60)
    print("각방제어 온도조절 시스템 완전 가이드 - PDF 생성")
    print("=" * 60)

    print("\n[1/5] 메타데이터 로드...")
    metadata = load_metadata()
    print(f"  제목: {metadata['title']}")

    print("\n[2/5] 목차 구조 로드...")
    toc_data = load_toc()
    print(f"  총 챕터: {toc_data['statistics']['total_chapters']}개")

    print("\n[3/5] PDF 구조 생성...")
    pdf = KoreanPDF()
    pdf.book_title = metadata["title"]
    pdf.set_title(metadata["title"])
    pdf.set_author(metadata["author"])

    print("\n[4/5] 표지 및 목차 생성...")
    build_cover(pdf, metadata)
    build_toc_page(pdf, toc_data)

    print("\n[5/5] 챕터 생성...")
    chapter_count = 0

    for section in toc_data["toc"]:
        section_name = section["section"]
        print(f"\n  [{section_name}]")
        pdf.section_title(section_name)

        for item in section["items"]:
            file_path = MARKDOWN_DIR / item["file"]
            if not file_path.exists():
                print(f"    [경고] 파일 없음: {file_path}")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            elements = parse_markdown(content)

            if chapter_count > 0:
                pdf.add_page()

            chapter_count += 1
            print(f"    + {item['title']}")

            first_h1 = True
            for elem_type, elem_content in elements:
                if elem_type == 'h1':
                    if first_h1:
                        pdf.chapter_title(elem_content, level=1)
                        first_h1 = False
                    else:
                        pdf.chapter_title(elem_content, level=2)
                elif elem_type == 'h2':
                    pdf.chapter_title(elem_content, level=2)
                elif elem_type == 'h3':
                    pdf.chapter_title(elem_content, level=3)
                elif elem_type == 'h4':
                    pdf.chapter_title(elem_content, level=4)
                elif elem_type == 'text':
                    pdf.body_text(elem_content)
                elif elem_type == 'quote':
                    pdf.blockquote(elem_content)
                elif elem_type == 'table':
                    render_table(pdf, elem_content)
                elif elem_type == 'hr':
                    pdf.ln(4)
                    pdf.set_draw_color(*COLOR_BORDER)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(4)

    print(f"\n[저장] PDF 파일 저장...")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PDF_DIR / "각방제어_온도조절_시스템_완전가이드.pdf"
    pdf.output(str(output_path))

    file_size = output_path.stat().st_size
    page_count = pdf.page_no()

    print(f"\n{'=' * 60}")
    print("생성 완료!")
    print(f"  파일: {output_path}")
    print(f"  크기: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    print(f"  페이지: {page_count}페이지")
    print(f"  챕터: {chapter_count}개")
    print("=" * 60)

    return output_path, page_count


if __name__ == "__main__":
    try:
        output, pages = build_pdf()
        print(f"\n성공: {output} ({pages} pages)")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
