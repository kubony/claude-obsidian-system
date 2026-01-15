#!/usr/bin/env python3
"""
최근 추가/수정된 파일을 찾는 스크립트
git status를 활용하여 untracked(??) 및 modified(M) 파일을 검색
"""

import subprocess
import argparse
import sys
from pathlib import Path


def get_git_status_files(repo_path: str = ".") -> dict:
    """git status에서 파일 목록 추출"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running git status: {e}", file=sys.stderr)
        sys.exit(1)

    files = {
        "untracked": [],      # ?? - 새로 추가된 파일
        "modified": [],       # M  - 수정된 파일 (staged)
        "modified_unstaged": [],  #  M - 수정된 파일 (unstaged)
        "added": [],          # A  - staged된 새 파일
        "deleted": [],        # D  - 삭제된 파일
    }

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        status = line[:2]
        filepath = line[3:].strip()

        # 따옴표 제거 (한글 파일명 등)
        if filepath.startswith('"') and filepath.endswith('"'):
            filepath = filepath[1:-1]
            # Git의 octal escape 디코딩
            filepath = filepath.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')

        if status == "??":
            files["untracked"].append(filepath)
        elif status[0] == "M":
            files["modified"].append(filepath)
        elif status[1] == "M":
            files["modified_unstaged"].append(filepath)
        elif status[0] == "A":
            files["added"].append(filepath)
        elif status[0] == "D" or status[1] == "D":
            files["deleted"].append(filepath)

    return files


def filter_by_extension(files: list, extensions: list) -> list:
    """확장자로 필터링"""
    if not extensions:
        return files
    return [f for f in files if any(f.endswith(ext) for ext in extensions)]


def filter_by_path(files: list, path_patterns: list) -> list:
    """경로 패턴으로 필터링"""
    if not path_patterns:
        return files
    return [f for f in files if any(pattern in f for pattern in path_patterns)]


def filter_person_related(files: list) -> list:
    """인물 관련 파일 필터링 (휴리스틱 기반)"""
    person_indicators = [
        "인물사전",
        "Networking",
        "미팅",
        "커피챗",
        "면접",
        "대화",
        "님",  # ~님 형식의 파일명
        "_책임",
        "_대표",
        "_과장",
        "_팀장",
    ]

    result = []
    for f in files:
        if any(indicator in f for indicator in person_indicators):
            result.append(f)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="최근 추가/수정된 파일을 찾습니다 (git status 기반)"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["all", "untracked", "modified", "added"],
        default="all",
        help="파일 유형 (기본: all)"
    )
    parser.add_argument(
        "--ext", "-e",
        action="append",
        help="필터링할 확장자 (예: .md) - 여러 번 사용 가능"
    )
    parser.add_argument(
        "--path", "-p",
        action="append",
        help="필터링할 경로 패턴 - 여러 번 사용 가능"
    )
    parser.add_argument(
        "--person", "-P",
        action="store_true",
        help="인물 관련 파일만 필터링"
    )
    parser.add_argument(
        "--exclude-obsidian",
        action="store_true",
        default=True,
        help=".obsidian 폴더 제외 (기본: True)"
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Git 저장소 경로 (기본: 현재 디렉토리)"
    )
    parser.add_argument(
        "--count", "-c",
        action="store_true",
        help="파일 개수만 출력"
    )

    args = parser.parse_args()

    # git status 파일 가져오기
    all_files = get_git_status_files(args.repo)

    # 유형별 필터링
    if args.type == "all":
        files = (
            all_files["untracked"] +
            all_files["modified"] +
            all_files["modified_unstaged"] +
            all_files["added"]
        )
    elif args.type == "untracked":
        files = all_files["untracked"]
    elif args.type == "modified":
        files = all_files["modified"] + all_files["modified_unstaged"]
    elif args.type == "added":
        files = all_files["added"]

    # .obsidian 제외
    if args.exclude_obsidian:
        files = [f for f in files if not f.startswith(".obsidian")]

    # 확장자 필터링
    if args.ext:
        files = filter_by_extension(files, args.ext)

    # 경로 패턴 필터링
    if args.path:
        files = filter_by_path(files, args.path)

    # 인물 관련 필터링
    if args.person:
        files = filter_person_related(files)

    # 출력
    if args.count:
        print(len(files))
    else:
        for f in sorted(files):
            print(f)

        if files:
            print(f"\n총 {len(files)}개 파일")


if __name__ == "__main__":
    main()
