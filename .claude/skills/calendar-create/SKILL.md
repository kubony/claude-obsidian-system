---
name: calendar-create
description: 구글 캘린더 미팅 생성/수정 스킬. 사용 시점: (1) "조쉬님과 미팅 잡아줘" (2) "내일 3시에 커피챗 일정 만들어줘" (3) "Google Meet 미팅 생성해줘" (4) "일정 수정해줘" (5) "미팅 삭제해줘"
version: 1.0.0
author: 서인근
tags:
  - 구글캘린더
  - 미팅생성
  - 일정관리
skill_type: managed
---

# calendar-create

구글 캘린더 미팅을 생성하고 수정하는 스킬입니다.

## 사용 시점

다음과 같은 요청이 있을 때 이 스킬을 사용하세요:

1. **"조쉬님과 미팅 잡아줘"**
2. **"내일 3시에 커피챗 일정 만들어줘"**
3. **"김민주님과 Google Meet 미팅 생성"**
4. **"일정 수정해줘"**
5. **"미팅 삭제해줘"**

## 실행 명령어

### 이벤트 생성

```bash
# 기본 이벤트 생성
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/create_event.py \
  --title "미팅" \
  --date 2025-01-15 \
  --time 14:00-15:00

# 인물 지정 (인물사전에서 이메일 자동 조회)
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/create_event.py \
  --person "조쉬" \
  --title "커피챗" \
  --date 2025-01-15 \
  --time 14:00-15:00

# Google Meet 자동 생성
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/create_event.py \
  --person "조쉬" \
  --title "온라인 미팅" \
  --date 2025-01-20 \
  --time 10:00-11:00 \
  --meet

# 장소 지정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/create_event.py \
  --title "미팅" \
  --date 2025-01-15 \
  --time 14:00-15:00 \
  --location "강남역 스타벅스"

# Dry-run (미리보기)
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/create_event.py \
  --person "조쉬" \
  --title "테스트" \
  --date 2025-01-20 \
  --time 15:00-16:00 \
  --dry-run
```

### 이벤트 수정

```bash
# 이벤트 ID로 수정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/update_event.py \
  --event-id abc123 \
  --title "새 제목"

# 시간 변경
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/update_event.py \
  --event-id abc123 \
  --time 15:00-16:00

# 검색 후 수정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/update_event.py \
  --search "조쉬 커피챗" \
  --location "판교 카페"

# 이벤트 삭제
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/update_event.py \
  --event-id abc123 \
  --delete
```

### 인물 정보 조회

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-create/scripts/person_lookup.py "조쉬"
```

## CLI 옵션

### create_event.py

| 옵션 | 설명 |
|------|------|
| `--title` | 이벤트 제목 (필수) |
| `--date` | 날짜 YYYY-MM-DD (필수) |
| `--time` | 시간 범위 HH:MM-HH:MM (필수) |
| `--person` | 인물명 (인물사전에서 이메일 자동 조회) |
| `--email` | 참석자 이메일 (직접 지정) |
| `--location` | 장소 |
| `--description` | 설명 |
| `--meet` | Google Meet 링크 자동 생성 |
| `--no-notify` | 이메일 알림 비활성화 |
| `--dry-run` | 미리보기 (실제 생성 안 함) |

### update_event.py

| 옵션 | 설명 |
|------|------|
| `--event-id` | 이벤트 ID (필수, --search와 택일) |
| `--search` | 검색어로 이벤트 찾기 (필수, --event-id와 택일) |
| `--title` | 새 제목 |
| `--date` | 새 날짜 |
| `--time` | 새 시간 범위 |
| `--location` | 새 장소 |
| `--description` | 새 설명 |
| `--delete` | 이벤트 삭제 |
| `--no-notify` | 이메일 알림 비활성화 |
| `--dry-run` | 미리보기 |

## 출력 예시

### 생성 성공

```
✅ 인물사전에서 '조쉬 (Josh)' 찾음
   이메일: attendee@example.com

==================================================
📅 이벤트 미리보기
==================================================
제목: 커피챗
일시: 2025-01-15 (수) 14:00 - 15:00
화상회의: Google Meet (자동 생성)
참석자: attendee@example.com
==================================================

✅ 이벤트 생성 완료!

🔗 캘린더 링크: https://calendar.google.com/calendar/event?eid=...
🎥 Google Meet: https://meet.google.com/xxx-xxxx-xxx
📝 이벤트 ID: abc123xyz
```

## 환경변수

`.env` 파일에 다음 변수가 필요합니다:

```bash
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
GOOGLE_CALENDAR_ID=primary
```

## 사전 설정 (필수)

### 캘린더 공유 설정

Google Calendar에서 Service Account에 **쓰기 권한** 부여:

1. [Google Calendar](https://calendar.google.com) 접속
2. 설정 (⚙️) → 내 캘린더의 설정 → [대상 캘린더]
3. "특정 사용자와 공유" 섹션
4. 사용자 추가: `your-service-account@project.iam.gserviceaccount.com`
5. 권한: **"변경 및 공유 관리 권한"** (쓰기 필요!)

## 인물사전 연동

`--person` 옵션 사용 시 인물사전(`04_Networking/00_인물사전/`)에서 자동으로 이메일을 조회합니다.

**검색 순서:**
1. 파일명 정확 일치 (이름_소속.md)
2. 파일명 부분 일치
3. YAML title 일치

## 에러 처리

| 에러 | 원인 | 해결방법 |
|------|------|----------|
| `403 Forbidden` | 쓰기 권한 없음 | 캘린더 공유 권한을 "변경 및 공유 관리"로 변경 |
| `인물을 찾을 수 없습니다` | 인물사전에 없음 | --email 옵션으로 직접 이메일 지정 |
| `Invalid time format` | 시간 형식 오류 | HH:MM-HH:MM 형식 사용 |

## 의존성

```bash
pip install google-api-python-client google-auth python-dotenv pytz pyyaml
```

## 주요 파일

| 파일 | 설명 |
|------|------|
| `scripts/create_event.py` | 이벤트 생성 CLI |
| `scripts/update_event.py` | 이벤트 수정/삭제 CLI |
| `scripts/person_lookup.py` | 인물사전 조회 유틸리티 |
| `google_api/calendar.py` | Calendar API 래퍼 (쓰기 권한) |

## 관련 스킬

- **calendar-list**: 일정 조회
- **calendar-sync**: 캘린더 ↔ 인물사전 동기화
