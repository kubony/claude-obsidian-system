#!/usr/bin/env python3
"""
Google Calendar Event Updater

Update or delete existing calendar events.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SKILL_DIR))

from dotenv import load_dotenv
import pytz

from google_api.calendar import GoogleCalendarAPIManager

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


def parse_time_range(time_str: str) -> tuple:
    """Parse time range string to (start_hour, start_min, end_hour, end_min)."""
    import re
    time_str = time_str.replace('~', '-').replace(' ', '')

    for pattern in [r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', r'(\d{2})(\d{2})-(\d{2})(\d{2})']:
        match = re.match(pattern, time_str)
        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4))
            )

    raise ValueError(f"Invalid time format: {time_str}. Use HH:MM-HH:MM")


def format_event_summary(event: dict) -> str:
    """Format event for display."""
    formatted = GoogleCalendarAPIManager.format_event(event)
    start = formatted['start']
    if 'T' in start:
        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        time_str = dt.strftime("%Y-%m-%d %H:%M")
    else:
        time_str = start

    return f"{time_str} | {formatted['summary']}"


def main():
    parser = argparse.ArgumentParser(
        description="Update or delete Google Calendar events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update by event ID
  update_event.py --event-id abc123 --title "새 제목"
  update_event.py --event-id abc123 --time 15:00-16:00
  update_event.py --event-id abc123 --location "판교 카페"

  # Search and update
  update_event.py --search "조쉬 커피챗" --time 15:00-16:00

  # Delete event
  update_event.py --event-id abc123 --delete

  # Dry-run
  update_event.py --event-id abc123 --title "새 제목" --dry-run
        """
    )

    # Event selection (mutually exclusive)
    select_group = parser.add_mutually_exclusive_group(required=True)
    select_group.add_argument("--event-id", type=str, help="Event ID to update")
    select_group.add_argument("--search", type=str, help="Search query to find event")

    # Update fields
    parser.add_argument("--title", type=str, help="New event title")
    parser.add_argument("--date", type=str, help="New date (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, help="New time range (HH:MM-HH:MM)")
    parser.add_argument("--location", type=str, help="New location")
    parser.add_argument("--description", type=str, help="New description")

    # Actions
    parser.add_argument("--delete", action="store_true", help="Delete the event")
    parser.add_argument("--no-notify", action="store_true", help="Don't send notifications")

    # Control
    parser.add_argument("--dry-run", action="store_true", help="Preview without updating")

    args = parser.parse_args()

    # Validate credentials
    if not CREDENTIALS_PATH:
        print("❌ GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        manager = GoogleCalendarAPIManager(CREDENTIALS_PATH, CALENDAR_ID)

        # Find event
        event_id = args.event_id
        if args.search:
            events = manager.search_events(args.search, max_results=10)
            if not events:
                print(f"❌ '{args.search}'와 일치하는 이벤트를 찾을 수 없습니다.")
                sys.exit(1)

            if len(events) == 1:
                event_id = events[0]['id']
                print(f"✅ 이벤트 찾음: {format_event_summary(events[0])}")
            else:
                print(f"⚠️ {len(events)}개의 이벤트가 검색되었습니다. 하나를 선택하세요:\n")
                for i, event in enumerate(events, 1):
                    print(f"  {i}. {format_event_summary(event)}")
                    print(f"     ID: {event['id']}")
                print("\n--event-id 옵션으로 특정 이벤트를 지정하세요.")
                sys.exit(1)

        # Get current event
        event = manager.get_event(event_id)
        formatted = GoogleCalendarAPIManager.format_event(event)

        print("\n" + "=" * 50)
        print("📅 현재 이벤트")
        print("=" * 50)
        print(f"제목: {formatted['summary']}")
        print(f"일시: {formatted['start']} - {formatted['end']}")
        if formatted['location']:
            print(f"장소: {formatted['location']}")
        print(f"ID: {formatted['id']}")
        print("=" * 50)

        # Handle delete
        if args.delete:
            if args.dry_run:
                print("\n🔍 Dry-run 모드: 이벤트가 삭제되지 않았습니다.")
                return

            confirm = input("\n⚠️ 이 이벤트를 삭제하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                print("취소됨")
                return

            manager.delete_event(event_id, send_updates=not args.no_notify)
            print("\n✅ 이벤트가 삭제되었습니다.")
            return

        # Check if any update field is provided
        if not any([args.title, args.date, args.time, args.location, args.description]):
            print("\n❌ 수정할 필드를 지정하세요 (--title, --date, --time, --location, --description)")
            sys.exit(1)

        # Prepare updates
        tz = pytz.timezone(TIMEZONE)
        start_dt = None
        end_dt = None

        if args.date or args.time:
            # Parse current event datetime
            current_start = formatted['start']
            if 'T' in current_start:
                current_dt = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
            else:
                current_dt = datetime.strptime(current_start, "%Y-%m-%d")
                current_dt = tz.localize(current_dt)

            # Default values from current event
            date_val = args.date if args.date else current_dt.strftime("%Y-%m-%d")
            base_date = parse_date(date_val)

            if args.time:
                start_h, start_m, end_h, end_m = parse_time_range(args.time)
                start_dt = base_date.replace(hour=start_h, minute=start_m)
                end_dt = base_date.replace(hour=end_h, minute=end_m)
            else:
                start_dt = base_date.replace(hour=current_dt.hour, minute=current_dt.minute)
                # Assume 1 hour duration if only date changed
                end_dt = start_dt + (datetime.fromisoformat(formatted['end'].replace('Z', '+00:00')) -
                                      datetime.fromisoformat(formatted['start'].replace('Z', '+00:00')))

        # Print preview
        print("\n📝 수정 내용:")
        if args.title:
            print(f"  제목: {formatted['summary']} → {args.title}")
        if start_dt:
            print(f"  시작: {formatted['start']} → {start_dt.isoformat()}")
        if end_dt:
            print(f"  종료: {formatted['end']} → {end_dt.isoformat()}")
        if args.location:
            print(f"  장소: {formatted['location'] or '(없음)'} → {args.location}")
        if args.description:
            print(f"  설명: 업데이트됨")

        if args.dry_run:
            print("\n🔍 Dry-run 모드: 이벤트가 수정되지 않았습니다.")
            return

        # Update event
        updated = manager.update_event(
            event_id=event_id,
            summary=args.title,
            start=start_dt,
            end=end_dt,
            location=args.location,
            description=args.description,
            send_updates=not args.no_notify
        )

        print("\n✅ 이벤트가 수정되었습니다!")
        print(f"🔗 {updated.get('htmlLink', '')}")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
