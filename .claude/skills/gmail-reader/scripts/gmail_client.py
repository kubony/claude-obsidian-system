#!/usr/bin/env python3
"""
Gmail API Client - OAuth2 인증 및 API 연결 관리
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API 스코프 (읽기 전용)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# 기본 경로 설정
SKILL_DIR = Path(__file__).parent.parent
CREDS_DIR = Path(os.getenv('GMAIL_CREDS_DIR', '/Users/inkeun/projects/obsidian/.creds'))
CREDENTIALS_FILE = CREDS_DIR / 'oauth_client.json'  # 기존 OAuth 클라이언트 활용
TOKEN_FILE = CREDS_DIR / 'gmail_token.pickle'


def get_gmail_service():
    """
    Gmail API 서비스 객체 반환.
    첫 실행 시 브라우저에서 OAuth2 인증 필요.
    """
    creds = None

    # 저장된 토큰 확인
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # 토큰 갱신
            creds.refresh(Request())
        else:
            # 새로운 인증 필요
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"OAuth credentials 파일이 없습니다: {CREDENTIALS_FILE}\n"
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고\n"
                    "credentials.json을 다운로드하여 위 경로에 저장하세요."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    # Gmail API 서비스 생성
    service = build('gmail', 'v1', credentials=creds)
    return service


def get_user_email(service):
    """현재 인증된 사용자의 이메일 주소 반환"""
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('emailAddress', 'me')


if __name__ == '__main__':
    # 테스트: 인증 및 프로필 확인
    try:
        service = get_gmail_service()
        email = get_user_email(service)
        print(f"Gmail API 연결 성공!")
        print(f"인증된 계정: {email}")
    except FileNotFoundError as e:
        print(f"오류: {e}")
    except Exception as e:
        print(f"Gmail API 연결 실패: {e}")
