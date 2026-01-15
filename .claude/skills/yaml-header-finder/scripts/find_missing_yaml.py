#!/usr/bin/env python3
"""
YAML 헤더가 누락된 마크다운 파일을 찾는 스크립트.

Usage:
    python find_missing_yaml.py <directory> [--limit N] [--exclude PATTERN]

Examples:
    python find_missing_yaml.py /path/to/vault/04_Networking
    python find_missing_yaml.py /path/to/vault --limit 10
    python find_missing_yaml.py /path/to/vault --exclude ".obsidian" --exclude "Templates"
"""

import os
import sys
import argparse
from pathlib import Path


def has_yaml_header(file_path: str) -> bool:
    """파일이 YAML 헤더를 가지고 있는지 확인"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 처음 5줄 내에서 YAML 헤더 시작 여부 확인
            for i, line in enumerate(f):
                if i >= 5:  # 최대 5줄까지만 확인
                    break
                stripped = line.strip()
                if stripped == '---':
                    return True
                elif stripped:  # 빈 줄이 아닌 다른 내용이 있으면
                    return False
            return False
    except Exception:
        return True  # 읽기 오류 시 건너뜀


def find_files_without_yaml(
    directory: str,
    limit: int = 0,
    exclude_patterns: list = None
) -> list:
    """YAML 헤더가 없는 마크다운 파일 목록 반환"""
    exclude_patterns = exclude_patterns or []
    # 기본 제외 패턴 (시스템 폴더)
    default_excludes = [
        '.obsidian',    # Obsidian 설정
        '.git',         # Git
        '.venv',        # Python 가상환경
        'node_modules', # Node.js
        'Templates',    # Obsidian 템플릿
        '.claude',      # Claude Code 설정
        '.clinerules',  # Cline 규칙
        '.docs',        # 시스템 문서
        'CLAUDE.md',    # 프로젝트 루트 시스템 파일
    ]
    exclude_patterns.extend(default_excludes)

    missing_yaml = []

    for root, dirs, files in os.walk(directory):
        # 제외할 디렉토리 필터링
        dirs[:] = [d for d in dirs if not any(ex in d for ex in exclude_patterns)]

        for file in files:
            if not file.endswith('.md'):
                continue

            file_path = os.path.join(root, file)

            # 제외 패턴 체크
            if any(ex in file_path for ex in exclude_patterns):
                continue

            if not has_yaml_header(file_path):
                missing_yaml.append(file_path)

                if limit > 0 and len(missing_yaml) >= limit:
                    return missing_yaml

    return missing_yaml


def main():
    parser = argparse.ArgumentParser(
        description='YAML 헤더가 누락된 마크다운 파일 찾기'
    )
    parser.add_argument('directory', help='검색할 디렉토리 경로')
    parser.add_argument('--limit', '-l', type=int, default=0,
                        help='최대 결과 수 (0=무제한)')
    parser.add_argument('--exclude', '-e', action='append', default=[],
                        help='제외할 패턴 (여러 번 사용 가능)')
    parser.add_argument('--count-only', '-c', action='store_true',
                        help='파일 경로 대신 개수만 출력')
    parser.add_argument('--relative', '-r', action='store_true',
                        help='상대 경로로 출력')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    files = find_files_without_yaml(
        args.directory,
        limit=args.limit,
        exclude_patterns=args.exclude
    )

    if args.count_only:
        print(len(files))
    else:
        base_path = Path(args.directory).resolve()
        for f in files:
            if args.relative:
                try:
                    rel_path = Path(f).relative_to(base_path)
                    print(rel_path)
                except ValueError:
                    print(f)
            else:
                print(f)

        # 요약 출력
        print(f"\n총 {len(files)}개 파일에 YAML 헤더가 누락되어 있습니다.", file=sys.stderr)


if __name__ == '__main__':
    main()
