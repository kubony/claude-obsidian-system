---
name: calendar-sync
description: 구글 캘린더 일정을 인물사전에 자동 동기화. 사용 시점: (1) "캘린더 동기화해줘" (2) "오늘 미팅 인물사전에 기록해줘" (3) "이번주 일정 동기화" (4) "캘린더에서 미팅 기록 가져와"
version: 1.0.0
author: 서인근
tags:
  - 구글캘린더
  - 인물사전
  - 동기화
  - 미팅기록
skill_type: managed
---

# calendar-sync

구글 캘린더 일정을 인물사전 파일에 자동으로 동기화하는 스킬입니다.

## 사용 시점

다음과 같은 요청이 있을 때 이 스킬을 사용하세요:

1. **"캘린더 동기화해줘"**
2. **"오늘 미팅 인물사전에 기록해줘"**
3. **"이번주 일정 동기화"**
4. **"캘린더에서 미팅 기록 가져와"**

## 실행 명령어

```bash
# 오늘 일정 동기화
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-sync/scripts/sync_to_person.py --today

# 이번 주 일정 동기화
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-sync/scripts/sync_to_person.py --week

# 특정 기간 동기화
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-sync/scripts/sync_to_person.py \
  --start 2025-01-01 --end 2025-01-08

# Dry-run (미리보기)
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-sync/scripts/sync_to_person.py --today --dry-run

# 특정 인물만 동기화
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/calendar-sync/scripts/sync_to_person.py --today --person "조쉬"
```

## CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--today` | 오늘 일정 동기화 |
| `--week` | 이번 주 일정 동기화 |
| `--start YYYY-MM-DD` | 시작 날짜 |
| `--end YYYY-MM-DD` | 종료 날짜 |
| `--person NAME` | 특정 인물만 동기화 |
| `--dry-run` | 미리보기 (실제 변경 없음) |

## 동기화 로직

1. **캘린더 이벤트 조회**: 지정 기간의 이벤트 가져오기
2. **인물 매칭**: 이벤트 참석자/제목에서 인물 찾기
   - 이메일 매칭 (YAML contact.email)
   - 이름 매칭 (파일명, YAML title)
3. **중복 검사**: 이벤트 ID로 이미 동기화된 항목 스킵
4. **파일 업데이트**: "## 미팅/대화 기록" 섹션에 추가

## 인물사전 업데이트 형식

```markdown
## 미팅/대화 기록

### 2025.01.08 캘린더 일정
- **시간**: 10:00-11:00
- **장소**: [Google Meet](https://meet.google.com/xxx-xxxx-xxx)
- **참석자**: 서인근, 조쉬
- **원본**: [캘린더 링크](https://calendar.google.com/...)
<!-- calendar_event_id: abc123xyz -->

(기존 미팅 기록...)
```

## 출력 예시

### Dry-run 모드

```
📋 캘린더 → 인물사전 동기화 (오늘)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Dry-run 모드: 실제 변경 없음

🔍 2025.01.08 10:00 조쉬님 커피챗
   → 조쉬_ASC.md (email: attendee@example.com)

🔍 2025.01.08 14:00 김민주님 미팅
   → 김민주_앤틀러7기.md (name: 김민주)

⏭️ 매칭 없음 (1개):
   - 2025.01.08 18:00 앤틀러 네트워킹

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
완료: 2개 동기화
      1개 매칭 없음
```

### 실제 동기화

```
📋 캘린더 → 인물사전 동기화 (오늘)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 2025.01.08 10:00 조쉬님 커피챗
   → 조쉬_ASC.md (email: attendee@example.com)
   ✅ 동기화 완료

📅 2025.01.08 14:00 김민주님 미팅
   → 김민주_앤틀러7기.md (name: 김민주)
   ✅ 동기화 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
완료: 2개 동기화
```

## 환경변수

`.env` 파일에 다음 변수가 필요합니다:

```bash
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
GOOGLE_CALENDAR_ID=primary
```

## 사전 설정 (필수)

### 캘린더 공유 설정

Google Calendar에서 Service Account에 캘린더를 공유해야 합니다:

1. [Google Calendar](https://calendar.google.com) 접속
2. 설정 (⚙️) → 내 캘린더의 설정 → [대상 캘린더]
3. "특정 사용자와 공유" 섹션
4. 사용자 추가: `your-service-account@project.iam.gserviceaccount.com`
5. 권한: **"모든 일정 세부정보 보기"** (읽기 권한으로 충분)

## 매칭 알고리즘

### 우선순위

1. **이메일 매칭**: 참석자 이메일 → 인물사전 YAML `contact.email`
2. **이름 매칭**: 이벤트 제목에서 이름 추출 → 파일명/YAML title

### 이름 추출 패턴

- `"조쉬님 커피챗"` → "조쉬"
- `"김민주님 1:1 미팅"` → "김민주"
- 한글 이름 (2-4자) 자동 인식

## 중복 방지

- 각 미팅 기록에 이벤트 ID를 HTML 주석으로 저장
- 재동기화 시 이미 있는 이벤트는 자동 스킵
- 같은 이벤트를 여러 번 실행해도 안전

## 에러 처리

| 에러 | 원인 | 해결방법 |
|------|------|----------|
| `403 Forbidden` | 캘린더 접근 권한 없음 | 캘린더 공유 설정 확인 |
| `매칭 없음` | 인물사전에 해당 인물 없음 | 인물 파일 생성 또는 이메일 추가 |

## 의존성

```bash
pip install google-api-python-client google-auth python-dotenv pytz pyyaml
```

## 주요 파일

| 파일 | 설명 |
|------|------|
| `scripts/sync_to_person.py` | 메인 동기화 CLI |
| `scripts/person_matcher.py` | 인물 매칭 유틸리티 |
| `google_api/calendar.py` | Calendar API 래퍼 |

## 관련 스킬

- **calendar-list**: 일정 조회
- **calendar-create**: 미팅 생성/수정
- **last-contact-updater**: 동기화 후 last_contact 업데이트에 활용 가능
