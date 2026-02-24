#!/usr/bin/env python3
"""
각방제어 온도조절 시스템 완전 가이드 - 배포용 PDF 생성
  --mode platform  : 플랫폼 입점용 (워터마크 없음)
  --mode direct    : 직접 판매용 (워터마크 있음)
"""

import argparse
import sys
from pathlib import Path

# 기존 빌드 스크립트 임포트
sys.path.insert(0, str(Path(__file__).parent))
from build_pdf_각방제어 import (
    KoreanPDF, load_metadata, load_toc,
    parse_markdown, render_table, build_cover, build_toc_page,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT,
    COLOR_SECONDARY, COLOR_LIGHT, COLOR_SUBTLE,
    MARKDOWN_DIR
)

PROJECT_ROOT = Path(__file__).parent.parent
PDF_DIR = PROJECT_ROOT / "pdf"


class DistributionPDF(KoreanPDF):
    """배포용 PDF — 워터마크 옵션 추가"""

    def __init__(self, watermark_text=None):
        super().__init__()
        self.watermark_text = watermark_text

    def footer(self):
        """워터마크 포함 푸터"""
        # 워터마크 (직접 판매용)
        if self.watermark_text and self.page_no() > 2:
            self.set_font("malgun", "", 7)
            self.set_text_color(200, 210, 230)
            self.set_y(-20)
            self.cell(0, 5, self.watermark_text, align="R")

        # 기본 푸터
        self.set_y(-14)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("malgun", "", 8)
        self.set_text_color(*COLOR_SUBTLE)
        self.cell(0, 8, f"— {self.page_no()} —", align="C")


def build_distribution_pdf(mode: str):
    is_direct = (mode == "direct")

    watermark = "각방제어 온도조절 시스템 완전 가이드 | 무단 배포 금지" if is_direct else None

    print("=" * 60)
    label = "직접판매용 (워터마크)" if is_direct else "플랫폼 입점용"
    print(f"배포용 PDF 생성 - {label}")
    print("=" * 60)

    metadata = load_metadata()
    toc_data = load_toc()

    pdf = DistributionPDF(watermark_text=watermark)
    pdf.book_title = metadata["title"]
    pdf.set_title(metadata["title"])
    pdf.set_author(metadata["author"])
    pdf.set_subject("각방제어 난방 시스템 가이드")
    pdf.set_keywords("각방제어, 난방, 온도조절, 분배기, 지역난방, 가스보일러")
    pdf.set_creator("각방제어 실무 가이드")

    # 표지 + 목차
    build_cover(pdf, metadata)
    build_toc_page(pdf, toc_data)

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

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "_직접판매용" if is_direct else "_플랫폼입점용"
    output_path = PDF_DIR / f"각방제어_온도조절_시스템_완전가이드{suffix}.pdf"
    pdf.output(str(output_path))

    file_size = output_path.stat().st_size
    page_count = pdf.page_no()
    print(f"\n{'=' * 60}")
    print(f"생성 완료! [{label}]")
    print(f"  파일: {output_path.name}")
    print(f"  크기: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    print(f"  페이지: {page_count}페이지")
    print("=" * 60)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["platform", "direct", "both"],
                        default="both", help="배포 모드")
    args = parser.parse_args()

    try:
        if args.mode in ("platform", "both"):
            build_distribution_pdf("platform")
        if args.mode in ("direct", "both"):
            build_distribution_pdf("direct")
    except Exception as e:
        print(f"\n오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
