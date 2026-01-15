---
name: gmail-reader
description: Gmail API를 통해 이메일을 검색하고 조회합니다. 미팅/일정 메일 추출, 특정 인물과의 이메일 히스토리 조회에 활용.
version: 1.0.0
author: claude
triggers:
  - 이메일 검색해줘
  - 메일 찾아줘
  - Gmail 확인해줘
  - 미팅 메일 찾아줘
  - "[인물명]과의 메일 히스토리"
tools:
  - Bash
  - Read
---

# Gmail Reader 스킬

Gmail API를 활용하여 이메일을 검색하고 조회하는 스킬입니다.

## 주요 기능

1. **이메일 검색** - Gmail 검색 쿼리로 메일 검색
2. **미팅/일정 메일 추출** - 최근 미팅 관련 이메일 자동 필터링
3. **인물별 이메일 히스토리** - 특정 인물과 주고받은 메일 조회
4. **미읽음/최근 메일 조회** - 읽지 않은 메일, 최근 메일 확인

## 사전 설정 (최초 1회)

### 1. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **APIs & Services > Library**에서 **Gmail API** 활성화
4. **APIs & Services > Credentials**에서:
   - **Create Credentials > OAuth client ID** 선택
   - Application type: **Desktop app**
   - 이름 입력 후 생성
5. 생성된 OAuth 클라이언트에서 **JSON 다운로드**
6. 다운로드한 파일을 아래 경로에 저장:
   ```
   /Users/inkeun/projects/obsidian/.creds/gmail_oauth_credentials.json
   ```

### 2. 첫 실행 시 인증

```bash
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/gmail-reader/scripts/gmail_client.py
```

- 브라우저가 열리고 Google 계정 로그인 요청
- 권한 승인 후 토큰이 자동 저장됨 (`gmail_token.pickle`)
- 이후에는 자동으로 토큰 갱신됨

## 사용법

### 기본 검색

```bash
# Gmail 검색 쿼리로 검색
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/gmail-reader/scripts/search_emails.py \
    --query "subject:미팅" --max 10

# 최근 7일 메일 (기본)
python .claude/skills/gmail-reader/scripts/search_emails.py --days 7
```

### 미팅/일정 관련 메일

```bash
# 최근 7일 미팅 관련 메일
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/gmail-reader/scripts/search_emails.py \
    --meetings --days 7

# 최근 30일 미팅 메일
python .claude/skills/gmail-reader/scripts/search_emails.py --meetings --days 30 --max 50
```

### 특정 인물 관련 메일

```bash
# 특정 인물로부터 받은 메일
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/gmail-reader/scripts/search_emails.py \
    --from-person "홍길동"

# 특정 인물과의 전체 이메일 히스토리 (주고받은 메일 모두)
python .claude/skills/gmail-reader/scripts/search_emails.py \
  --with-person "example@gmail.com" --max 30
```

### 개별 이메일 조회

```bash
# 읽지 않은 메일 확인
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/gmail-reader/scripts/get_email.py \
    --unread --max 10

# 최근 메일 확인
python .claude/skills/gmail-reader/scripts/get_email.py --recent

# 특정 이메일 상세 조회 (ID 필요)
python .claude/skills/gmail-reader/scripts/get_email.py --id "18d1234abcd5678"

# 스레드 전체 대화 조회
python .claude/skills/gmail-reader/scripts/get_email.py --thread "18d1234abcd5678"
```

### JSON 출력 (파이프라인용)

```bash
# JSON 형식으로 출력
python .claude/skills/gmail-reader/scripts/search_emails.py --meetings --json

# 본문 포함 JSON 출력
python .claude/skills/gmail-reader/scripts/search_emails.py --query "from:앤틀러" --body --json
```

## Gmail 검색 쿼리 예시

| 용도 | 쿼리 |
|------|------|
| 발신자 검색 | `from:example@gmail.com` |
| 수신자 검색 | `to:example@gmail.com` |
| 제목 검색 | `subject:미팅` |
| 본문 키워드 | `회의 일정` |
| 날짜 이후 | `after:2025/01/01` |
| 날짜 이전 | `before:2025/12/31` |
| 첨부파일 있음 | `has:attachment` |
| 별표 표시 | `is:starred` |
| 읽지 않음 | `is:unread` |
| 라벨 검색 | `label:중요` |
| 복합 검색 | `from:김철수 subject:미팅 after:2025/01/01` |

## 활용 시나리오

### 1. 미팅 메일에서 일정 추출 → 볼트에 기록

```bash
# 미팅 메일 검색
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python .claude/skills/gmail-reader/scripts/search_emails.py --meetings --days 14 --json > /tmp/meetings.json

# 결과를 기반으로 볼트에 미팅 노트 생성 (Claude가 처리)
```

### 2. 인물사전 연동 - 특정 인물과의 연락 히스토리

```bash
# 인물사전에서 이메일 확인 후 히스토리 조회
python .claude/skills/gmail-reader/scripts/search_emails.py \
  --with-person "이성용" --max 20

# 결과로 last_contact 필드 업데이트 가능
```

### 3. 네트워킹 후속 연락 관리

```bash
# 최근 앤틀러 관련 메일 확인
python .claude/skills/gmail-reader/scripts/search_emails.py \
  --query "앤틀러 OR Antler" --days 30

# 특정 조직 관련 메일
python .claude/skills/gmail-reader/scripts/search_emails.py \
  --query "from:@antler.co OR from:앤틀러" --max 50
```

## 파일 구조

```
.claude/skills/gmail-reader/
├── SKILL.md                    # 이 파일
└── scripts/
    ├── gmail_client.py         # Gmail API 클라이언트 (인증)
    ├── search_emails.py        # 이메일 검색
    └── get_email.py            # 개별 이메일 조회
```

## 필요 패키지

```bash
# 루트 venv에 설치
source /Users/inkeun/projects/obsidian/.venv/bin/activate
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## 주의사항

- **읽기 전용**: 이 스킬은 이메일 읽기/검색만 지원합니다 (보내기, 삭제 불가)
- **개인 계정용**: OAuth2 인증이므로 개인 Gmail 계정에서 사용
- **토큰 만료**: 장기간 미사용 시 토큰이 만료될 수 있음 (재인증 필요)
- **API 할당량**: 일일 API 호출 제한이 있음 (일반 사용에는 충분)

## 트러블슈팅

### "OAuth credentials 파일이 없습니다" 오류
→ Google Cloud Console에서 OAuth 클라이언트 생성 후 JSON 다운로드 필요

### "Token has been expired or revoked" 오류
→ `gmail_token.pickle` 파일 삭제 후 재인증:
```bash
rm /Users/inkeun/projects/obsidian/.creds/gmail_token.pickle
python .claude/skills/gmail-reader/scripts/gmail_client.py
```

### "Access blocked" 오류
→ Google Cloud Console에서 OAuth 동의 화면 설정 필요
- User Type: External 선택
- 테스트 사용자에 본인 이메일 추가
