#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTML to Markdown Converter for 연해자평 lessons
Converts lesson-XX.html files to markdown format
"""

import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md, MarkdownConverter

class LectureConverter(MarkdownConverter):
    """Custom converter with better table and blockquote handling"""

    def convert_table(self, el, text, convert_as_inline):
        """Preserve table structure properly"""
        return '\n' + md(str(el), heading_style='ATX') + '\n'

def extract_lecture_body(html_path: Path) -> str:
    """Extract content from div.lecture-body"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    lecture_body = soup.find('div', class_='lecture-body')
    if not lecture_body:
        raise ValueError(f"No div.lecture-body found in {html_path}")

    # Remove first h1 (duplicate of header)
    first_h1 = lecture_body.find('h1')
    if first_h1:
        first_h1.decompose()

    # Remove navigation links at the end (다음 강의, 이전 강의)
    for link in lecture_body.find_all('a'):
        href = link.get('href', '')
        if 'lesson-' in href and link.parent.name == 'p':
            link.parent.decompose()

    return str(lecture_body)

def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown"""
    # Use markdownify with custom options
    markdown = md(
        html_content,
        heading_style='ATX',
        bullets='-',
        strip=['div', 'span'],
        code_language='',
    )

    # Clean up excessive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Clean up table formatting
    markdown = re.sub(r'\| +\|', '|', markdown)

    # Ensure proper spacing after headers
    markdown = re.sub(r'(#{1,6} .+)\n([^\n])', r'\1\n\n\2', markdown)

    return markdown.strip()

def get_lesson_title(html_path: Path) -> str:
    """Extract lesson title from HTML"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Get title from header h1
    header_h1 = soup.find('header', class_='lecture-header')
    if header_h1:
        title = header_h1.find('h1')
        if title:
            return title.get_text().strip()

    # Fallback to meta title
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text().split(' - ')[0].strip()

    return f"Lesson {html_path.stem}"

def convert_file(html_path: Path, output_dir: Path, lesson_num: int) -> dict:
    """Convert a single HTML file to markdown"""
    try:
        # Extract lesson title
        title = get_lesson_title(html_path)

        # Extract and convert content
        html_content = extract_lecture_body(html_path)
        markdown_content = html_to_markdown(html_content)

        # Add title as h1
        full_content = f"# {title}\n\n{markdown_content}"

        # Write output file
        output_path = output_dir / f"{lesson_num:02d}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        # Count characters
        char_count = len(full_content)

        return {
            'lesson': lesson_num,
            'input': html_path.name,
            'output': output_path.name,
            'chars': char_count,
            'status': 'success'
        }
    except Exception as e:
        return {
            'lesson': lesson_num,
            'input': html_path.name if html_path else 'N/A',
            'output': 'N/A',
            'chars': 0,
            'status': f'error: {str(e)}'
        }

def main():
    """Main conversion function"""
    # Set paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    html_dir = project_dir / 'theories-static' / 'yeonghaejapyeong'
    output_dir = project_dir / 'raw_texts' / '연해자평' / 'markdown'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("연해자평 HTML → Markdown 변환기")
    print("=" * 60)
    print(f"입력: {html_dir}")
    print(f"출력: {output_dir}")
    print("-" * 60)

    results = []
    total_chars = 0
    success_count = 0

    # Process lessons 1-30
    for i in range(1, 31):
        html_file = html_dir / f"lesson-{i:02d}.html"

        if html_file.exists():
            result = convert_file(html_file, output_dir, i)
            results.append(result)

            if result['status'] == 'success':
                success_count += 1
                total_chars += result['chars']
                print(f"✓ {result['output']}: {result['chars']:,} chars")
            else:
                print(f"✗ lesson-{i:02d}.html: {result['status']}")
        else:
            results.append({
                'lesson': i,
                'input': f'lesson-{i:02d}.html',
                'output': 'N/A',
                'chars': 0,
                'status': 'file not found'
            })
            print(f"✗ lesson-{i:02d}.html: 파일 없음")

    # Summary
    print("-" * 60)
    print(f"변환 완료: {success_count}/30 파일")
    print(f"총 글자수: {total_chars:,}")
    print(f"평균 글자수: {total_chars // max(success_count, 1):,}")
    print("=" * 60)

    return results

if __name__ == '__main__':
    main()
