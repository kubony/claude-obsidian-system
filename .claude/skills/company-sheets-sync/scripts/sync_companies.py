#!/usr/bin/env python3
"""
법인사전 → 구글시트 동기화 메인 스크립트

옵시디언 볼트의 법인사전 마크다운 파일들을 파싱하여
구글 시트 CRM의 '법인사전' 탭으로 동기화합니다.

Usage:
    source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
      python /Users/inkeun/projects/obsidian/.claude/skills/company-sheets-sync/scripts/sync_companies.py
"""

import os
import sys
import locale
from pathlib import Path
from dotenv import load_dotenv

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
VAULT_PATH = Path("/Users/inkeun/projects/obsidian")
COMPANY_DIR = VAULT_PATH / "04_Networking/01_법인사전"
SKILL_DIR = SCRIPT_DIR.parent  # .claude/skills/company-sheets-sync

# company_parser 모듈 import
sys.path.insert(0, str(SCRIPT_DIR))
from company_parser import parse_company_file

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

# 시트 탭 이름
SHEET_TAB_NAME = "법인사전"

# 컬럼 순서 (13개 필드)
COLUMNS = [
    "ID", "회사명", "유형", "업종", "설립년도",
    "대표자", "홈페이지", "소속인원수", "인물목록",
    "설명", "최종수정일", "태그", "파일경로"
]


def authenticate_google_sheets():
    """
    구글 시트 인증

    Returns:
        GoogleSheetAPIManager 인스턴스

    Raises:
        SystemExit: 인증 실패 시
    """
    if not GOOGLE_SHEET_ID:
        print("❌ ERROR: GOOGLE_SHEET_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    if not CREDENTIALS_PATH:
        print("❌ ERROR: GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    creds_file = Path(CREDENTIALS_PATH)
    if not creds_file.exists():
        print(f"❌ ERROR: 구글 서비스 계정 JSON 파일이 없습니다: {CREDENTIALS_PATH}")
        sys.exit(1)

    try:
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

    except Exception as e:
        print(f"❌ ERROR: 구글시트 접근 실패: {e}")
        sys.exit(1)


def ensure_sheet_tab_exists(manager: GoogleSheetAPIManager):
    """
    '법인사전' 탭 존재 확인 및 생성

    Args:
        manager: GoogleSheetAPIManager 인스턴스
    """
    try:
        # 시트 메타데이터 조회
        spreadsheet = manager.sheet_service.spreadsheets().get(
            spreadsheetId=GOOGLE_SHEET_ID
        ).execute()

        # 기존 탭 목록 확인
        sheets = spreadsheet.get('sheets', [])
        tab_names = [sheet['properties']['title'] for sheet in sheets]

        if SHEET_TAB_NAME in tab_names:
            print(f"✅ '{SHEET_TAB_NAME}' 탭 존재 확인")
            return

        # 탭 생성
        print(f"📝 '{SHEET_TAB_NAME}' 탭 생성 중...")

        request = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': SHEET_TAB_NAME
                    }
                }
            }]
        }

        manager.sheet_service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body=request
        ).execute()

        # 헤더 행 추가
        manager.update_values(
            range_name=f'{SHEET_TAB_NAME}!A1:M1',
            values=[COLUMNS],
            major_dimension="ROWS"
        )

        print(f"✅ '{SHEET_TAB_NAME}' 탭 생성 완료")

    except Exception as e:
        print(f"❌ ERROR: 탭 생성/확인 실패: {e}")
        sys.exit(1)


def fetch_company_data() -> list[dict]:
    """
    모든 법인 파일 파싱

    Returns:
        법인 데이터 딕셔너리 리스트
    """
    if not COMPANY_DIR.exists():
        print(f"⚠️  WARNING: 법인사전 디렉토리가 없습니다: {COMPANY_DIR}")
        return []

    company_files = list(COMPANY_DIR.glob("*.md"))
    print(f"📂 법인 파일 {len(company_files)}개 발견")

    if not company_files:
        return []

    rows = []
    errors = []

    for filepath in company_files:
        try:
            data = parse_company_file(filepath)
            rows.append(data)
        except Exception as e:
            errors.append((filepath.name, str(e)))
            continue

    if errors:
        print(f"\n⚠️  WARNING: {len(errors)}개 파일 파싱 실패:")
        for filename, error in errors[:5]:
            print(f"  - {filename}: {error}")
        if len(errors) > 5:
            print(f"  ... 외 {len(errors) - 5}개")

    print(f"✅ {len(rows)}개 법인 파싱 완료")
    return rows


def sort_by_korean_name(rows: list[dict]) -> list[dict]:
    """
    회사명 가나다순 정렬 (한글 → 영문)
    """
    try:
        try:
            locale.setlocale(locale.LC_COLLATE, 'ko_KR.UTF-8')
            use_locale = True
        except locale.Error:
            use_locale = False

        if use_locale:
            sorted_rows = sorted(rows, key=lambda x: locale.strxfrm(x["회사명"]))
        else:
            sorted_rows = sorted(rows, key=lambda x: x["회사명"])

        return sorted_rows

    except Exception:
        return rows


def build_id_mapping(manager: GoogleSheetAPIManager) -> dict[str, int]:
    """
    기존 시트의 ID → 행번호 매핑

    Args:
        manager: GoogleSheetAPIManager 인스턴스

    Returns:
        {"company_abc123": 2, "company_def456": 3, ...}
    """
    try:
        existing_data = manager.get_values(f"{SHEET_TAB_NAME}!A2:A500")

        if not existing_data:
            return {}

        id_to_row = {}
        for idx, row in enumerate(existing_data, start=2):
            if row and row[0]:
                id_to_row[row[0]] = idx

        return id_to_row

    except Exception as e:
        print(f"⚠️  WARNING: ID 매핑 읽기 실패: {e}")
        return {}


def sync_sheet_incremental(manager: GoogleSheetAPIManager, data: list[dict]):
    """
    ID 기반 증분 동기화

    Args:
        manager: GoogleSheetAPIManager 인스턴스
        data: 법인 데이터 리스트
    """
    try:
        print("🔄 시트 업데이트 중 (ID 기반 증분 동기화)...")

        # 1. 기존 ID 매핑 읽기
        id_to_row = build_id_mapping(manager)

        # 2. 데이터 분류
        to_update = []
        to_append = []

        for company in data:
            company_id = company.get('ID', '')
            if not company_id:
                print(f"⚠️  WARNING: ID 없는 법인 스킵: {company.get('회사명', 'Unknown')}")
                continue

            if company_id in id_to_row:
                row_num = id_to_row[company_id]
                to_update.append((row_num, company))
            else:
                to_append.append(company)

        # 3. 배치 업데이트 (기존 행)
        if to_update:
            batch_data = []
            for row_num, company in to_update:
                row_values = [str(company.get(col, "")) for col in COLUMNS]

                batch_data.append({
                    'range': f'{SHEET_TAB_NAME}!A{row_num}:M{row_num}',
                    'values': [row_values]
                })

            manager.batch_update_values(batch_data)
            print(f"  ✓ {len(to_update)}행 업데이트")

        # 4. 신규 행 추가
        if to_append:
            next_row = max(id_to_row.values()) + 1 if id_to_row else 2
            append_values = []

            for company in to_append:
                row_values = [str(company.get(col, "")) for col in COLUMNS]
                append_values.append(row_values)

            end_row = next_row + len(to_append) - 1
            manager.update_values(
                range_name=f'{SHEET_TAB_NAME}!A{next_row}:M{end_row}',
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
    print("법인사전 → 구글시트 동기화 시작")
    print("=" * 60)
    print()

    # 1. 구글 시트 인증
    manager = authenticate_google_sheets()

    # 2. '법인사전' 탭 확인/생성
    ensure_sheet_tab_exists(manager)

    # 3. 법인 파일 파싱
    data = fetch_company_data()

    if not data:
        print("ℹ️  동기화할 법인 데이터가 없습니다.")
        print("법인사전 파일을 먼저 생성하세요: 04_Networking/01_법인사전/")
        return

    # 4. 데이터 정렬 (회사명 가나다순)
    sorted_data = sort_by_korean_name(data)

    # 5. 시트 업데이트 (ID 기반 증분 동기화)
    sync_sheet_incremental(manager, sorted_data)

    # 6. 성공 메시지
    print()
    print("=" * 60)
    print(f"✅ 완료: {len(sorted_data)}개 법인 정보를 구글시트에 동기화했습니다.")
    print(f"시트 URL: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
    print(f"탭: {SHEET_TAB_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
