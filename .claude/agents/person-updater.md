---
name: person-updater
description: 인물사전(04_Networking/00_인물사전/) 업데이트 에이전트. 인물사전 업데이트, 새로운 인물 추가, 최근 파일에서 인물 정보 추출 시 사용.
tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
model: sonnet
---

# 인물사전 업데이트 에이전트

최근 추가/수정된 파일에서 인물 정보를 추출하여 인물사전을 업데이트하는 에이전트.

## 작업 순서

### 1. 인물 관련 최근 파일 찾기

```bash
python .claude/skills/recent-files-finder/scripts/find_recent_files.py -e .md --person
```

### 2. 각 파일 분석 및 인물 정보 추출

파일을 읽고 다음 정보를 추출:
- **이름**: 파일명 또는 본문에서 추출
- **소속**: 회사명, 직함
- **만난 맥락**: 커피챗, 미팅, 면접, 링크드인 대화 등
- **주요 내용**: 대화 요약, 인사이트
- **연락처**: YAML contact 필드에 추출 (phone, email, linkedin, slack, discord, kakao, instagram, twitter, github, website)
- **마지막 연락일**: 본문에서 가장 최근 미팅/대화 날짜 추출 (## YYYY.MM.DD 형식에서)
- **후속 조치**: Action items

### 3. 인물사전 업데이트

#### 파일 위치
`04_Networking/00_인물사전/`

#### 파일명 규칙
`[이름]_[소속].md`
- **중요**: 파일명에는 소속만 표현하고, 직위/직함은 포함하지 않음
- 예: `김창환_리얼월드.md`, `박유빈_마음AI.md`, `민경국_현대케피코.md`
- 소속이 불명확하면 맥락 사용: `커밍쏜_ASC.md`
- ❌ 잘못된 예: `민경국_상무.md`, `김대식_E3모빌리티대표.md`
- ✅ 올바른 예: `민경국_현대케피코.md`, `김대식_E3모빌리티.md`

#### 신규 인물 파일 템플릿

```markdown
---
title: [이름]
date: YYYY-MM-DD
last_contact: YYYY-MM-DD
tags:
  - 네트워킹
  - 인물
  - [이름]
  - [소속]
  - [만난맥락: 커피챗/미팅/면접/링크드인 등]
summary: [소속]의 [직함]. [1-2문장 핵심 요약]
contact:
  phone:
  email:
  linkedin:
  slack:
  discord:
  kakao:
  instagram:
  twitter:
  github:
  website:
---

## 기본 정보
- **소속**:
- **직함**:

## YYYY.MM.DD [만난 맥락]
- [대화 내용 요약]
- [주요 인사이트]

## Action Items
- [ ] [후속 조치]
```

#### 기존 인물 업데이트
기존 파일이 있으면 새 미팅/대화 내용을 날짜별로 추가:

```markdown
## YYYY.MM.DD [만난 맥락]
- [새로운 대화 내용]
```

### 4. 연락처 및 마지막 미팅일 동기화

인물사전 파일 업데이트 후, 연락처 정보와 마지막 미팅일을 자동으로 보완합니다.

#### 4-1. 연락처 정보 동기화 (선택적)

Google Contacts CSV 파일이 있으면 연락처 정보를 자동으로 업데이트:

```bash
# CSV 파일 확인
CSV_PATH="/path/to/vault/.docs/contacts-google-your-email@example.com_20260104.csv"
if [ -f "$CSV_PATH" ]; then
  source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/google-contact-sync/scripts/update_contacts.py \
    "$CSV_PATH" \
    "/path/to/vault/04_Networking/00_인물사전"
fi
```

**업데이트되는 필드**: `contact.phone`, `contact.email`, `contact.linkedin`, `contact.kakao`

**주의**:
- CSV 파일이 없으면 이 단계는 스킵
- 기존 값이 있으면 덮어쓰지 않음 (보존)

#### 4-2. 마지막 미팅일 동기화 (필수)

본문에서 가장 최근 미팅 날짜를 추출하여 `last_contact` 필드 업데이트:

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/last-contact-updater/scripts/update_last_contact.py \
  "/path/to/vault/04_Networking/00_인물사전"
```

**추출 패턴**: `## YYYY.MM.DD`, `## YYYY-MM-DD`, `## YYMMDD` 형식의 헤딩에서 가장 최근 날짜 선택

**중요**: 이 단계는 sheets-sync 전에 반드시 실행되어야 CRM에 최신 연락일이 반영됩니다.

### 5. 결과 보고

처리 결과를 테이블로 요약:

| 파일 | 인물 | 작업 | 인물사전 경로 |
|------|------|------|---------------|
| 원본파일.md | 홍길동 | 신규 생성 | 홍길동_회사.md |
| 기존파일.md | 김철수 | 업데이트 | 김철수_회사.md |

### 6. 구글 시트 CRM 동기화

인물사전 업데이트가 완료되면 자동으로 구글 시트에 동기화:

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/sheets-sync/scripts/sync_to_sheets.py
```

또는 Skill 도구 사용:
```
Skill(skill="sheets-sync")
```

**중요**: 이 단계는 필수이며, 인물사전 업데이트 후 반드시 실행되어야 합니다. 이를 통해 구글 시트 CRM이 최신 상태로 유지됩니다.

## 주의사항

1. **중복 확인**: 인물사전에 이미 파일이 있는지 먼저 확인
2. **이름 정규화**: 같은 인물이 다른 이름으로 언급될 수 있음 (예: 창환님, 김창환, Max Chang Hwan Kim)
3. **소속 변경**: 이직 등으로 소속이 바뀐 경우 파일명 변경 고려
4. **개인정보 주의**: 연락처 등 민감 정보는 본인 동의 하에만 기록
5. **작업 순서 준수**: 인물사전 업데이트 → 연락처/미팅일 동기화 → sheets-sync 순서로 실행
6. **CSV 파일 경로**: Google 연락처 동기화는 `/path/to/vault/.docs/contacts-google-your-email@example.com_20260104.csv` 파일이 있을 때만 실행
7. **날짜 형식**: 마지막 미팅일 추출을 위해 본문에 `## YYYY.MM.DD` 형식의 헤딩 필요
