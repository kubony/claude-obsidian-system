#!/usr/bin/env python3
"""
Calendar to Person Directory Sync

Sync calendar events to person directory files in Obsidian vault.
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
import pytz

from google_api.calendar import GoogleCalendarAPIManager
from person_matcher import PersonMatcher

# Load environment variables
VAULT_PATH = Path("/Users/inkeun/projects/obsidian")
load_dotenv(VAULT_PATH / ".env")

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
TIMEZONE = 'Asia/Seoul'


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    tz = pytz.timezone(TIMEZONE)
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return tz.localize(dt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def format_event_datetime(iso_string: str) -> tuple:
    """
    Format ISO datetime string to (date_str, time_str).

    Returns:
        (date: "YYYY.MM.DD", time: "HH:MM-HH:MM" or "종일")
    """
    if not iso_string:
        return ("", "")

    try:
        if 'T' in iso_string:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return (dt.strftime("%Y.%m.%d"), dt.strftime("%H:%M"))
        else:
            dt = datetime.strptime(iso_string, "%Y-%m-%d")
            return (dt.strftime("%Y.%m.%d"), "종일")
    except Exception:
        return (iso_string, "")


def is_event_synced(content: str, event_id: str) -> bool:
    """Check if an event is already synced to the file."""
    pattern = rf'calendar_event_id:\s*{re.escape(event_id)}'
    return bool(re.search(pattern, content))


def build_meeting_entry(event: Dict, attendees_str: str = "") -> str:
    """
    Build a meeting entry markdown block.

    Args:
        event: Formatted event dictionary.
        attendees_str: Comma-separated attendee names.

    Returns:
        Markdown string for the meeting entry.
    """
    formatted = GoogleCalendarAPIManager.format_event(event)

    start_date, start_time = format_event_datetime(formatted['start'])
    _, end_time = format_event_datetime(formatted['end'])

    time_str = f"{start_time}-{end_time}" if start_time != "종일" else "종일"

    lines = [
        f"### {start_date} 캘린더 일정",
        f"- **시간**: {time_str}",
    ]

    # Location or Meet link
    location = formatted['location']
    if formatted['hangout_link']:
        lines.append(f"- **장소**: [Google Meet]({formatted['hangout_link']})")
    elif location:
        lines.append(f"- **장소**: {location}")

    # Attendees
    if attendees_str:
        lines.append(f"- **참석자**: {attendees_str}")

    # Event link
    if formatted['html_link']:
        lines.append(f"- **원본**: [캘린더 링크]({formatted['html_link']})")

    # Event ID for duplicate prevention
    lines.append(f"<!-- calendar_event_id: {formatted['id']} -->")

    return "\n".join(lines)


def find_meeting_section(content: str) -> int:
    """
    Find the position to insert a new meeting entry.

    Looks for "## 미팅/대화 기록" section.

    Returns:
        Position (character index) to insert the new entry, or -1 if not found.
    """
    # Look for the meeting section header
    patterns = [
        r'\n## 미팅/대화 기록\s*\n',
        r'\n## 미팅 기록\s*\n',
        r'\n## 대화 기록\s*\n',
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            # Return position right after the header
            return match.end()

    return -1


def insert_meeting_entry(content: str, entry: str) -> str:
    """
    Insert a meeting entry into the file content.

    Args:
        content: Original file content.
        entry: Meeting entry to insert.

    Returns:
        Updated file content.
    """
    section_pos = find_meeting_section(content)

    if section_pos > 0:
        # Insert after the section header
        return content[:section_pos] + "\n" + entry + "\n" + content[section_pos:]
    else:
        # Append a new section at the end
        return content.rstrip() + "\n\n## 미팅/대화 기록\n\n" + entry + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Sync calendar events to person directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync today's events
  sync_to_person.py --today

  # Sync this week's events
  sync_to_person.py --week

  # Sync specific date range
  sync_to_person.py --start 2025-01-01 --end 2025-01-08

  # Dry-run (preview without syncing)
  sync_to_person.py --today --dry-run

  # Filter by person
  sync_to_person.py --today --person "조쉬"
        """
    )

    # Time range options
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument("--today", action="store_true", help="Sync today's events")
    time_group.add_argument("--week", action="store_true", help="Sync this week's events")

    # Date range
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    # Filters
    parser.add_argument("--person", type=str, help="Filter by person name")

    # Control
    parser.add_argument("--dry-run", action="store_true", help="Preview without syncing")

    args = parser.parse_args()

    # Validate credentials
    if not CREDENTIALS_PATH:
        print("❌ GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    if not Path(CREDENTIALS_PATH).exists():
        print(f"❌ 서비스 계정 키 파일을 찾을 수 없습니다: {CREDENTIALS_PATH}")
        sys.exit(1)

    try:
        # Initialize managers
        calendar_mgr = GoogleCalendarAPIManager(CREDENTIALS_PATH, CALENDAR_ID)
        person_matcher = PersonMatcher()

        # Determine time range
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)

        if args.today:
            time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
            time_max = time_min + timedelta(days=1)
            title = "오늘"
        elif args.week:
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = today - timedelta(days=today.weekday())
            time_max = time_min + timedelta(days=7)
            title = "이번 주"
        elif args.start and args.end:
            time_min = parse_date(args.start)
            time_max = parse_date(args.end) + timedelta(days=1)
            title = f"{args.start} ~ {args.end}"
        else:
            # Default to today
            time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
            time_max = time_min + timedelta(days=1)
            title = "오늘"

        # Fetch events
        events = calendar_mgr.list_events(time_min, time_max)

        print(f"\n📋 캘린더 → 인물사전 동기화 ({title})")
        print("━" * 50)

        if not events:
            print("일정이 없습니다.")
            return

        # Process events
        sync_results = []
        skipped_no_match = []
        skipped_already_synced = []

        for event in events:
            formatted = GoogleCalendarAPIManager.format_event(event)

            # Filter by person if specified
            if args.person:
                if args.person not in formatted['summary']:
                    continue

            # Find matching persons
            matches = person_matcher.match_event(event)

            if not matches:
                skipped_no_match.append(formatted)
                continue

            # Process each match
            for match in matches:
                file_path = match['file_path']

                # Check if already synced
                content = file_path.read_text(encoding='utf-8')
                if is_event_synced(content, formatted['id']):
                    skipped_already_synced.append({
                        'event': formatted,
                        'file': file_path.name
                    })
                    continue

                # Get person info for attendees string
                person_info = person_matcher.get_person_info(file_path)

                # Build attendees list from event
                attendee_names = []
                for attendee in event.get('attendees', []):
                    email = attendee.get('email', '')
                    if email and not email.endswith('calendar.google.com'):
                        # Try to find name from person directory
                        att_match = person_matcher.find_by_email(email)
                        if att_match:
                            att_info = person_matcher.get_person_info(att_match)
                            attendee_names.append(att_info.get('name', email))
                        else:
                            attendee_names.append(email.split('@')[0])

                attendees_str = ", ".join(attendee_names) if attendee_names else ""

                # Build meeting entry
                entry = build_meeting_entry(event, attendees_str)

                sync_results.append({
                    'event': formatted,
                    'file': file_path,
                    'match_type': match['match_type'],
                    'match_value': match['match_value'],
                    'entry': entry,
                })

        # Print results
        if args.dry_run:
            print("\n🔍 Dry-run 모드: 실제 변경 없음\n")

        # Sync results
        for result in sync_results:
            event = result['event']
            start_date, start_time = format_event_datetime(event['start'])

            status = "📅" if not args.dry_run else "🔍"
            print(f"{status} {start_date} {start_time} {event['summary']}")
            print(f"   → {result['file'].name} ({result['match_type']}: {result['match_value']})")

            if not args.dry_run:
                # Actually sync
                content = result['file'].read_text(encoding='utf-8')
                new_content = insert_meeting_entry(content, result['entry'])
                result['file'].write_text(new_content, encoding='utf-8')
                print("   ✅ 동기화 완료")
            print()

        # Skipped (no match)
        if skipped_no_match:
            print(f"\n⏭️ 매칭 없음 ({len(skipped_no_match)}개):")
            for event in skipped_no_match:
                start_date, start_time = format_event_datetime(event['start'])
                print(f"   - {start_date} {start_time} {event['summary']}")

        # Skipped (already synced)
        if skipped_already_synced:
            print(f"\n⏭️ 이미 동기화됨 ({len(skipped_already_synced)}개):")
            for item in skipped_already_synced:
                event = item['event']
                start_date, _ = format_event_datetime(event['start'])
                print(f"   - {event['summary']} → {item['file']}")

        # Summary
        print("\n" + "━" * 50)
        print(f"완료: {len(sync_results)}개 동기화")
        if skipped_no_match:
            print(f"      {len(skipped_no_match)}개 매칭 없음")
        if skipped_already_synced:
            print(f"      {len(skipped_already_synced)}개 이미 동기화됨")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        if "403" in str(e):
            print("\n💡 캘린더 접근 권한이 없습니다.")
            print("   Google Calendar 설정에서 서비스 계정에 캘린더를 공유하세요.")
        sys.exit(1)


# Type hint for event dict
from typing import Dict

if __name__ == "__main__":
    main()
