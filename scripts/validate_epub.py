#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import zipfile
import re
from pathlib import Path

epub_path = Path(__file__).parent.parent / 'epub' / '각방제어_온도조절_시스템_완전가이드.epub'
errors = []
warnings = []

with zipfile.ZipFile(str(epub_path)) as z:
    names = set(z.namelist())

    # 1. mimetype
    if 'mimetype' not in names:
        errors.append('mimetype 파일 없음')
    else:
        mt = z.read('mimetype').decode()
        if mt.strip() != 'application/epub+zip':
            errors.append(f'mimetype 내용 오류: {mt}')
        else:
            print('[OK] mimetype 정상')

    # 2. container.xml
    if 'META-INF/container.xml' not in names:
        errors.append('META-INF/container.xml 없음')
    else:
        print('[OK] META-INF/container.xml 존재')

    # 3. OPF
    container = z.read('META-INF/container.xml').decode()
    opf_match = re.search(r'full-path="([^"]+)"', container)
    if not opf_match:
        errors.append('OPF 경로를 container.xml에서 찾을 수 없음')
        sys.exit(1)

    opf_path = opf_match.group(1)
    if opf_path not in names:
        errors.append(f'OPF 파일 없음: {opf_path}')
    else:
        print(f'[OK] OPF 파일: {opf_path}')
        opf = z.read(opf_path).decode()

        # 4. 필수 메타데이터
        for tag in ['dc:title', 'dc:language', 'dc:identifier']:
            if tag in opf:
                print(f'[OK] {tag} 존재')
            else:
                errors.append(f'{tag} 없음')

        # 5. 표지
        if 'cover' in opf.lower():
            print('[OK] 표지(cover) 메타데이터 존재')
        else:
            warnings.append('표지 메타데이터 없음')

        # 6. manifest 파일 존재 확인
        href_items = re.findall(r'href="([^"]+)"', opf)
        opf_dir = str(Path(opf_path).parent).replace('\\', '/')
        if opf_dir == '.':
            opf_dir = ''
        missing = []
        for item in href_items:
            if opf_dir:
                full = opf_dir + '/' + item
            else:
                full = item
            if full not in names and item not in names:
                missing.append(item)
        if missing:
            for m in missing[:5]:
                errors.append(f'manifest 참조 파일 없음: {m}')
        else:
            print(f'[OK] manifest {len(href_items)}개 파일 모두 존재')

    # 7. nav.xhtml
    nav_files = [n for n in names if 'nav' in n.lower() and n.endswith('.xhtml')]
    if nav_files:
        print(f'[OK] nav 파일: {nav_files[0]}')
    else:
        warnings.append('nav.xhtml 없음 (ePub3 권장)')

    # 8. NCX (ePub2 하위호환)
    ncx_files = [n for n in names if n.endswith('.ncx')]
    if ncx_files:
        print(f'[OK] NCX 파일: {ncx_files[0]}')

    # 9. 표지 이미지
    cover_files = [n for n in names if 'cover' in n.lower() and n.endswith(('.jpg', '.jpeg', '.png'))]
    if cover_files:
        print(f'[OK] 표지 이미지: {cover_files[0]}')
    else:
        warnings.append('표지 이미지 없음')

print()
if errors:
    print(f'오류 {len(errors)}건:')
    for e in errors:
        print(f'  [ERROR] {e}')
else:
    print('오류 없음 — 플랫폼 제출 가능 수준')

if warnings:
    print(f'경고 {len(warnings)}건:')
    for w in warnings:
        print(f'  [WARN]  {w}')

print()
print(f'파일 수: {len(names)}개  |  크기: {epub_path.stat().st_size:,} bytes')
