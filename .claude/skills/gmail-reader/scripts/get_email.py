#!/usr/bin/env python3
"""
Gmail 개별 이메일 조회 스크립트
- 이메일 ID로 상세 내용 조회
- 스레드 전체 조회
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gmail_client import get_gmail_service
from search_emails import parse_email, extract_body


def get_email_by_id(email_id: str, include_body: bool = True) -> dict:
    """
    이메일 ID로 상세 정보 조회

    Args:
        email_id: Gmail 메시지 ID
        include_body: 본문 포함 여부

    Returns:
        이메일 상세 정보
    """
    service = get_gmail_service()

    msg_detail = service.users().messages().get(
        userId='me',
        id=email_id,
        format='full'
    ).execute()

    return parse_email(msg_detail, include_body)


def get_thread(thread_id: str) -> list:
    """
    스레드 전체 이메일 조회

    Args:
        thread_id: Gmail 스레드 ID

    Returns:
        스레드 내 모든 이메일 목록
    """
    service = get_gmail_service()

    thread = service.users().threads().get(
        userId='me',
        id=thread_id,
        format='full'
    ).execute()

    emails = []
    for msg in thread.get('messages', []):
        email_data = parse_email(msg, include_body=True)
        emails.append(email_data)

    return emails


def get_unread_emails(max_results: int = 20) -> list:
    """
    읽지 않은 이메일 조회

    Args:
        max_results: 최대 결과 수

    Returns:
        읽지 않은 이메일 목록
    """
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return []

    emails = []
    for msg in messages:
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()

        email_data = parse_email(msg_detail, include_body=False)
        emails.append(email_data)

    return emails


def get_recent_emails(max_results: int = 10) -> list:
    """
    최근 이메일 조회 (받은편지함)

    Args:
        max_results: 최대 결과 수

    Returns:
        최근 이메일 목록
    """
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return []

    emails = []
    for msg in messages:
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()

        email_data = parse_email(msg_detail, include_body=False)
        emails.append(email_data)

    return emails


def main():
    parser = argparse.ArgumentParser(description='Gmail 이메일 상세 조회')
    parser.add_argument('--id', '-i', type=str, help='이메일 ID로 조회')
    parser.add_argument('--thread', '-t', type=str, help='스레드 ID로 전체 대화 조회')
    parser.add_argument('--unread', '-u', action='store_true', help='읽지 않은 메일 조회')
    parser.add_argument('--recent', '-r', action='store_true', help='최근 메일 조회')
    parser.add_argument('--max', '-n', type=int, default=10, help='최대 결과 수 (기본: 10)')
    parser.add_argument('--json', '-j', action='store_true', help='JSON 형식 출력')

    args = parser.parse_args()

    try:
        result = None

        if args.id:
            result = get_email_by_id(args.id)
        elif args.thread:
            result = get_thread(args.thread)
        elif args.unread:
            result = get_unread_emails(args.max)
        elif args.recent:
            result = get_recent_emails(args.max)
        else:
            result = get_recent_emails(args.max)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if isinstance(result, list):
                print(f"\n총 {len(result)}개의 이메일\n")
                print("-" * 80)
                for i, email in enumerate(result, 1):
                    print(f"\n[{i}] {email['subject']}")
                    print(f"    From: {email['from']}")
                    print(f"    Date: {email['date_iso'][:10] if email['date_iso'] else email['date']}")
                    print(f"    ID: {email['id']}")
                    if email.get('body'):
                        print(f"\n    --- 본문 ---")
                        print(f"    {email['body'][:1000]}...")
            else:
                # 단일 이메일
                print(f"\n제목: {result['subject']}")
                print(f"From: {result['from']}")
                print(f"To: {result['to']}")
                print(f"Date: {result['date']}")
                print(f"ID: {result['id']}")
                print(f"Thread ID: {result['thread_id']}")
                print(f"\n--- 본문 ---\n")
                print(result.get('body', result['snippet']))

            print("\n" + "-" * 80)

    except FileNotFoundError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"조회 실패: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
