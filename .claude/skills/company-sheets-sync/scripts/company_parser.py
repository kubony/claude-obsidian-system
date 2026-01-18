#!/usr/bin/env python3
"""
법인사전 마크다운 파일 파싱 유틸리티

옵시디언 법인사전 파일(04_Networking/01_법인사전/*.md)에서
구글 시트 CRM 동기화에 필요한 필드를 추출합니다.
"""

import re
import hashlib
import unicodedata
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    import sys
    sys.exit(1)


def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)


def generate_company_id(company_name: str) -> str:
    """
    회사명 기반 해시 ID 생성

    Args:
        company_name: 회사명

    Returns:
        "company_" prefix + 16자 hex hash
    """
    normalized = normalize_str(company_name)
    hash_digest = hashlib.md5(normalized.encode('utf-8')).hexdigest()[:16]
    return f"company_{hash_digest}"


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


def extract_person_list(body: str) -> list[str]:
    """
    본문에서 소속 인물 목록 추출

    Args:
        body: 마크다운 본문

    Returns:
        인물 이름 리스트
    """
    persons = []

    # "## 소속 인물" 섹션 찾기
    section_pattern = r'^##\s*소속\s*인물\s*$(.*?)(?=^##|\Z)'
    match = re.search(section_pattern, body, re.MULTILINE | re.DOTALL)

    if not match:
        return persons

    section = match.group(1).strip()

    # wikilink 패턴: [[이름_소속]] 또는 [[이름]]
    wikilink_pattern = r'\[\[([^\]]+)\]\]'
    for link_match in re.finditer(wikilink_pattern, section):
        link = link_match.group(1)
        # 이름_소속에서 이름만 추출
        name = link.split('_')[0]
        persons.append(normalize_str(name))

    return persons


def parse_company_file(filepath: Path) -> dict:
    """
    법인 파일 전체 파싱

    Args:
        filepath: 법인 파일 Path 객체

    Returns:
        구글 시트 행 데이터 dict
        {
            "ID": str,
            "회사명": str,
            "유형": str,
            "업종": str,
            "설립년도": str,
            "대표자": str,
            "홈페이지": str,
            "소속인원수": int,
            "인물목록": str,  # 쉼표 구분
            "설명": str,
            "최종수정일": str,
            "태그": str,  # 쉼표 구분
            "파일경로": str
        }
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        raise ValueError(f"파일 읽기 실패: {e}")

    # YAML front matter 파싱
    metadata, body = parse_yaml_frontmatter(content)

    # 회사명 (파일명에서 추출)
    company_name = normalize_str(filepath.stem)

    # ID 추출/생성
    company_id = metadata.get('id', '')
    if not company_id:
        company_id = generate_company_id(company_name)

    # 유형
    company_type = metadata.get('type', '기타')

    # 업종
    industry = metadata.get('industry', '기타')

    # 설립년도
    founded = metadata.get('founded', '')
    if founded:
        founded = str(founded)

    # 대표자
    ceo = metadata.get('ceo', '')

    # 홈페이지
    website = metadata.get('website', '')

    # 설명
    description = metadata.get('description', '')

    # 태그 추출 (쉼표 구분 문자열로 변환)
    tags = metadata.get('tags', [])
    if isinstance(tags, list):
        tags_str = ', '.join(tags)
    else:
        tags_str = str(tags)

    # 최종 수정일
    date = metadata.get('date', '')
    if isinstance(date, datetime):
        last_modified = date.strftime("%Y-%m-%d")
    else:
        last_modified = str(date) if date else ""

    # 소속 인물 목록
    persons = extract_person_list(body)
    person_count = len(persons)
    person_list_str = ', '.join(persons[:20])  # 최대 20명까지
    if len(persons) > 20:
        person_list_str += f' 외 {len(persons) - 20}명'

    # 파일 경로 (상대 경로)
    try:
        rel_path = filepath.relative_to("/path/to/vault")
        file_path = str(rel_path)
    except ValueError:
        file_path = str(filepath)

    return {
        "ID": company_id,
        "회사명": company_name,
        "유형": company_type,
        "업종": industry,
        "설립년도": founded,
        "대표자": ceo,
        "홈페이지": website,
        "소속인원수": person_count,
        "인물목록": person_list_str,
        "설명": description,
        "최종수정일": last_modified,
        "태그": tags_str,
        "파일경로": file_path
    }


if __name__ == "__main__":
    # 테스트 코드
    test_dir = Path("/path/to/vault/04_Networking/01_법인사전")

    if test_dir.exists():
        print("=== Company Parser 테스트 ===\n")

        for filepath in list(test_dir.glob("*.md"))[:3]:
            print(f"파일: {filepath.name}")
            try:
                data = parse_company_file(filepath)
                for key, value in data.items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"  에러: {e}")
            print()
    else:
        print(f"법인사전 폴더 없음: {test_dir}")
        print("테스트를 위해 법인사전 파일을 먼저 생성하세요.")
