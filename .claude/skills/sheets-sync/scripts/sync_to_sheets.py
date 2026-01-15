#!/usr/bin/env python3
"""
인물사전 → 구글시트 동기화 메인 스크립트

옵시디언 볼트의 인물사전 마크다운 파일들을 파싱하여
구글 시트 CRM으로 동기화합니다.

Usage:
    source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
      python /Users/inkeun/projects/obsidian/.claude/skills/sheets-sync/scripts/sync_to_sheets.py
"""

import os
import sys
import locale
from pathlib import Path
from dotenv import load_dotenv

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
VAULT_PATH = Path("/Users/inkeun/projects/obsidian")
PERSON_DIR = VAULT_PATH / "04_Networking/00_인물사전"
SKILL_DIR = SCRIPT_DIR.parent  # .claude/skills/sheets-sync

# person_parser 모듈 import
sys.path.insert(0, str(SCRIPT_DIR))
from person_parser import parse_person_file

# GoogleSheetAPIManager import (로컬 google_api 패키지)
sys.path.insert(0, str(SKILL_DIR))
try:
    from google_api.sheets import GoogleSheetAPIManager
except ImportError as e:
    print("❌ ERROR: google_api 패키지를 찾을 수 없습니다.")
    print(f"경로 확인: {SKILL_DIR / 'google_api'}")
    print(f"상세 오류: {e}")
    sys.exit(1)

# 환경변수 로드
load_dotenv(VAULT_PATH / ".env")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

# 컬럼 순서 (17개 필드)
COLUMNS = [
    "ID", "이름", "별명", "소속", "직급",
    "전화번호", "이메일", "LinkedIn", "GitHub",
    "최근미팅일자", "총미팅횟수", "마지막연락일", "최종수정일",
    "태그", "요약", "주요경력", "파일경로"
]


def authenticate_google_sheets():
    """
    구글 시트 인증

    Returns:
        GoogleSheetAPIManager 인스턴스

    Raises:
        SystemExit: 인증 실패 시
    """
    # 환경변수 확인
    if not GOOGLE_SHEET_ID:
        print("❌ ERROR: GOOGLE_SHEET_ID 환경변수가 설정되지 않았습니다.")
        print(f".env 파일 확인: {VAULT_PATH / '.env'}")
        sys.exit(1)

    if not CREDENTIALS_PATH:
        print("❌ ERROR: GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        print(f".env 파일 확인: {VAULT_PATH / '.env'}")
        sys.exit(1)

    # JSON 키 파일 확인
    creds_file = Path(CREDENTIALS_PATH)
    if not creds_file.exists():
        print(f"❌ ERROR: 구글 서비스 계정 JSON 파일이 없습니다.")
        print(f"경로 확인: {CREDENTIALS_PATH}")
        sys.exit(1)

    try:
        # 구글 시트 인증
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        manager = GoogleSheetAPIManager(
            key_file=CREDENTIALS_PATH,
            scopes=scopes
        )
        manager.set_spreadsheet_id(GOOGLE_SHEET_ID)

        print("✅ 구글시트 인증 완료")
        return manager

    except FileNotFoundError:
        print(f"❌ ERROR: JSON 키 파일을 찾을 수 없습니다: {CREDENTIALS_PATH}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ ERROR: 구글시트 접근 실패: {e}")
        sys.exit(1)


def fetch_person_data() -> list[dict]:
    """
    모든 인물 파일 파싱

    Returns:
        인물 데이터 딕셔너리 리스트
    """
    if not PERSON_DIR.exists():
        print(f"❌ ERROR: 인물사전 디렉토리가 없습니다: {PERSON_DIR}")
        sys.exit(1)

    person_files = list(PERSON_DIR.glob("*.md"))
    print(f"📂 인물 파일 {len(person_files)}개 발견")

    rows = []
    errors = []

    for filepath in person_files:
        try:
            data = parse_person_file(filepath)
            rows.append(data)
        except Exception as e:
            errors.append((filepath.name, str(e)))
            continue  # 다음 파일 계속 처리

    if errors:
        print(f"\n⚠️  WARNING: {len(errors)}개 파일 파싱 실패:")
        for filename, error in errors[:5]:  # 최대 5개만 표시
            print(f"  - {filename}: {error}")
        if len(errors) > 5:
            print(f"  ... 외 {len(errors) - 5}개")

    print(f"✅ {len(rows)}명 파싱 완료")
    return rows


def sort_by_korean_name(rows: list[dict]) -> list[dict]:
    """
    이름 가나다순 정렬 (한글 → 영문)

    Args:
        rows: 인물 데이터 리스트

    Returns:
        정렬된 리스트
    """
    try:
        # macOS 한글 로케일 설정 시도
        try:
            locale.setlocale(locale.LC_COLLATE, 'ko_KR.UTF-8')
            use_locale = True
        except locale.Error:
            # 로케일 설정 실패 시 기본 정렬
            use_locale = False
            print("⚠️  WARNING: 한글 로케일 설정 실패, 기본 정렬 사용")

        if use_locale:
            sorted_rows = sorted(rows, key=lambda x: locale.strxfrm(x["이름"]))
        else:
            # 기본 유니코드 정렬 (한글 → 영문 순서 보장)
            sorted_rows = sorted(rows, key=lambda x: x["이름"])

        return sorted_rows

    except Exception as e:
        print(f"⚠️  WARNING: 정렬 실패, 원본 순서 사용: {e}")
        return rows


def build_id_mapping(manager: GoogleSheetAPIManager) -> dict[str, int]:
    """
    기존 시트의 ID → 행번호 매핑

    Args:
        manager: GoogleSheetAPIManager 인스턴스

    Returns:
        {"person_abc123": 2, "person_def456": 3, ...}
        ID가 없는 행은 매핑에 포함되지 않음
    """
    try:
        # A2:A1000 범위에서 기존 ID 읽기
        existing_data = manager.get_values("시트1!A2:A1000")

        if not existing_data:
            return {}

        id_to_row = {}
        for idx, row in enumerate(existing_data, start=2):
            if row and row[0]:  # ID 값이 있으면
                id_to_row[row[0]] = idx

        return id_to_row

    except Exception as e:
        # 시트가 비어있거나 A열이 없는 경우 빈 dict 반환
        print(f"⚠️  WARNING: ID 매핑 읽기 실패 (첫 동기화일 수 있음): {e}")
        return {}


def sync_sheet_incremental(manager: GoogleSheetAPIManager, data: list[dict]):
    """
    ID 기반 증분 동기화

    기존 행은 업데이트, 신규 인물은 추가
    사용자의 필터/정렬이 유지됨

    Args:
        manager: GoogleSheetAPIManager 인스턴스
        data: 인물 데이터 리스트
    """
    try:
        print("🔄 시트 업데이트 중 (ID 기반 증분 동기화)...")

        # 1. 기존 ID 매핑 읽기
        id_to_row = build_id_mapping(manager)

        # 2. 데이터 분류 (업데이트 vs 추가)
        to_update = []  # (row_num, person) tuples
        to_append = []  # person dicts

        for person in data:
            person_id = person.get('ID', '')
            if not person_id:
                print(f"⚠️  WARNING: ID 없는 인물 스킵: {person.get('이름', 'Unknown')}")
                continue

            if person_id in id_to_row:
                row_num = id_to_row[person_id]
                to_update.append((row_num, person))
            else:
                to_append.append(person)

        # 3. 배치 업데이트 (기존 행)
        if to_update:
            batch_data = []
            for row_num, person in to_update:
                row_values = [person.get(col, "") for col in COLUMNS]
                # 총미팅횟수 int → str 변환 (index 10)
                row_values[10] = str(row_values[10]) if row_values[10] else "0"

                batch_data.append({
                    'range': f'시트1!A{row_num}:Q{row_num}',
                    'values': [row_values]
                })

            # batch_update_values 호출
            manager.batch_update_values(batch_data)
            print(f"  ✓ {len(to_update)}행 업데이트")

        # 4. 신규 행 추가
        if to_append:
            # 다음 빈 행 번호 계산
            next_row = max(id_to_row.values()) + 1 if id_to_row else 2
            append_values = []

            for person in to_append:
                row_values = [person.get(col, "") for col in COLUMNS]
                # 총미팅횟수 int → str 변환 (index 10)
                row_values[10] = str(row_values[10]) if row_values[10] else "0"
                append_values.append(row_values)

            end_row = next_row + len(to_append) - 1
            manager.update_values(
                range_name=f'시트1!A{next_row}:Q{end_row}',
                values=append_values,
                major_dimension="ROWS"
            )
            print(f"  ✓ {len(to_append)}행 추가")

        print(f"✅ 시트 동기화 완료: {len(to_update)}행 업데이트, {len(to_append)}행 추가")

    except Exception as e:
        print(f"❌ ERROR: 시트 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """메인 함수"""
    print("=" * 60)
    print("인물사전 → 구글시트 동기화 시작")
    print("=" * 60)
    print()

    # 1. 구글 시트 인증
    manager = authenticate_google_sheets()

    # 2. 인물 파일 파싱
    data = fetch_person_data()

    if not data:
        print("❌ ERROR: 파싱된 데이터가 없습니다.")
        sys.exit(1)

    # 3. 데이터 정렬 (이름 가나다순)
    sorted_data = sort_by_korean_name(data)

    # 4. 시트 업데이트 (ID 기반 증분 동기화)
    sync_sheet_incremental(manager, sorted_data)

    # 5. 성공 메시지
    print()
    print("=" * 60)
    print(f"✅ 완료: {len(sorted_data)}명의 정보를 구글시트에 동기화했습니다.")
    print(f"시트 URL: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
