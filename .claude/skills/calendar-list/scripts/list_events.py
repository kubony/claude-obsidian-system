#!/usr/bin/env python3
"""
Google Calendar Event Lister

List calendar events with various filters: today, week, date range, or person.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for google_api import
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


def format_time(iso_string: str) -> str:
    """Format ISO datetime string to HH:MM."""
    if not iso_string:
        return ""
    try:
        # Handle both datetime and date-only formats
        if 'T' in iso_string:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        else:
            return "종일"
    except Exception:
        return iso_string


def format_date(iso_string: str) -> str:
    """Format ISO datetime string to YYYY-MM-DD (요일)."""
    if not iso_string:
        return ""
    try:
        if 'T' in iso_string:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(iso_string, "%Y-%m-%d")

        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        weekday = weekdays[dt.weekday()]
        return f"{dt.strftime('%Y-%m-%d')} ({weekday})"
    except Exception:
        return iso_string


def print_events(events: list, title: str, json_output: bool = False):
    """Print events in formatted or JSON output."""
    if json_output:
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return

    print(f"\n📅 {title}")
    print("━" * 50)

    if not events:
        print("일정이 없습니다.")
        print("━" * 50)
        return

    current_date = None
    for event in events:
        formatted = GoogleCalendarAPIManager.format_event(event)

        # Group by date
        event_date = format_date(formatted['start'])
        if event_date != current_date:
            if current_date is not None:
                print()
            print(f"\n📆 {event_date}")
            current_date = event_date

        # Time range
        start_time = format_time(formatted['start'])
        end_time = format_time(formatted['end'])
        time_str = f"{start_time}-{end_time}" if start_time != "종일" else "종일"

        # Location
        location = formatted['location']
        if formatted['hangout_link']:
            location = "Google Meet"
        location_str = f" | {location}" if location else ""

        # Attendees
        attendees = formatted['attendees']
        attendee_str = f" | 👥 {len(attendees)}명" if attendees else ""

        print(f"  {time_str:13} | {formatted['summary']}{location_str}{attendee_str}")

    print("\n" + "━" * 50)
    print(f"총 {len(events)}개 일정")


def search_by_person(events: list, person_name: str) -> list:
    """Filter events by person name in summary or attendees."""
    results = []
    for event in events:
        formatted = GoogleCalendarAPIManager.format_event(event)

        # Check summary
        if person_name.lower() in formatted['summary'].lower():
            results.append(event)
            continue

        # Check attendees
        for attendee in formatted['attendees']:
            if person_name.lower() in attendee.lower():
                results.append(event)
                break

    return results


def main():
    parser = argparse.ArgumentParser(
        description="List Google Calendar events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  list_events.py --today           # Today's events
  list_events.py --week            # This week's events
  list_events.py --start 2025-01-01 --end 2025-01-31  # Date range
  list_events.py --person "조쉬"    # Events with specific person
  list_events.py --today --json    # JSON output
        """
    )

    # Time range options (mutually exclusive)
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument("--today", action="store_true", help="Show today's events")
    time_group.add_argument("--week", action="store_true", help="Show this week's events")
    time_group.add_argument("--month", action="store_true", help="Show this month's events")

    # Date range
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    # Filters
    parser.add_argument("--person", type=str, help="Filter by person name")
    parser.add_argument("--query", type=str, help="Search query")

    # Output options
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--max", type=int, default=100, help="Maximum events to return")

    args = parser.parse_args()

    # Validate credentials
    if not CREDENTIALS_PATH:
        print("❌ GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_CREDENTIALS_PATH를 설정하세요.")
        sys.exit(1)

    if not Path(CREDENTIALS_PATH).exists():
        print(f"❌ 서비스 계정 키 파일을 찾을 수 없습니다: {CREDENTIALS_PATH}")
        sys.exit(1)

    try:
        # Initialize API manager
        manager = GoogleCalendarAPIManager(CREDENTIALS_PATH, CALENDAR_ID)

        # Determine time range
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)

        if args.today:
            events = manager.get_today_events()
            title = f"{now.strftime('%Y-%m-%d')} 오늘의 일정"
        elif args.week:
            events = manager.get_week_events()
            title = "이번 주 일정"
        elif args.month:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                month_end = month_start.replace(year=now.year + 1, month=1)
            else:
                month_end = month_start.replace(month=now.month + 1)
            events = manager.list_events(month_start, month_end, args.max)
            title = f"{now.strftime('%Y년 %m월')} 일정"
        elif args.start and args.end:
            start_date = parse_date(args.start)
            end_date = parse_date(args.end) + timedelta(days=1)  # Include end date
            events = manager.list_events(start_date, end_date, args.max)
            title = f"{args.start} ~ {args.end} 일정"
        elif args.query:
            events = manager.search_events(args.query, max_results=args.max)
            title = f'"{args.query}" 검색 결과'
        else:
            # Default to today
            events = manager.get_today_events()
            title = f"{now.strftime('%Y-%m-%d')} 오늘의 일정"

        # Filter by person if specified
        if args.person:
            events = search_by_person(events, args.person)
            title = f"{args.person}님 관련 일정"

        # Output
        print_events(events, title, args.json)

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        if "403" in str(e):
            print("\n💡 캘린더 접근 권한이 없습니다.")
            print("   Google Calendar 설정에서 서비스 계정에 캘린더를 공유하세요:")
            print(f"   이메일: hrm123@crawler-457104.iam.gserviceaccount.com")
        sys.exit(1)


if __name__ == "__main__":
    main()
