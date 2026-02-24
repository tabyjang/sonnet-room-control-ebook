#!/usr/bin/env python3
"""
각방제어 온도조절 시스템 완전 가이드 - EPUB 생성 스크립트
마크다운 콘텐츠를 EPUB 3.0 전자책으로 변환합니다.
"""

import json
import os
import re
import sys
from pathlib import Path

import markdown
import yaml
from ebooklib import epub

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
MARKDOWN_DIR = PROJECT_ROOT / "markdown"
EPUB_DIR = PROJECT_ROOT / "epub"
STYLES_DIR = EPUB_DIR / "styles"


def load_metadata():
    with open(MARKDOWN_DIR / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_toc():
    with open(MARKDOWN_DIR / "toc.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_css():
    css_content = ""
    for css_file in ["ebook.css", "toc.css"]:
        css_path = STYLES_DIR / css_file
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content += f.read() + "\n"
    return css_content


def convert_markdown_to_html(md_content):
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "attr_list"]
    )
    html = md.convert(md_content)
    # pre > code 블록에 class 추가 (코드 스타일)
    html = re.sub(r'<pre><code>', '<pre><code class="code-block">', html)
    return html


def create_chapter(title, content, chapter_id, css_item):
    chapter = epub.EpubHtml(
        title=title,
        file_name=f"{chapter_id}.xhtml",
        lang="ko"
    )
    html_content = f'<div id="{chapter_id}" class="chapter">\n{content}\n</div>'
    chapter.set_content(html_content)
    chapter.add_item(css_item)
    return chapter


def build_epub():
    print("=" * 60)
    print("각방제어 온도조절 시스템 완전 가이드 - EPUB 생성")
    print("=" * 60)

    print("\n[1/5] 메타데이터 로드...")
    metadata = load_metadata()
    print(f"  제목: {metadata['title']}")
    print(f"  저자: {metadata['author']}")

    print("\n[2/5] 목차 구조 로드...")
    toc_data = load_toc()
    print(f"  총 챕터: {toc_data['statistics']['total_chapters']}개")

    print("\n[3/5] EPUB 구조 생성...")
    book = epub.EpubBook()
    book.set_identifier(metadata["identifier"])
    book.set_title(metadata["title"])
    book.set_language(metadata["language"])
    book.add_author(metadata["author"])
    book.add_metadata("DC", "publisher", metadata["publisher"])
    book.add_metadata("DC", "description", metadata["description"])
    book.add_metadata("DC", "date", metadata["date"])
    book.add_metadata("DC", "rights", metadata.get("rights", ""))
    book.add_metadata("DC", "subject", "주택·인테리어")
    book.add_metadata("DC", "subject", "각방제어")
    book.add_metadata("DC", "subject", "난방")
    book.add_metadata("DC", "subject", "온도조절")
    book.add_metadata("DC", "subject", "설비")

    # 표지 이미지 삽입
    cover_path = EPUB_DIR / "cover.jpg"
    if cover_path.exists():
        with open(cover_path, "rb") as f:
            cover_data = f.read()
        book.set_cover("cover.jpg", cover_data)
        print(f"  표지 이미지: cover.jpg ({len(cover_data):,} bytes)")

    print("\n[4/5] 스타일시트 로드...")
    css_content = load_css()
    css_item = epub.EpubItem(
        uid="style",
        file_name="styles/ebook.css",
        media_type="text/css",
        content=css_content.encode("utf-8")
    )
    book.add_item(css_item)
    print(f"  CSS 크기: {len(css_content):,}자")

    print("\n[5/5] 챕터 생성...")
    chapters = []
    toc = []

    for section in toc_data["toc"]:
        section_name = section["section"]
        print(f"\n  [{section_name}]")
        section_toc = []

        for item in section["items"]:
            file_path = MARKDOWN_DIR / item["file"]
            if not file_path.exists():
                print(f"  [경고] 파일 없음: {file_path}")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            chapter_id = re.sub(r'[^\w]', '_', Path(item["file"]).stem)
            html_content = convert_markdown_to_html(md_content)
            chapter = create_chapter(item["title"], html_content, chapter_id, css_item)

            chapters.append(chapter)
            section_toc.append(chapter)
            print(f"    + {item['title']}")

        if section_toc:
            toc.append((epub.Section(section_name), section_toc))

    for chapter in chapters:
        book.add_item(chapter)

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    output_path = EPUB_DIR / "각방제어_온도조절_시스템_완전가이드.epub"
    EPUB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print("EPUB 파일 생성 중...")
    epub.write_epub(str(output_path), book)

    file_size = output_path.stat().st_size
    print(f"\n생성 완료!")
    print(f"  파일: {output_path}")
    print(f"  크기: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"  챕터: {len(chapters)}개")
    print("=" * 60)
    return output_path


if __name__ == "__main__":
    try:
        output = build_epub()
        print(f"\n성공: {output}")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
