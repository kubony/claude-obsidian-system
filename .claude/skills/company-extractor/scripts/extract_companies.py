#!/usr/bin/env python3
"""
회사 목록 추출 스크립트

인물사전 파일(04_Networking/00_인물사전/*.md)에서
회사/조직 목록을 추출하고 집계합니다.
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict


# 제외할 소속 목록 (비법인)
EXCLUDE_AFFILIATIONS = {
    '가족',
    '간병',
    '본인',
    '기타',
    '개인셀러',
    'ASC강사',
    '못디동기',
    '친구',
    '지인',
    '교회',
}

# 직장명에서 제외할 패턴 (일반적인 설명 제거)
COMPANY_CLEANUP_PATTERNS = [
    r'독일\s+',      # "독일 머크" → "머크"
    r'한국지사',     # "머크 한국지사" → "머크"
    r'\s+한국$',     # "XX 한국" → "XX"
]


def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)


def parse_filename(filepath: Path) -> tuple[str, str]:
    """
    파일명에서 이름과 소속 추출

    Args:
        filepath: Path 객체

    Returns:
        (이름, 소속) 튜플

    Examples:
        "김종호_누비랩.md" → ("김종호", "누비랩")
        "박혁.md" → ("박혁", "")
    """
    stem = normalize_str(filepath.stem)
    parts = stem.rsplit('_', 1)

    name = parts[0]
    affiliation = parts[1] if len(parts) > 1 else ""

    return name, affiliation


def clean_company_name(company: str) -> str:
    """
    직장명에서 불필요한 수식어 제거

    Args:
        company: 원본 직장명

    Returns:
        정리된 회사명

    Examples:
        "독일 머크 한국지사" → "머크"
        "현대자동차" → "현대자동차"
    """
    result = company.strip()
    for pattern in COMPANY_CLEANUP_PATTERNS:
        result = re.sub(pattern, '', result)
    return result.strip()


def extract_company_from_content(filepath: Path) -> str:
    """
    파일 내용에서 직장 정보 추출

    Args:
        filepath: 인물사전 파일 경로

    Returns:
        추출된 회사명 (없으면 빈 문자열)

    파싱 우선순위:
    1. 본문의 "**직장**:" 또는 "- **직장**:" 패턴
    2. YAML tags에서 회사명 추출 (향후 확장 가능)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        content = normalize_str(content)

        # 패턴 1: "**직장**: 회사명" 또는 "- **직장**: 회사명"
        patterns = [
            r'\*\*직장\*\*:\s*(.+?)(?:\n|$)',
            r'-\s*\*\*직장\*\*:\s*(.+?)(?:\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                company = match.group(1).strip()
                return clean_company_name(company)

        return ""

    except Exception:
        return ""


def should_exclude(affiliation: str) -> bool:
    """
    제외 대상 소속인지 확인

    Args:
        affiliation: 소속명

    Returns:
        제외해야 하면 True
    """
    if not affiliation:
        return True

    normalized = normalize_str(affiliation.lower())

    for exclude in EXCLUDE_AFFILIATIONS:
        if normalize_str(exclude.lower()) in normalized:
            return True

    return False


def extract_companies(
    person_dir: Path,
    company_dir: Path,
    min_count: int = 1
) -> dict:
    """
    인물사전에서 회사 목록 추출

    Args:
        person_dir: 인물사전 폴더 경로
        company_dir: 법인사전 폴더 경로
        min_count: 최소 인원수 필터

    Returns:
        {
            "companies": [...],
            "total_companies": int,
            "new_companies": int,
            "excluded": [...]
        }
    """
    # 회사별 인물 집계
    company_persons = defaultdict(list)
    excluded_affiliations = set()
    content_extracted = []  # 본문에서 추출된 케이스 추적

    # 인물사전 파일 스캔
    for filepath in person_dir.glob("*.md"):
        name, affiliation = parse_filename(filepath)

        # 파일명 소속이 비법인인 경우 본문에서 직장 정보 추출 시도
        if should_exclude(affiliation):
            content_company = extract_company_from_content(filepath)
            if content_company and not should_exclude(content_company):
                # 본문에서 유효한 회사명 추출됨
                company_persons[content_company].append(name)
                content_extracted.append(f"{name}: {affiliation} → {content_company}")
                continue
            # 본문에서도 추출 실패 → 제외
            if affiliation:
                excluded_affiliations.add(affiliation)
            continue

        company_persons[affiliation].append(name)

    # 기존 법인사전 파일 목록
    existing_companies = set()
    if company_dir.exists():
        for filepath in company_dir.glob("*.md"):
            company_name = normalize_str(filepath.stem)
            existing_companies.add(company_name)

    # 회사 목록 생성
    companies = []
    for company_name, persons in company_persons.items():
        if len(persons) < min_count:
            continue

        is_new = company_name not in existing_companies

        companies.append({
            "name": company_name,
            "person_count": len(persons),
            "persons": sorted(persons),
            "is_new": is_new
        })

    # 인원수 기준 내림차순 정렬
    companies.sort(key=lambda x: (-x["person_count"], x["name"]))

    # 신규 회사 수 계산
    new_count = sum(1 for c in companies if c["is_new"])

    return {
        "companies": companies,
        "total_companies": len(companies),
        "new_companies": new_count,
        "excluded": sorted(excluded_affiliations),
        "content_extracted": content_extracted  # 본문에서 추출된 케이스
    }


def format_table(result: dict) -> str:
    """테이블 형식으로 출력"""
    lines = []
    lines.append("| 회사명 | 인원수 | 신규 |")
    lines.append("|--------|--------|------|")

    for company in result["companies"]:
        new_mark = "O" if company["is_new"] else "-"
        lines.append(f"| {company['name']} | {company['person_count']} | {new_mark} |")

    lines.append("")
    lines.append(f"총 {result['total_companies']}개 회사, 신규 {result['new_companies']}개")
    lines.append(f"제외된 소속: {', '.join(result['excluded'])}")

    # 본문에서 추출된 케이스 출력
    if result.get("content_extracted"):
        lines.append("")
        lines.append("본문에서 추출된 소속:")
        for item in result["content_extracted"]:
            lines.append(f"  - {item}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="인물사전에서 회사 목록 추출"
    )
    parser.add_argument(
        "--person-dir",
        type=Path,
        default=Path("/path/to/vault/04_Networking/00_인물사전"),
        help="인물사전 폴더 경로"
    )
    parser.add_argument(
        "--company-dir",
        type=Path,
        default=Path("/path/to/vault/04_Networking/01_법인사전"),
        help="법인사전 폴더 경로"
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="최소 인원수 필터 (기본: 1)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="출력 형식 (기본: json)"
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="신규 회사만 출력"
    )

    args = parser.parse_args()

    # 회사 목록 추출
    result = extract_companies(
        person_dir=args.person_dir,
        company_dir=args.company_dir,
        min_count=args.min_count
    )

    # 신규 회사만 필터링
    if args.new_only:
        result["companies"] = [c for c in result["companies"] if c["is_new"]]
        result["total_companies"] = len(result["companies"])

    # 출력
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_table(result))


if __name__ == "__main__":
    main()
