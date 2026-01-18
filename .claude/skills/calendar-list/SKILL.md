---
name: calendar-list
description: 구글 캘린더 일정 조회 스킬. 사용 시점: (1) "오늘 일정 보여줘" (2) "이번주 일정 확인" (3) "1월 일정 조회해줘" (4) "조쉬님과의 일정 확인" (5) "캘린더 일정 검색"
version: 1.0.0
author: 서인근
tags:
  - 구글캘린더
  - 일정조회
  - 스케줄
skill_type: managed
---

# calendar-list

구글 캘린더 일정을 조회하는 스킬입니다 (읽기 전용).

## 사용 시점

다음과 같은 요청이 있을 때 이 스킬을 사용하세요:

1. **"오늘 일정 보여줘"**
2. **"이번주 일정 확인"**
3. **"이번달 스케줄 알려줘"**
4. **"1월 일정 조회해줘"**
5. **"조쉬님과의 일정 확인"**
6. **"캘린더에서 미팅 검색해줘"**

## 실행 명령어

```bash
# 오늘 일정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --today

# 이번 주 일정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --week

# 이번 달 일정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --month

# 특정 기간 일정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py \
  --start 2025-01-01 --end 2025-01-31

# 특정 인물 관련 일정
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --person "조쉬"

# 검색어로 일정 찾기
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --query "커피챗"

# JSON 출력 (다른 스킬에서 사용)
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-list/scripts/list_events.py --today --json
```

## CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--today` | 오늘 일정 조회 |
| `--week` | 이번 주 일정 조회 |
| `--month` | 이번 달 일정 조회 |
| `--start YYYY-MM-DD` | 시작 날짜 |
| `--end YYYY-MM-DD` | 종료 날짜 |
| `--person NAME` | 특정 인물 관련 일정 필터 |
| `--query TEXT` | 검색어로 일정 찾기 |
| `--json` | JSON 형식으로 출력 |
| `--max N` | 최대 결과 수 (기본: 100) |

## 출력 예시

```
📅 2025-01-08 오늘의 일정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📆 2025-01-08 (수)
  10:00-11:00   | 조쉬님 커피챗 | Google Meet | 👥 2명
  14:00-15:00   | 김민주님 1:1 미팅 | 강남역
  18:00-19:00   | 앤틀러 네트워킹 | 구로디지털단지 | 👥 5명

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 3개 일정
```

## 환경변수

`.env` 파일에 다음 변수가 필요합니다:

```bash
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
GOOGLE_CALENDAR_ID=primary  # 또는 특정 캘린더 ID
```

## 사전 설정 (필수)

### 캘린더 공유 설정

Google Calendar에서 Service Account에 캘린더를 공유해야 합니다:

1. [Google Calendar](https://calendar.google.com) 접속
2. 설정 (⚙️) → 내 캘린더의 설정 → [대상 캘린더]
3. "특정 사용자와 공유" 섹션
4. 사용자 추가: `your-service-account@project.iam.gserviceaccount.com`
5. 권한: **"모든 일정 세부정보 보기"** (읽기 전용으로 충분)

## 에러 처리

| 에러 | 원인 | 해결방법 |
|------|------|----------|
| `403 Forbidden` | 캘린더 접근 권한 없음 | 캘린더 공유 설정 확인 |
| `GOOGLE_CREDENTIALS_PATH 없음` | 환경변수 미설정 | `.env` 파일 확인 |
| `키 파일을 찾을 수 없습니다` | JSON 파일 누락 | `.creds/crawler-hrm.json` 확인 |

## 의존성

```bash
pip install google-api-python-client google-auth python-dotenv pytz
```

## 주요 파일

| 파일 | 설명 |
|------|------|
| `scripts/list_events.py` | 메인 CLI 스크립트 |
| `google_api/calendar.py` | Calendar API 래퍼 |
| `google_api/base.py` | Google API 기본 클래스 |

## 관련 스킬

- **calendar-create**: 미팅 생성/수정
- **calendar-sync**: 캘린더 ↔ 인물사전 동기화
