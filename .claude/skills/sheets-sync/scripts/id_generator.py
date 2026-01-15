#!/usr/bin/env python3
"""
ID 생성 유틸리티

파일 경로 기반 해시 ID를 생성하여 인물사전 파일을 고유하게 식별합니다.
"""

import hashlib
from pathlib import Path


def generate_id_from_path(filepath: Path, vault_path: Path) -> str:
    """
    파일 경로 기반 해시 ID 생성

    Args:
        filepath: 인물 파일의 전체 경로
        vault_path: Vault 루트 경로

    Returns:
        str: "person_" prefix + 16자 hex hash

    Example:
        >>> filepath = Path("/Users/inkeun/projects/obsidian/04_Networking/00_인물사전/김태훈_앤틀러7기.md")
        >>> vault_path = Path("/Users/inkeun/projects/obsidian")
        >>> generate_id_from_path(filepath, vault_path)
        'person_a1b2c3d4e5f6g7h8'

    특징:
        - 파일 이동/이름 변경에 독립적 (경로 기반)
        - 충돌 확률 극히 낮음 (MD5 16자)
        - YAML에 명시적 저장하여 추적 가능
    """
    try:
        # 상대 경로 생성
        rel_path = str(filepath.relative_to(vault_path))
    except ValueError:
        # vault_path의 하위 경로가 아닌 경우, 절대 경로 사용
        rel_path = str(filepath.absolute())

    # MD5 해시 생성 (16자)
    hash_digest = hashlib.md5(rel_path.encode('utf-8')).hexdigest()[:16]

    return f"person_{hash_digest}"


def validate_unique_ids(person_data_list: list[dict]) -> tuple[bool, list[str]]:
    """
    ID 중복 검증 (해시 충돌 체크)

    Args:
        person_data_list: 인물 데이터 딕셔너리 리스트 (각각 'ID' 키 포함)

    Returns:
        tuple[bool, list[str]]: (중복 없으면 True, 중복 ID 목록)

    Example:
        >>> data = [
        ...     {"ID": "person_abc123", "이름": "김철수"},
        ...     {"ID": "person_def456", "이름": "이영희"},
        ...     {"ID": "person_abc123", "이름": "박민수"},  # 중복!
        ... ]
        >>> is_unique, duplicates = validate_unique_ids(data)
        >>> is_unique
        False
        >>> duplicates
        ['person_abc123']
    """
    ids = [person.get('ID', '') for person in person_data_list if person.get('ID')]

    # 중복 ID 찾기
    id_counts = {}
    for person_id in ids:
        id_counts[person_id] = id_counts.get(person_id, 0) + 1

    duplicates = [pid for pid, count in id_counts.items() if count > 1]

    return (len(duplicates) == 0, duplicates)


def generate_collision_free_id(base_id: str, existing_ids: set[str]) -> str:
    """
    충돌 없는 ID 생성 (suffix 추가)

    Args:
        base_id: 기본 ID
        existing_ids: 이미 사용 중인 ID 집합

    Returns:
        str: 충돌 없는 ID (필요시 "-2", "-3" suffix 추가)

    Example:
        >>> existing = {"person_abc123", "person_abc123-2"}
        >>> generate_collision_free_id("person_abc123", existing)
        'person_abc123-3'
    """
    if base_id not in existing_ids:
        return base_id

    # suffix 번호 증가
    counter = 2
    while f"{base_id}-{counter}" in existing_ids:
        counter += 1

    return f"{base_id}-{counter}"


if __name__ == "__main__":
    # 테스트 코드
    vault = Path("/Users/inkeun/projects/obsidian")
    test_file = vault / "04_Networking/00_인물사전/김태훈_앤틀러7기.md"

    print("=== ID Generator 테스트 ===")
    print(f"파일: {test_file.name}")
    print(f"생성된 ID: {generate_id_from_path(test_file, vault)}")
    print()

    # 중복 검증 테스트
    test_data = [
        {"ID": "person_abc123", "이름": "김철수"},
        {"ID": "person_def456", "이름": "이영희"},
        {"ID": "person_ghi789", "이름": "박민수"},
    ]

    is_unique, duplicates = validate_unique_ids(test_data)
    print(f"중복 검증: {'✅ 통과' if is_unique else '❌ 실패'}")
    if duplicates:
        print(f"중복 ID: {duplicates}")
