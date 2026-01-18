#!/usr/bin/env python3
"""
Google Calendar Event Creator

Create calendar events with optional person lookup and Google Meet integration.
"""

import argparse
import os
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
from person_lookup import get_person_email, get_person_info

# Load environment variables
VAULT_PATH = Path("/path/to/vault")
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
    """
    Parse time range string to (start_hour, start_min, end_hour, end_min).

    Formats:
    - "14:00-15:00"
    - "14:00~15:00"
    - "1400-1500"
    """
    # Normalize separators
    time_str = time_str.replace('~', '-').replace(' ', '')

    # Try HH:MM-HH:MM format
    match = None
    for pattern in [r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', r'(\d{2})(\d{2})-(\d{2})(\d{2})']:
        import re
        match = re.match(pattern, time_str)
        if match:
            break

    if match:
        return (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4))
        )

    raise ValueError(f"Invalid time format: {time_str}. Use HH:MM-HH:MM")


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[dt.weekday()]
    return f"{dt.strftime('%Y-%m-%d')} ({weekday}) {dt.strftime('%H:%M')}"


def main():
    parser = argparse.ArgumentParser(
        description="Create Google Calendar events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic event
  create_event.py --title "미팅" --date 2025-01-15 --time 14:00-15:00

  # With person (auto-lookup email from person directory)
  create_event.py --person "조쉬" --title "커피챗" --date 2025-01-15 --time 14:00-15:00

  # With Google Meet
  create_event.py --person "조쉬" --title "온라인 미팅" --date 2025-01-15 --time 10:00-11:00 --meet

  # With location
  create_event.py --title "미팅" --date 2025-01-15 --time 14:00-15:00 --location "강남역 스타벅스"

  # Dry-run (preview without creating)
  create_event.py --person "조쉬" --title "테스트" --date 2025-01-20 --time 15:00-16:00 --dry-run
        """
    )

    # Required
    parser.add_argument("--title", type=str, required=True, help="Event title")
    parser.add_argument("--date", type=str, required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, required=True, help="Time range (HH:MM-HH:MM)")

    # Optional
    parser.add_argument("--person", type=str, help="Person name (lookup email from person directory)")
    parser.add_argument("--email", type=str, help="Attendee email (direct)")
    parser.add_argument("--location", type=str, help="Event location")
    parser.add_argument("--description", type=str, help="Event description")
    parser.add_argument("--meet", action="store_true", help="Create Google Meet link")
    parser.add_argument("--no-notify", action="store_true", help="Don't send email notifications")

    # Control
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    args = parser.parse_args()

    # Validate credentials
    if not CREDENTIALS_PATH:
        print("❌ GOOGLE_CREDENTIALS_PATH 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    if not Path(CREDENTIALS_PATH).exists():
        print(f"❌ 서비스 계정 키 파일을 찾을 수 없습니다: {CREDENTIALS_PATH}")
        sys.exit(1)

    try:
        # Parse date and time
        event_date = parse_date(args.date)
        start_h, start_m, end_h, end_m = parse_time_range(args.time)

        start_dt = event_date.replace(hour=start_h, minute=start_m)
        end_dt = event_date.replace(hour=end_h, minute=end_m)

        # Validate time range
        if end_dt <= start_dt:
            print("❌ 종료 시간이 시작 시간보다 이후여야 합니다.")
            sys.exit(1)

        # Resolve attendees
        attendees = []
        person_info = None

        if args.person:
            person_info = get_person_info(args.person)
            if person_info:
                print(f"✅ 인물사전에서 '{person_info['name']}' 찾음")
                if person_info.get('email'):
                    attendees.append(person_info['email'])
                    print(f"   이메일: {person_info['email']}")
                else:
                    print(f"   ⚠️ 이메일 정보 없음 - 참석자 없이 생성됩니다")
            else:
                print(f"⚠️ 인물사전에서 '{args.person}'을 찾을 수 없습니다.")

        if args.email:
            if args.email not in attendees:
                attendees.append(args.email)

        # Build event summary
        summary = args.title
        if person_info and person_info.get('name') and args.person not in args.title:
            # Add person name to title if not already included
            pass  # Keep original title

        # Print preview
        print("\n" + "=" * 50)
        print("📅 이벤트 미리보기")
        print("=" * 50)
        print(f"제목: {summary}")
        print(f"일시: {format_datetime(start_dt)} - {end_dt.strftime('%H:%M')}")
        if args.location:
            print(f"장소: {args.location}")
        if args.meet:
            print("화상회의: Google Meet (자동 생성)")
        if attendees:
            print(f"참석자: {', '.join(attendees)}")
        if args.description:
            print(f"설명: {args.description}")
        print("=" * 50)

        if args.dry_run:
            print("\n🔍 Dry-run 모드: 실제 이벤트가 생성되지 않았습니다.")
            return

        # Create event
        manager = GoogleCalendarAPIManager(CREDENTIALS_PATH, CALENDAR_ID)

        event = manager.create_event(
            summary=summary,
            start=start_dt,
            end=end_dt,
            location=args.location,
            description=args.description,
            attendees=attendees if attendees else None,
            create_meet=args.meet,
            send_updates=not args.no_notify
        )

        # Print result
        formatted = GoogleCalendarAPIManager.format_event(event)

        print("\n✅ 이벤트 생성 완료!")
        print(f"\n🔗 캘린더 링크: {formatted['html_link']}")
        if formatted['hangout_link']:
            print(f"🎥 Google Meet: {formatted['hangout_link']}")
        print(f"📝 이벤트 ID: {formatted['id']}")

    except ValueError as e:
        print(f"❌ 입력 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        if "403" in str(e):
            print("\n💡 캘린더 쓰기 권한이 없습니다.")
            print("   Google Calendar 설정에서 서비스 계정에 '변경 및 공유 관리' 권한을 부여하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
