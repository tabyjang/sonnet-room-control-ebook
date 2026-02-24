#!/usr/bin/env python3
"""
연해자평 30일 완성 - EPUB 생성 스크립트

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
RAW_TEXTS = PROJECT_ROOT / "raw_texts" / "연해자평"
EPUB_DIR = PROJECT_ROOT / "epub"
STYLES_DIR = EPUB_DIR / "styles"


def load_metadata():
    """메타데이터 로드"""
    with open(RAW_TEXTS / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_toc():
    """목차 구조 로드"""
    with open(RAW_TEXTS / "toc.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_css():
    """CSS 스타일시트 로드"""
    css_content = ""
    for css_file in ["ebook.css", "toc.css"]:
        css_path = STYLES_DIR / css_file
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content += f.read() + "\n"
    return css_content


def convert_markdown_to_html(md_content, chapter_file):
    """마크다운을 HTML로 변환"""
    # 마크다운 확장 설정
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "attr_list",
        ]
    )

    # 내부 링크 변환 (상대 경로 → EPUB 내부 경로)
    # ../보강/십간십이지/01_갑목.md → chapter_appendix_a_01.xhtml
    def fix_internal_links(match):
        link_path = match.group(1)
        link_text = match.group(2) if match.group(2) else link_path

        # 마크다운 링크를 EPUB 내부 링크로 변환
        if link_path.endswith(".md"):
            # 파일명에서 EPUB 챕터 ID 생성
            filename = Path(link_path).stem
            # 간단히 앵커만 제거하고 파일명 기반 ID 사용
            return f'<a href="#{filename}">{link_text}</a>'
        return match.group(0)

    html = md.convert(md_content)

    # 마크다운 링크 패턴 (이미 HTML로 변환된 후)
    # href="...md" 패턴을 찾아서 수정
    html = re.sub(
        r'href="([^"]*\.md)"',
        lambda m: f'href="#{Path(m.group(1)).stem}"',
        html
    )

    return html


def create_chapter(title, content, chapter_id, css_item):
    """EPUB 챕터 생성"""
    chapter = epub.EpubHtml(
        title=title,
        file_name=f"{chapter_id}.xhtml",
        lang="ko"
    )

    # ebooklib은 body 내용만 필요 (wrapper는 자동 생성)
    html_content = f"""<div id="{chapter_id}" class="chapter">
<h1>{title}</h1>
{content}
</div>"""

    chapter.set_content(html_content)
    chapter.add_item(css_item)

    return chapter


def process_section_items(items, base_path, chapters, toc_items, css_item, section_prefix=""):
    """섹션 내 항목들 처리 (재귀)"""
    for item in items:
        if "subsection" in item:
            # 서브섹션인 경우 재귀 처리
            sub_toc = []
            process_section_items(
                item["items"],
                base_path,
                chapters,
                sub_toc,
                css_item,
                section_prefix
            )
            toc_items.append((epub.Section(item["subsection"]), sub_toc))
        elif "file" in item:
            # 일반 챕터
            file_path = RAW_TEXTS / item["file"]
            if not file_path.exists():
                print(f"  [경고] 파일 없음: {file_path}")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            # 챕터 ID 생성 (파일 경로 기반)
            chapter_id = item["file"].replace("/", "_").replace(".md", "")
            chapter_id = re.sub(r'[^\w가-힣]', '_', chapter_id)

            # 마크다운 → HTML 변환
            html_content = convert_markdown_to_html(md_content, item["file"])

            # 챕터 생성
            chapter = create_chapter(
                item["title"],
                html_content,
                chapter_id,
                css_item
            )

            chapters.append(chapter)
            toc_items.append(chapter)
            print(f"  + {item['title']}")


def build_epub():
    """EPUB 생성 메인 함수"""
    print("=" * 60)
    print("연해자평 30일 완성 - EPUB 생성")
    print("=" * 60)

    # 메타데이터 로드
    print("\n[1/5] 메타데이터 로드...")
    metadata = load_metadata()
    print(f"  제목: {metadata['title']}")
    print(f"  저자: {metadata['author']}")

    # 목차 로드
    print("\n[2/5] 목차 구조 로드...")
    toc_data = load_toc()
    print(f"  총 챕터: {toc_data['statistics']['total_chapters']}개")

    # EPUB 객체 생성
    print("\n[3/5] EPUB 구조 생성...")
    book = epub.EpubBook()

    # 메타데이터 설정
    book.set_identifier(metadata["identifier"])
    book.set_title(metadata["title"])
    book.set_language(metadata["language"])
    book.add_author(metadata["author"])
    book.add_metadata("DC", "publisher", metadata["publisher"])
    book.add_metadata("DC", "description", metadata["description"])
    book.add_metadata("DC", "date", metadata["date"])

    # CSS 스타일시트 추가
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

    # 챕터 생성
    print("\n[5/5] 챕터 생성...")
    chapters = []
    toc = []

    for section in toc_data["toc"]:
        section_name = section["section"]
        print(f"\n  [{section_name}]")

        section_toc = []
        process_section_items(
            section["items"],
            RAW_TEXTS,
            chapters,
            section_toc,
            css_item
        )

        if section_toc:
            toc.append((epub.Section(section_name), section_toc))

    # 모든 챕터를 책에 추가
    for chapter in chapters:
        book.add_item(chapter)

    # 목차 설정
    book.toc = toc

    # 네비게이션 파일 추가
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 스파인 설정 (읽기 순서)
    book.spine = ["nav"] + chapters

    # EPUB 파일 저장
    output_path = EPUB_DIR / "연해자평_30일완성.epub"
    EPUB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print("EPUB 파일 생성 중...")
    epub.write_epub(str(output_path), book)

    # 결과 출력
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
