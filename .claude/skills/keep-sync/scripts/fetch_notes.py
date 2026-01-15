#!/usr/bin/env python3
"""
Google Keep 메모 가져오기 스크립트 (gkeepapi 비공식 라이브러리)

Usage:
    python fetch_notes.py --list              # 메모 목록 조회
    python fetch_notes.py --fetch-all         # 모든 메모 가져오기
    python fetch_notes.py --search "검색어"   # 메모 검색

첫 실행 시 Google 계정 인증이 필요합니다.
- 2FA 사용 시: 앱 비밀번호 필요 (https://myaccount.google.com/apppasswords)
"""

import argparse
import json
import os
import sys
import getpass
from datetime import datetime
from pathlib import Path

import gkeepapi

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def load_env():
    """Load environment variables from .env file."""
    env_paths = [
        Path(__file__).parent.parent.parent.parent.parent / '.env',
        Path.home() / '.env',
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return True
    return False


def get_token_file() -> str:
    """Get the token file path."""
    return os.getenv(
        'GOOGLE_KEEP_TOKEN_FILE',
        '/Users/inkeun/projects/obsidian/.creds/keep_master_token.json'
    )


def get_credentials():
    """Get email and master token from saved file or prompt user."""
    token_file = get_token_file()

    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            data = json.load(f)
            return data.get('email'), data.get('master_token')

    return None, None


def save_credentials(email: str, master_token: str):
    """Save credentials to file."""
    token_file = get_token_file()
    os.makedirs(os.path.dirname(token_file), exist_ok=True)

    with open(token_file, 'w') as f:
        json.dump({
            'email': email,
            'master_token': master_token
        }, f)

    # Secure the file
    os.chmod(token_file, 0o600)
    print(f"✅ 토큰 저장됨: {token_file}")


def authenticate_keep(arg_email: str = None, arg_password: str = None) -> gkeepapi.Keep:
    """Authenticate and return Keep instance."""
    keep = gkeepapi.Keep()

    email, master_token = get_credentials()

    if master_token:
        print(f"🔄 저장된 토큰으로 로그인 중... ({email})")
        try:
            keep.resume(email, master_token)
            print("✅ 로그인 성공")
            return keep
        except Exception as e:
            print(f"⚠️ 토큰 만료됨, 재인증 필요: {e}")

    # Need fresh login
    print("\n📝 Google 계정 로그인")

    # Use argument or prompt
    if arg_email:
        email = arg_email
    elif not email:
        print("   2FA 사용 시 앱 비밀번호 필요: https://myaccount.google.com/apppasswords")
        email = input("이메일: ").strip()

    if arg_password:
        password = arg_password
    else:
        password = getpass.getpass("비밀번호 (또는 앱 비밀번호): ")

    print(f"🔄 로그인 중... ({email})")
    try:
        keep.login(email, password)
        master_token = keep.getMasterToken()
        save_credentials(email, master_token)
        print("✅ 로그인 성공")
        return keep
    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        print("\n💡 가능한 원인:")
        print("   1. 잘못된 이메일/비밀번호")
        print("   2. 2FA 사용 중인데 앱 비밀번호를 사용하지 않음")
        print("   3. Google 보안 설정에서 차단됨")
        sys.exit(1)


def format_note_for_display(note) -> str:
    """Format a note for console display."""
    title = note.title or '(제목 없음)'

    # Get text content
    if hasattr(note, 'text'):
        text = note.text[:100] if note.text else ''
    elif hasattr(note, 'items'):  # List note
        items = list(note.items)[:3]
        text = ', '.join([item.text for item in items if item.text])
    else:
        text = ''

    if len(text) > 100:
        text = text[:100] + '...'

    # Status icons
    status_icons = []
    if note.pinned:
        status_icons.append('📌')
    if note.trashed:
        status_icons.append('🗑️')
    if note.archived:
        status_icons.append('📦')
    if hasattr(note, 'color') and note.color.name != 'DEFAULT':
        status_icons.append(f'🎨{note.color.name}')

    status = ' '.join(status_icons) if status_icons else ''

    # Timestamps
    timestamps = note.timestamps
    created = timestamps.created.strftime('%Y-%m-%d %H:%M') if timestamps.created else ''
    updated = timestamps.updated.strftime('%Y-%m-%d %H:%M') if timestamps.updated else ''

    note_type = '📋' if hasattr(note, 'items') else '📝'

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{note_type} {title} {status}
   ID: {note.id}
   Created: {created}
   Updated: {updated}
   Preview: {text}
"""


def note_to_markdown(note, output_dir: Path) -> Path:
    """Convert a note to markdown and save to file."""
    title = note.title or '제목없음'

    # Sanitize filename
    safe_title = "".join(c for c in title if c.isalnum() or c in ' -_').strip()
    if not safe_title:
        safe_title = note.id[:8]

    if len(safe_title) > 50:
        safe_title = safe_title[:50]

    # Get body content
    content = ''
    if hasattr(note, 'text') and note.text:
        content = note.text
    elif hasattr(note, 'items'):  # List note
        for item in note.items:
            checked = item.checked
            text = item.text or ''
            checkbox = '[x]' if checked else '[ ]'
            content += f"- {checkbox} {text}\n"

    # Get timestamps
    timestamps = note.timestamps
    created = timestamps.created.strftime('%Y-%m-%d') if timestamps.created else ''
    updated = timestamps.updated.strftime('%Y-%m-%d') if timestamps.updated else ''

    date_str = updated or created or datetime.now().strftime('%Y-%m-%d')

    # Get labels
    labels = [label.name for label in note.labels.all()]
    tags_yaml = '\n'.join([f'  - {label}' for label in labels]) if labels else '  - 구글킵'
    if not labels:
        tags_yaml = '  - 구글킵\n  - 메모'

    # Color
    color = note.color.name if hasattr(note, 'color') else 'DEFAULT'

    # Format as YAML front matter + content
    md_content = f"""---
title: "{title}"
date: {date_str}
source: google-keep
keep_id: "{note.id}"
keep_color: "{color}"
pinned: {str(note.pinned).lower()}
archived: {str(note.archived).lower()}
tags:
{tags_yaml}
---

# {title}

{content}

---
*Google Keep에서 가져옴*
*Created: {created}*
*Updated: {updated}*
"""

    # Save to file
    filename = f"{date_str.replace('-', '')}_{safe_title}.md"
    output_path = output_dir / filename

    # Handle duplicate filenames
    counter = 1
    while output_path.exists():
        filename = f"{date_str.replace('-', '')}_{safe_title}_{counter}.md"
        output_path = output_dir / filename
        counter += 1

    output_path.write_text(md_content, encoding='utf-8')
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Google Keep 메모 가져오기 (gkeepapi)')
    parser.add_argument('--list', action='store_true', help='메모 목록 조회')
    parser.add_argument('--fetch-all', action='store_true', help='모든 메모 가져오기')
    parser.add_argument('--search', type=str, help='메모 검색')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/inkeun/projects/obsidian/00_Inbox',
                        help='출력 디렉토리')
    parser.add_argument('--include-archived', action='store_true', help='보관된 메모 포함')
    parser.add_argument('--include-trashed', action='store_true', help='휴지통 메모 포함')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    parser.add_argument('--sync', action='store_true', help='서버와 동기화')
    parser.add_argument('--email', type=str, help='Google 계정 이메일')
    parser.add_argument('--password', type=str, help='앱 비밀번호')

    args = parser.parse_args()

    load_env()

    print("=" * 60)
    print("Google Keep 메모 가져오기 (gkeepapi)")
    print("=" * 60)

    # Authenticate
    keep = authenticate_keep(args.email, args.password)

    # Sync with server
    if args.sync or not args.list:
        print("\n🔄 서버와 동기화 중...")
        keep.sync()
        print("✅ 동기화 완료")

    # Get notes
    all_notes = keep.all()

    # Filter notes
    notes = []
    for note in all_notes:
        if note.trashed and not args.include_trashed:
            continue
        if note.archived and not args.include_archived:
            continue
        notes.append(note)

    # Execute requested action
    try:
        if args.list:
            print(f"\n📋 메모 목록 ({len(notes)}개)")

            if args.json:
                notes_data = []
                for note in notes:
                    notes_data.append({
                        'id': note.id,
                        'title': note.title,
                        'text': note.text if hasattr(note, 'text') else None,
                        'pinned': note.pinned,
                        'archived': note.archived,
                        'trashed': note.trashed,
                    })
                print(json.dumps(notes_data, indent=2, ensure_ascii=False))
            else:
                for note in notes:
                    print(format_note_for_display(note))

        elif args.fetch_all:
            print(f"\n📥 모든 메모 가져오기 ({len(notes)}개)")

            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"📂 출력 디렉토리: {output_dir}")

            saved_count = 0
            for i, note in enumerate(notes, 1):
                try:
                    output_path = note_to_markdown(note, output_dir)
                    print(f"  [{i}/{len(notes)}] ✓ {output_path.name}")
                    saved_count += 1
                except Exception as e:
                    print(f"  [{i}/{len(notes)}] ✗ 변환 실패: {e}")

            print(f"\n✅ 완료: {saved_count}개 메모를 {output_dir}에 저장")

        elif args.search:
            print(f"\n🔍 '{args.search}' 검색 중...")

            matching = []
            search_lower = args.search.lower()
            for note in notes:
                title = (note.title or '').lower()
                text = ''
                if hasattr(note, 'text'):
                    text = (note.text or '').lower()
                elif hasattr(note, 'items'):
                    text = ' '.join([item.text or '' for item in note.items]).lower()

                if search_lower in title or search_lower in text:
                    matching.append(note)

            print(f"✅ {len(matching)}개 발견")

            for note in matching:
                print(format_note_for_display(note))

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
