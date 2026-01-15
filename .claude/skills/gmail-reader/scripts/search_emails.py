#!/usr/bin/env python3
"""
Gmail 이메일 검색 스크립트
- 키워드, 발신자, 날짜 범위 등으로 검색
- 미팅/일정 관련 메일 필터링
- 특정 인물과의 이메일 히스토리 조회
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 같은 디렉토리의 gmail_client 임포트
sys.path.insert(0, str(Path(__file__).parent))
from gmail_client import get_gmail_service


def search_emails(query: str, max_results: int = 20, include_body: bool = False):
    """
    Gmail 검색 쿼리로 이메일 검색

    Args:
        query: Gmail 검색 쿼리 (예: "from:someone@example.com", "subject:미팅")
        max_results: 최대 결과 수
        include_body: 본문 포함 여부

    Returns:
        검색된 이메일 목록
    """
    service = get_gmail_service()

    # 메시지 목록 검색
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return []

    emails = []
    for msg in messages:
        # 메시지 상세 정보 가져오기
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full' if include_body else 'metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()

        email_data = parse_email(msg_detail, include_body)
        emails.append(email_data)

    return emails


def parse_email(msg_detail: dict, include_body: bool = False) -> dict:
    """메시지 상세 정보를 파싱하여 딕셔너리로 반환"""
    headers = msg_detail.get('payload', {}).get('headers', [])

    def get_header(name):
        for h in headers:
            if h['name'].lower() == name.lower():
                return h['value']
        return ''

    email_data = {
        'id': msg_detail['id'],
        'thread_id': msg_detail['threadId'],
        'date': get_header('Date'),
        'from': get_header('From'),
        'to': get_header('To'),
        'subject': get_header('Subject'),
        'snippet': msg_detail.get('snippet', ''),
        'labels': msg_detail.get('labelIds', []),
    }

    # 날짜 파싱 (ISO 형식으로 변환)
    try:
        internal_date = int(msg_detail.get('internalDate', 0)) / 1000
        email_data['date_iso'] = datetime.fromtimestamp(internal_date).isoformat()
    except:
        email_data['date_iso'] = ''

    # 본문 포함
    if include_body:
        email_data['body'] = extract_body(msg_detail.get('payload', {}))

    return email_data


def extract_body(payload: dict) -> str:
    """이메일 본문 추출 (text/plain 우선)"""
    import base64

    body = ''

    if 'body' in payload and payload['body'].get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    elif 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                break
            elif 'parts' in part:
                # 재귀적으로 파트 탐색
                body = extract_body(part)
                if body:
                    break

    return body[:5000] if body else ''  # 본문 길이 제한


def search_meeting_emails(days: int = 7, max_results: int = 20):
    """
    미팅/일정 관련 이메일 검색

    Args:
        days: 최근 N일 이내
        max_results: 최대 결과 수
    """
    # 날짜 계산
    after_date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')

    # 미팅 관련 키워드 검색
    meeting_keywords = [
        'subject:(미팅 OR 회의 OR meeting OR 일정 OR 커피챗 OR "coffee chat")',
        'subject:(초대 OR invite OR calendar)',
        'from:calendar-notification@google.com',  # Google Calendar 알림
    ]

    query = f"({' OR '.join(meeting_keywords)}) after:{after_date}"
    return search_emails(query, max_results, include_body=True)


def search_from_person(email_or_name: str, max_results: int = 20):
    """
    특정 인물로부터 받은 이메일 검색

    Args:
        email_or_name: 이메일 주소 또는 이름
        max_results: 최대 결과 수
    """
    query = f"from:{email_or_name}"
    return search_emails(query, max_results, include_body=False)


def search_with_person(email_or_name: str, max_results: int = 30):
    """
    특정 인물과의 전체 이메일 히스토리 (주고받은 메일 모두)

    Args:
        email_or_name: 이메일 주소 또는 이름
        max_results: 최대 결과 수
    """
    # from: 또는 to:에 해당하는 메일 검색
    query = f"from:{email_or_name} OR to:{email_or_name}"
    return search_emails(query, max_results, include_body=False)


def main():
    parser = argparse.ArgumentParser(description='Gmail 이메일 검색')
    parser.add_argument('--query', '-q', type=str, help='Gmail 검색 쿼리')
    parser.add_argument('--meetings', '-m', action='store_true', help='미팅/일정 관련 메일 검색')
    parser.add_argument('--from-person', '-f', type=str, help='특정 인물로부터 받은 메일')
    parser.add_argument('--with-person', '-w', type=str, help='특정 인물과의 메일 히스토리')
    parser.add_argument('--days', '-d', type=int, default=7, help='최근 N일 이내 (기본: 7)')
    parser.add_argument('--max', '-n', type=int, default=20, help='최대 결과 수 (기본: 20)')
    parser.add_argument('--body', '-b', action='store_true', help='본문 포함')
    parser.add_argument('--json', '-j', action='store_true', help='JSON 형식 출력')

    args = parser.parse_args()

    try:
        emails = []

        if args.meetings:
            emails = search_meeting_emails(args.days, args.max)
        elif args.from_person:
            emails = search_from_person(args.from_person, args.max)
        elif args.with_person:
            emails = search_with_person(args.with_person, args.max)
        elif args.query:
            emails = search_emails(args.query, args.max, args.body)
        else:
            # 기본: 최근 메일 조회
            after_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y/%m/%d')
            emails = search_emails(f"after:{after_date}", args.max, args.body)

        if args.json:
            print(json.dumps(emails, ensure_ascii=False, indent=2))
        else:
            print(f"\n총 {len(emails)}개의 이메일을 찾았습니다.\n")
            print("-" * 80)
            for i, email in enumerate(emails, 1):
                print(f"\n[{i}] {email['subject']}")
                print(f"    From: {email['from']}")
                print(f"    Date: {email['date_iso'][:10] if email['date_iso'] else email['date']}")
                print(f"    Preview: {email['snippet'][:100]}...")
                if args.body and email.get('body'):
                    print(f"\n    --- 본문 ---")
                    print(f"    {email['body'][:500]}...")
            print("\n" + "-" * 80)

    except FileNotFoundError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"검색 실패: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
