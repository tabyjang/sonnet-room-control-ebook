#!/usr/bin/env python3
"""
연해자평 30일 완성 - PDF 생성 스크립트

마크다운 콘텐츠를 PDF 전자책으로 변환합니다.
fpdf2 라이브러리 사용 (한글 지원)
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml
from fpdf import FPDF

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
RAW_TEXTS = PROJECT_ROOT / "raw_texts" / "연해자평"
PDF_DIR = PROJECT_ROOT / "pdf"

# 폰트 경로
FONT_PATH = Path("C:/Windows/Fonts")


class KoreanPDF(FPDF):
    """한글 지원 PDF 클래스"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

        # 맑은 고딕 폰트 등록
        self.add_font("malgun", "", str(FONT_PATH / "malgun.ttf"))
        self.add_font("malgun", "B", str(FONT_PATH / "malgunbd.ttf"))

        self.chapter_num = 0
        self.section_name = ""

    def header(self):
        """페이지 헤더"""
        if self.page_no() > 1:
            self.set_font("malgun", "", 9)
            self.set_text_color(128)
            self.cell(0, 10, "연해자평 30일 완성", align="C")
            self.ln(5)
            self.set_draw_color(200)
            self.line(10, 15, 200, 15)
            self.ln(10)

    def footer(self):
        """페이지 푸터"""
        self.set_y(-15)
        self.set_font("malgun", "", 9)
        self.set_text_color(128)
        self.cell(0, 10, f"- {self.page_no()} -", align="C")

    def chapter_title(self, title, level=1):
        """챕터 제목"""
        if level == 1:
            self.set_font("malgun", "B", 18)
            self.set_text_color(0)
            self.ln(5)
            self.multi_cell(0, 10, title)
            self.ln(3)
            # 제목 아래 선
            self.set_draw_color(139, 69, 19)  # 갈색
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(8)
        elif level == 2:
            self.set_font("malgun", "B", 14)
            self.set_text_color(44, 62, 80)
            self.ln(5)
            self.multi_cell(0, 8, title)
            self.ln(3)
        elif level == 3:
            self.set_font("malgun", "B", 12)
            self.set_text_color(52, 73, 94)
            self.ln(4)
            self.multi_cell(0, 7, title)
            self.ln(2)
        else:
            self.set_font("malgun", "B", 11)
            self.set_text_color(85, 85, 85)
            self.ln(3)
            self.multi_cell(0, 6, title)
            self.ln(2)

    def body_text(self, text):
        """본문 텍스트"""
        self.set_font("malgun", "", 11)
        self.set_text_color(51)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def blockquote(self, text):
        """인용문"""
        self.set_fill_color(249, 245, 240)
        self.set_draw_color(139, 69, 19)

        # 왼쪽 여백 추가
        x = self.get_x()
        y = self.get_y()

        self.set_x(x + 5)
        self.set_font("malgun", "", 10)
        self.set_text_color(85, 85, 85)

        # 배경 및 왼쪽 선
        self.set_line_width(1)
        self.line(15, y, 15, y + 15)
        self.set_fill_color(249, 245, 240)
        self.multi_cell(180, 6, text, fill=True)
        self.ln(3)

    def section_title(self, title):
        """섹션 제목 (새 페이지)"""
        self.add_page()
        self.section_name = title
        self.set_font("malgun", "B", 24)
        self.set_text_color(139, 69, 19)
        self.ln(40)
        self.multi_cell(0, 15, title, align="C")
        self.ln(10)


def load_metadata():
    """메타데이터 로드"""
    with open(RAW_TEXTS / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_toc():
    """목차 구조 로드"""
    with open(RAW_TEXTS / "toc.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_markdown(content):
    """마크다운을 구조화된 데이터로 파싱"""
    lines = content.split('\n')
    elements = []

    current_text = []
    in_blockquote = False
    in_table = False
    table_data = []

    for line in lines:
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
            # 구분선 제외
            if not re.match(r'^[\|\s\-:]+$', line):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                table_data.append(cells)
        else:
            if in_table:
                elements.append(('table', table_data))
                in_table = False
                table_data = []

            # 일반 텍스트
            if line.strip():
                # 마크다운 서식 제거
                clean = line.strip()
                clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)  # bold
                clean = re.sub(r'\*([^*]+)\*', r'\1', clean)  # italic
                clean = re.sub(r'`([^`]+)`', r'\1', clean)  # code
                clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)  # links
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

    pdf.set_font("malgun", "", 9)
    pdf.set_text_color(51)

    # 열 너비 계산
    col_count = len(data[0]) if data else 0
    if col_count == 0:
        return

    col_width = 180 / col_count

    # 헤더 행
    if data:
        pdf.set_fill_color(139, 69, 19)
        pdf.set_text_color(255)
        pdf.set_font("malgun", "B", 9)
        for cell in data[0]:
            pdf.cell(col_width, 7, cell[:20], border=1, fill=True, align="C")
        pdf.ln()

        # 데이터 행
        pdf.set_text_color(51)
        pdf.set_font("malgun", "", 9)
        for i, row in enumerate(data[1:]):
            if i % 2 == 0:
                pdf.set_fill_color(249, 249, 249)
            else:
                pdf.set_fill_color(255, 255, 255)

            for cell in row:
                pdf.cell(col_width, 6, cell[:25], border=1, fill=True)
            pdf.ln()

    pdf.ln(3)


def build_pdf():
    """PDF 생성 메인 함수"""
    print("=" * 60)
    print("연해자평 30일 완성 - PDF 생성")
    print("=" * 60)

    # 메타데이터 로드
    print("\n[1/5] 메타데이터 로드...")
    metadata = load_metadata()
    print(f"  제목: {metadata['title']}")

    # 목차 로드
    print("\n[2/5] 목차 구조 로드...")
    toc_data = load_toc()
    print(f"  총 챕터: {toc_data['statistics']['total_chapters']}개")

    # PDF 생성
    print("\n[3/5] PDF 구조 생성...")
    pdf = KoreanPDF()
    pdf.set_title(metadata["title"])
    pdf.set_author(metadata["author"])

    # 표지 페이지
    print("\n[4/5] 콘텐츠 추가...")
    pdf.add_page()
    pdf.set_font("malgun", "B", 32)
    pdf.set_text_color(139, 69, 19)
    pdf.ln(60)
    pdf.multi_cell(0, 20, metadata["title"], align="C")
    pdf.ln(10)
    pdf.set_font("malgun", "", 18)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 12, metadata["subtitle"], align="C")
    pdf.ln(30)
    pdf.set_font("malgun", "", 14)
    pdf.multi_cell(0, 10, metadata["author"], align="C")
    pdf.ln(5)
    pdf.multi_cell(0, 10, metadata["date"], align="C")

    chapter_count = 0

    # 각 섹션 처리
    for section in toc_data["toc"]:
        section_name = section["section"]
        print(f"\n  [{section_name}]")

        # 섹션 제목 페이지
        pdf.section_title(section_name)

        # 섹션 내 항목들 처리
        def process_items(items):
            nonlocal chapter_count
            for item in items:
                if "subsection" in item:
                    # 서브섹션
                    pdf.chapter_title(item["subsection"], level=2)
                    process_items(item["items"])
                elif "file" in item:
                    # 챕터
                    file_path = RAW_TEXTS / item["file"]
                    if not file_path.exists():
                        print(f"    [경고] 파일 없음: {file_path}")
                        continue

                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 마크다운 파싱
                    elements = parse_markdown(content)

                    # 새 페이지 시작 (표지/서문 이후)
                    if chapter_count > 0:
                        pdf.add_page()

                    chapter_count += 1
                    print(f"    + {item['title']}")

                    # 요소 렌더링
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
                            pdf.ln(5)
                            pdf.set_draw_color(200)
                            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                            pdf.ln(5)

        process_items(section["items"])

    # PDF 저장
    print(f"\n[5/5] PDF 파일 저장...")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PDF_DIR / "연해자평_30일완성.pdf"
    pdf.output(str(output_path))

    # 결과 출력
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
