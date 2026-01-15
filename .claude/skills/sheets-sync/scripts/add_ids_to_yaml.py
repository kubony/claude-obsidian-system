#!/usr/bin/env python3
"""
인물사전 파일에 ID 필드 일괄 추가

YAML frontmatter에 id 필드가 없는 파일들을 찾아서
파일 경로 기반 해시 ID를 생성하여 추가합니다.

Usage:
    # Dry-run (미리보기)
    python add_ids_to_yaml.py --dry-run

    # 테스트 (5개만)
    python add_ids_to_yaml.py --limit 5

    # 전체 실행
    python add_ids_to_yaml.py
"""

import argparse
import yaml
import shutil
from pathlib import Path
from id_generator import generate_id_from_path

# 경로 설정
VAULT_PATH = Path("/Users/inkeun/projects/obsidian")
PERSON_DIR = VAULT_PATH / "04_Networking/00_인물사전"


def add_id_to_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    파일에 ID 추가

    Args:
        filepath: 인물 파일 경로
        dry_run: True면 실제 수정 없이 미리보기만

    Returns:
        True if modified, False if skipped
    """
    try:
        # 1. 파일 읽기
        content = filepath.read_text(encoding='utf-8')

        # 2. YAML frontmatter 확인
        if not content.startswith('---'):
            print(f"⚠️  YAML 없음: {filepath.name}")
            return False

        parts = content.split('---', 2)
        if len(parts) < 3:
            print(f"⚠️  잘못된 YAML 형식: {filepath.name}")
            return False

        # 3. YAML 파싱
        try:
            metadata = yaml.safe_load(parts[1])
            if not metadata:
                metadata = {}
        except yaml.YAMLError as e:
            print(f"❌ YAML 파싱 실패: {filepath.name} - {e}")
            return False

        # 4. id 필드 있으면 스킵
        if 'id' in metadata:
            return False

        # 5. ID 생성
        person_id = generate_id_from_path(filepath, VAULT_PATH)

        if dry_run:
            print(f"  [DRY-RUN] {filepath.name} → ID: {person_id}")
            return False

        # 6. YAML에 id 추가 (date 필드 뒤에 삽입)
        # date 필드의 위치 찾기
        keys = list(metadata.keys())
        if 'date' in keys:
            date_idx = keys.index('date')
            # date 뒤에 id 삽입
            new_metadata = {}
            for i, key in enumerate(keys):
                new_metadata[key] = metadata[key]
                if i == date_idx:
                    new_metadata['id'] = person_id
        else:
            # date 없으면 맨 위에 삽입
            new_metadata = {'id': person_id}
            new_metadata.update(metadata)

        # 7. YAML 재구성 (한글 유지, 키 순서 유지)
        new_yaml = yaml.dump(
            new_metadata,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )

        new_content = f"---\n{new_yaml}---{parts[2]}"

        # 8. 백업 생성
        backup_path = filepath.with_suffix('.md.backup')
        shutil.copy2(filepath, backup_path)

        # 9. 파일 쓰기
        filepath.write_text(new_content, encoding='utf-8')
        print(f"✅ {filepath.name} → ID: {person_id}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {filepath.name} - {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='인물사전 파일에 ID 필드 일괄 추가'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 수정 없이 미리보기만 (기본: False)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='처리할 파일 개수 제한 (기본: 전체)'
    )
    args = parser.parse_args()

    # 인물사전 디렉토리 확인
    if not PERSON_DIR.exists():
        print(f"❌ ERROR: 인물사전 디렉토리가 없습니다: {PERSON_DIR}")
        return 1

    # 파일 목록 가져오기 (알파벳순 정렬)
    person_files = sorted(PERSON_DIR.glob("*.md"))

    # .backup 파일 제외
    person_files = [f for f in person_files if not f.suffix == '.backup']

    if args.limit > 0:
        person_files = person_files[:args.limit]

    # 시작 메시지
    print("=" * 60)
    if args.dry_run:
        print("[DRY-RUN 모드] ID 추가 미리보기")
    else:
        print("인물사전 파일 ID 필드 추가 시작")
    print("=" * 60)
    print(f"\n처리 대상: {len(person_files)}개 파일")
    print()

    # 파일 처리
    modified = 0
    skipped = 0

    for filepath in person_files:
        result = add_id_to_file(filepath, args.dry_run)
        if result:
            modified += 1
        else:
            skipped += 1

    # 결과 요약
    print()
    print("=" * 60)
    if args.dry_run:
        print(f"[DRY-RUN 완료] {modified}개 파일이 수정될 예정입니다.")
    else:
        print(f"✅ 완료: {modified}개 파일 수정, {skipped}개 파일 스킵")
        if modified > 0:
            print(f"\n백업 파일: *.md.backup ({modified}개)")
            print("문제 발생 시 백업 파일로 복원 가능")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
