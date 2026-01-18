#!/usr/bin/env python3
"""
인물사전 마크다운 파일 파싱 유틸리티

옵시디언 인물사전 파일(04_Networking/00_인물사전/*.md)에서
구글 시트 CRM 동기화에 필요한 필드를 추출합니다.
"""

import re
import unicodedata
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    import sys
    sys.exit(1)

# ID 생성 유틸리티 import
import sys
sys.path.insert(0, str(Path(__file__).parent))
from id_generator import generate_id_from_path


def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """
    YAML front matter와 본문 분리

    Args:
        content: 마크다운 파일 전체 내용

    Returns:
        (metadata dict, body str)
    """
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        metadata = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        return metadata, body
    except yaml.YAMLError:
        return {}, content


def extract_nickname(body: str) -> str:
    """
    본문에서 닉네임/별명 추출

    Args:
        body: 마크다운 본문

    Returns:
        닉네임 문자열, 없으면 빈 문자열
    """
    nickname_patterns = [
        r'[-*]\s*\*?\*?닉네임\*?\*?:?\s*(.+)',
        r'[-*]\s*\*?\*?별명\*?\*?:?\s*(.+)',
        r'[-*]\s*\*?\*?Nickname\*?\*?:?\s*(.+)',
    ]

    for pattern in nickname_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            nickname = match.group(1).strip()
            # 하이픈(-) 제거 (예: "- **닉네임**: -" 형태 처리)
            if nickname == '-':
                return ""
            return nickname

    return ""


def parse_filename(filepath: Path) -> tuple[str, str, str, str]:
    """
    파일명에서 이름, 소속, 직급 추출 (별명은 본문에서 추출)

    Args:
        filepath: Path 객체

    Returns:
        (이름, 소속, 직급) 튜플

    Examples:
        "신효진_헤드헌터.md" → ("신효진", "헤드헌터", "")
        "서인근_본인.md" → ("서인근", "본인", "")
        "김남규_현대케피코팀장.md" → ("김남규", "현대케피코", "팀장")
        "박혁.md" → ("박혁", "", "")
    """
    stem = filepath.stem
    parts = stem.rsplit('_', 1)

    name = normalize_str(parts[0])
    affiliation = ""
    position = ""

    if len(parts) > 1:
        affiliation_part = normalize_str(parts[1])

        # 직급 패턴 추출 (팀장, 상무, 대표, 매니저, 리더 등)
        position_patterns = [
            r'(팀장|상무|이사|부장|과장|대리|사원|대표|매니저|리더|센터장|본부장|실장|책임)$',
        ]

        for pattern in position_patterns:
            match = re.search(pattern, affiliation_part)
            if match:
                position = match.group(1)
                affiliation = affiliation_part[:match.start()]
                break

        if not position:
            affiliation = affiliation_part

    return name, affiliation, position


def extract_contact_info(metadata: dict, body: str = "") -> dict:
    """
    YAML frontmatter 또는 본문에서 contact 정보 추출

    Args:
        metadata: YAML frontmatter dict
        body: 마크다운 본문 (fallback용)

    Returns:
        {"phone": str, "email": str, "linkedin": str, "github": str}
    """
    contact_info = {
        "phone": "",
        "email": "",
        "linkedin": "",
        "github": ""
    }

    # 1. contact가 dict 형태인 경우 (새 구조 - 우선순위 1)
    if 'contact' in metadata and isinstance(metadata['contact'], dict):
        contact = metadata['contact']
        contact_info["phone"] = contact.get('phone', '')
        contact_info["email"] = contact.get('email', '')
        contact_info["linkedin"] = contact.get('linkedin', '')
        contact_info["github"] = contact.get('github', '')

    # 2. YAML에 없으면 본문에서 추출 시도 (구버전 호환)
    else:
        # 전화번호 패턴
        phone_patterns = [
            r'[-*]\s*\*?\*?전화번호?\*?\*?:?\s*([0-9-]+)',
            r'[-*]\s*\*?\*?연락처\*?\*?:?\s*([0-9-]+)',
            r'[-*]\s*\*?\*?Phone\*?\*?:?\s*([0-9-]+)',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                contact_info["phone"] = match.group(1).strip()
                break

        # 이메일 패턴
        email_patterns = [
            r'[-*]\s*\*?\*?이메일\*?\*?:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'[-*]\s*\*?\*?Email\*?\*?:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        for pattern in email_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                contact_info["email"] = match.group(1).strip()
                break

        # LinkedIn 패턴
        linkedin_patterns = [
            r'[-*]\s*\*?\*?LinkedIn\*?\*?:?\s*\[.*?\]\((https?://[^\)]+)\)',
            r'[-*]\s*\*?\*?LinkedIn\*?\*?:?\s*(https?://\S+)',
        ]
        for pattern in linkedin_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                contact_info["linkedin"] = match.group(1).strip()
                break

        # GitHub 패턴
        github_patterns = [
            r'[-*]\s*\*?\*?GitHub\*?\*?:?\s*\[.*?\]\((https?://[^\)]+)\)',
            r'[-*]\s*\*?\*?GitHub\*?\*?:?\s*(https?://github\.com/\S+)',
        ]
        for pattern in github_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                contact_info["github"] = match.group(1).strip()
                break

    return contact_info


def extract_meeting_dates(content: str) -> list[str]:
    """
    본문에서 미팅 날짜 추출 (## YYYY.MM.DD 패턴)

    Args:
        content: 마크다운 본문

    Returns:
        날짜 문자열 리스트 (YYYY.MM.DD 형식)
    """
    dates = []
    seen_dates = set()

    # 헤딩 패턴 (## YYYY.MM.DD 또는 ### YYYY.MM.DD)
    heading_patterns = [
        r'#{2,3}\s*(\d{4})\.(\d{2})\.(\d{2})',   # ## 2024.11.21
        r'#{2,3}\s*(\d{4})-(\d{2})-(\d{2})',     # ## 2024-11-21
        r'#{2,3}\s*(\d{2})(\d{2})(\d{2})',       # ## 241121 (YYMMDD)
    ]

    for pattern in heading_patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            groups = match.groups()

            # YYMMDD 형식 처리
            if len(groups[0]) == 2:  # YY
                year = f"20{groups[0]}"
                month, day = groups[1], groups[2]
            else:  # YYYY
                year, month, day = groups[0], groups[1], groups[2]

            date_str = f"{year}.{month}.{day}"

            if date_str not in seen_dates:
                seen_dates.add(date_str)
                dates.append(date_str)

    return dates


def get_latest_meeting(dates: list[str]) -> str:
    """
    최근 미팅 날짜 반환 (YYYY-MM-DD 형식)

    Args:
        dates: 날짜 문자열 리스트 (YYYY.MM.DD)

    Returns:
        최근 날짜 (YYYY-MM-DD), 없으면 빈 문자열
    """
    if not dates:
        return ""

    # YYYY.MM.DD → datetime 변환 후 정렬
    parsed_dates = []
    for date_str in dates:
        try:
            dt = datetime.strptime(date_str, "%Y.%m.%d")
            parsed_dates.append(dt)
        except ValueError:
            continue

    if not parsed_dates:
        return ""

    latest = max(parsed_dates)
    return latest.strftime("%Y-%m-%d")


def extract_career_summary(content: str, max_length: int = 200) -> str:
    """
    배경 및 경력 섹션 요약

    Args:
        content: 마크다운 본문
        max_length: 최대 문자 수

    Returns:
        경력 요약 문자열
    """
    # "## 배경 및 경력" 또는 "## 경력" 섹션 찾기
    patterns = [
        r'^##\s*배경\s*및\s*경력\s*$(.*?)^##',
        r'^##\s*경력\s*$(.*?)^##',
        r'^##\s*배경\s*$(.*?)^##',
    ]

    section = ""
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            section = match.group(1).strip()
            break

    if not section:
        return ""

    # 불릿 포인트 제거, 개행을 쉼표+공백으로 치환
    clean = re.sub(r'\n\s*[-*]\s*', ', ', section)
    clean = re.sub(r'\n+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # 최대 길이 제한
    if len(clean) > max_length:
        return clean[:max_length] + "..."

    return clean


def parse_person_file(filepath: Path) -> dict:
    """
    인물 파일 전체 파싱

    Args:
        filepath: 인물 파일 Path 객체

    Returns:
        구글 시트 행 데이터 dict
        {
            "ID": str,  # 파일 경로 기반 해시 ID
            "이름": str,
            "별명": str,
            "소속": str,
            "직급": str,
            "전화번호": str,
            "이메일": str,
            "LinkedIn": str,
            "GitHub": str,
            "최근미팅일자": str,
            "총미팅횟수": int,
            "최종수정일": str,
            "태그": str,  # 쉼표 구분
            "요약": str,
            "주요경력": str,
            "파일경로": str
        }
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        raise ValueError(f"파일 읽기 실패: {e}")

    # YAML front matter 파싱
    metadata, body = parse_yaml_frontmatter(content)

    # ID 추출/생성
    person_id = metadata.get('id', '')
    if not person_id:
        # YAML에 id가 없으면 파일 경로 기반으로 생성
        vault_path = Path("/path/to/vault")
        person_id = generate_id_from_path(filepath, vault_path)

    # 파일명에서 이름/소속/직급 추출
    name, affiliation, position = parse_filename(filepath)

    # YAML에서 title이 있으면 우선 사용
    if 'title' in metadata:
        name = normalize_str(metadata['title'])

        # 1. "님과 링크드인 대화", "님과 대화" 등 제거
        name = re.sub(r'님과\s*(링크드인\s*)?(대화|통화|미팅)', '', name).strip()

        # 2. 괄호 안의 내용 제거 (예: "김선후 (Sunhoo Kim)" → "김선후")
        name = re.sub(r'\s*\([^)]*\)', '', name).strip()

        # 3. 슬래시(/) 구분자 처리 - 첫 번째 이름만 사용
        if ' / ' in name:
            name = name.split(' / ')[0].strip()

        # 4. 직급 추출 (교수, 대표 등)
        position_suffixes = ['교수', '센터장', '본부장', '실장', '국장', '팀장', '부장', '과장']
        for suffix in position_suffixes:
            if name.endswith(suffix):
                # 직급이 비어있을 때만 추출
                if not position:
                    position = suffix
                name = name[:-len(suffix)].strip()
                break

    # 본문에서 별명 추출
    nickname = extract_nickname(body)

    # 태그 추출 (쉼표 구분 문자열로 변환)
    tags = metadata.get('tags', [])
    if isinstance(tags, list):
        tags_str = ', '.join(tags)
    else:
        tags_str = str(tags)

    # 요약
    summary = metadata.get('summary', '')

    # 최종 수정일
    date = metadata.get('date', '')
    if isinstance(date, datetime):
        last_modified = date.strftime("%Y-%m-%d")
    else:
        last_modified = str(date) if date else ""

    # 마지막 연락일
    last_contact = metadata.get('last_contact', '')
    if isinstance(last_contact, datetime):
        last_contact = last_contact.strftime("%Y-%m-%d")
    else:
        last_contact = str(last_contact) if last_contact else ""

    # 연락처 (YAML frontmatter 또는 본문에서 추출)
    contact = extract_contact_info(metadata, body)

    # 미팅 정보
    meeting_dates = extract_meeting_dates(body)
    latest_meeting = get_latest_meeting(meeting_dates)
    meeting_count = len(meeting_dates)

    # 경력 요약
    career = extract_career_summary(body)

    # 파일 경로 (상대 경로)
    try:
        rel_path = filepath.relative_to("/path/to/vault")
        file_path = str(rel_path)
    except ValueError:
        file_path = str(filepath)

    return {
        "ID": person_id,
        "이름": name,
        "별명": nickname,
        "소속": affiliation,
        "직급": position,
        "전화번호": contact.get("phone", ""),
        "이메일": contact.get("email", ""),
        "LinkedIn": contact.get("linkedin", ""),
        "GitHub": contact.get("github", ""),
        "최근미팅일자": latest_meeting,
        "총미팅횟수": meeting_count,
        "마지막연락일": last_contact,
        "최종수정일": last_modified,
        "태그": tags_str,
        "요약": summary,
        "주요경력": career,
        "파일경로": file_path
    }
