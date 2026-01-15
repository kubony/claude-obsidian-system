#!/usr/bin/env python3
"""
Gmail 이메일 발송 스크립트
"""

import argparse
import base64
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from gmail_client import get_gmail_service, get_user_email


def create_message(to: str, subject: str, body: str, sender: str = None) -> dict:
    """이메일 메시지 생성"""
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    if sender:
        message['from'] = sender

    # 본문 추가 (UTF-8)
    msg_body = MIMEText(body, 'plain', 'utf-8')
    message.attach(msg_body)

    # base64 인코딩
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw}


def send_email(service, to: str, subject: str, body: str, dry_run: bool = False) -> dict:
    """
    이메일 발송

    Args:
        service: Gmail API 서비스 객체
        to: 수신자 이메일
        subject: 제목
        body: 본문
        dry_run: True면 실제 발송 안 함 (미리보기)

    Returns:
        발송 결과 (message id 등)
    """
    sender = get_user_email(service)
    message = create_message(to, subject, body, sender)

    if dry_run:
        return {
            'status': 'dry_run',
            'from': sender,
            'to': to,
            'subject': subject,
            'body': body
        }

    result = service.users().messages().send(userId='me', body=message).execute()
    return {
        'status': 'sent',
        'id': result.get('id'),
        'threadId': result.get('threadId'),
        'from': sender,
        'to': to,
        'subject': subject
    }


def main():
    parser = argparse.ArgumentParser(description='Gmail 이메일 발송')
    parser.add_argument('--to', required=True, help='수신자 이메일 주소')
    parser.add_argument('--subject', required=True, help='이메일 제목')
    parser.add_argument('--body', required=True, help='이메일 본문')
    parser.add_argument('--body-file', help='본문을 파일에서 읽기')
    parser.add_argument('--dry-run', action='store_true', help='실제 발송 없이 미리보기')
    parser.add_argument('--yes', '-y', action='store_true', help='확인 없이 바로 발송')

    args = parser.parse_args()

    # 본문 처리
    body = args.body
    if args.body_file:
        with open(args.body_file, 'r', encoding='utf-8') as f:
            body = f.read()

    # Gmail 서비스 연결
    try:
        service = get_gmail_service()
        sender = get_user_email(service)
    except Exception as e:
        print(f"Gmail 연결 실패: {e}", file=sys.stderr)
        sys.exit(1)

    # 미리보기 출력
    print("=" * 50)
    print("📧 이메일 미리보기")
    print("=" * 50)
    print(f"From: {sender}")
    print(f"To: {args.to}")
    print(f"Subject: {args.subject}")
    print("-" * 50)
    print(body)
    print("=" * 50)

    if args.dry_run:
        print("\n[Dry Run] 실제 발송되지 않았습니다.")
        return

    # 발송 확인
    if not args.yes:
        confirm = input("\n발송하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("발송이 취소되었습니다.")
            return

    # 발송
    try:
        result = send_email(service, args.to, args.subject, body)
        print(f"\n✅ 발송 완료!")
        print(f"   Message ID: {result.get('id')}")
    except Exception as e:
        print(f"\n❌ 발송 실패: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
