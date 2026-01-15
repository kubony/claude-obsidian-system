#!/usr/bin/env python3
"""
인물사전 파일에 last_contact 필드 일괄 업데이트

각 파일의 본문에서 가장 최근 미팅 날짜를 추출하여
YAML frontmatter의 last_contact 필드에 추가합니다.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
import unicodedata

def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """YAML front matter와 본문 분리"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        metadata = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        return metadata, body
    except yaml.YAMLError as e:
        print(f"YAML 파싱 오류: {e}")
        return {}, content


def extract_latest_meeting_date(body: str) -> str | None:
    """본문에서 가장 최근 미팅 날짜 추출"""
    dates = []

    # 헤딩 기반 패턴
    heading_patterns = [
        (r'#{2,3}\s*(\d{4})\.(\d{2})\.(\d{2})', 'full'),      # ## 2024.11.21
        (r'#{2,3}\s*(\d{4})-(\d{2})-(\d{2})', 'full'),        # ## 2024-11-21
        (r'#{2,3}\s*(\d{2})(\d{2})(\d{2})', 'short'),         # ## 241121
    ]

    # 불릿 포인트 기반 패턴
    bullet_patterns = [
        (r'^-\s*(\d{4})\.(\d{2})\.(\d{2})', 'full'),          # - 2024.11.21
        (r'^-\s*(\d{4})-(\d{2})-(\d{2})', 'full'),            # - 2024-11-21
    ]

    def parse_date(groups, fmt):
        """날짜 그룹 파싱"""
        try:
            if fmt == 'short':  # YYMMDD
                year = f"20{groups[0]}"
                month = groups[1]
                day = groups[2]
            else:  # full: YYYY.MM.DD or YYYY-MM-DD
                year = groups[0]
                month = groups[1]
                day = groups[2]

            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            # 유효한 날짜인지 검증
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except (ValueError, IndexError):
            return None

    # 헤딩 패턴 검색
    for pattern, fmt in heading_patterns:
        for match in re.finditer(pattern, body, re.MULTILINE):
            date_str = parse_date(match.groups()[:3], fmt)
            if date_str:
                dates.append(date_str)

    # 불릿 패턴 검색
    for pattern, fmt in bullet_patterns:
        for match in re.finditer(pattern, body, re.MULTILINE):
            date_str = parse_date(match.groups()[:3], fmt)
            if date_str:
                dates.append(date_str)

    # 가장 최근 날짜 반환
    if dates:
        return max(dates)
    return None


def update_file(file_path: Path, dry_run=False) -> dict:
    """파일의 last_contact 필드 업데이트"""
    content = file_path.read_text(encoding='utf-8')
    content = normalize_str(content)

    metadata, body = parse_yaml_frontmatter(content)

    # 가장 최근 미팅 날짜 추출
    latest_date = extract_latest_meeting_date(body)

    result = {
        'file': file_path.name,
        'had_last_contact': 'last_contact' in metadata,
        'old_value': metadata.get('last_contact'),
        'new_value': latest_date,
        'updated': False,
    }

    # 업데이트 필요 여부 확인: 기존 값보다 최신일 때만 업데이트
    if latest_date:
        existing = metadata.get('last_contact')
        existing_str = str(existing) if existing else None
        # 기존 값이 없거나, 새 값이 더 최신인 경우에만 업데이트
        if not existing_str or latest_date > existing_str:
            metadata['last_contact'] = latest_date
            result['updated'] = True

            if not dry_run:
                # YAML frontmatter 재구성
                yaml_str = yaml.dump(metadata, allow_unicode=True, sort_keys=False, default_flow_style=False)
                new_content = f"---\n{yaml_str}---\n\n{body}"
                file_path.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='인물사전 파일의 last_contact 일괄 업데이트')
    parser.add_argument('directory', help='인물사전 디렉토리 경로')
    parser.add_argument('--dry-run', action='store_true', help='실제 파일 수정 없이 미리보기만')
    parser.add_argument('--limit', type=int, help='처리할 파일 수 제한')

    args = parser.parse_args()

    person_dir = Path(args.directory)
    if not person_dir.exists():
        print(f"Error: 디렉토리를 찾을 수 없습니다: {person_dir}")
        sys.exit(1)

    files = sorted(person_dir.glob('*.md'))
    if args.limit:
        files = files[:args.limit]

    print(f"{'[DRY RUN] ' if args.dry_run else ''}총 {len(files)}개 파일 처리 중...\n")

    stats = {
        'total': 0,
        'updated': 0,
        'skipped_no_date': 0,
        'skipped_same': 0,
        'added': 0,
    }

    results = []

    for file_path in files:
        stats['total'] += 1
        result = update_file(file_path, dry_run=args.dry_run)

        if result['updated']:
            stats['updated'] += 1
            if not result['had_last_contact']:
                stats['added'] += 1
            results.append(result)
        elif result['new_value'] is None:
            stats['skipped_no_date'] += 1
        else:
            stats['skipped_same'] += 1

    # 결과 출력
    if results:
        print("\n## 업데이트된 파일:\n")
        for r in results[:20]:  # 처음 20개만 출력
            status = "추가" if not r['had_last_contact'] else "변경"
            old = r['old_value'] or '(없음)'
            print(f"  {r['file']}: {old} → {r['new_value']} ({status})")

        if len(results) > 20:
            print(f"  ... 외 {len(results) - 20}개")

    # 통계 출력
    print(f"\n## 통계:")
    print(f"  - 전체 파일: {stats['total']}개")
    print(f"  - 업데이트됨: {stats['updated']}개")
    print(f"    - 신규 추가: {stats['added']}개")
    print(f"    - 값 변경: {stats['updated'] - stats['added']}개")
    print(f"  - 스킵 (미팅 없음): {stats['skipped_no_date']}개")
    print(f"  - 스킵 (동일): {stats['skipped_same']}개")

    if args.dry_run:
        print("\n[DRY RUN] 실제 파일은 수정되지 않았습니다.")
        print("실제 업데이트하려면 --dry-run 옵션을 제거하세요.")


if __name__ == '__main__':
    main()
