---
name: last-contact-updater
description: 인물사전 파일 본문에서 가장 최근 미팅 날짜를 추출하여 YAML last_contact 필드를 자동 업데이트하는 스킬. 사용 시점: (1) "마지막 연락일 업데이트해줘" (2) "last_contact 필드 동기화해줘" (3) 인물사전 파일에 새로운 미팅 기록 추가 후 (4) sheets-sync 실행 전 최신 연락일 정보 반영이 필요할 때 (5) vault-organizer 실행 후 YAML 필드 보완 작업
---

# Last Contact Updater

인물사전 파일의 본문에서 가장 최근 미팅 날짜를 추출하여 YAML `last_contact` 필드를 자동으로 업데이트하는 스킬입니다.

## 목적

각 인물사전 파일의 본문에서 가장 최근 미팅/대화 날짜를 추출하여 YAML frontmatter의 `last_contact` 필드에 반영합니다. 이를 통해 구글 시트 CRM에서 마지막 연락일 기준 정렬 및 필터링이 가능합니다.

## 사용 시점

1. "마지막 연락일 업데이트해줘"
2. "last_contact 필드 동기화해줘"
3. 인물사전 파일에 새로운 미팅 기록을 추가한 후
4. `sheets-sync` 스킬 실행 전 최신 연락일 정보를 반영할 때
5. `vault-organizer` 에이전트 실행 후 YAML 필드 보완 작업

## 실행 방법

### Dry-run (미리보기)

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/last-contact-updater/scripts/update_last_contact.py \
  "/path/to/vault/04_Networking/00_인물사전" \
  --dry-run
```

### 실제 업데이트

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/last-contact-updater/scripts/update_last_contact.py \
  "/path/to/vault/04_Networking/00_인물사전"
```

### 일부 파일만 처리

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/last-contact-updater/scripts/update_last_contact.py \
  "/path/to/vault/04_Networking/00_인물사전" \
  --limit 50
```

## 파라미터

| 파라미터 | 위치 | 필수 | 설명 |
|---------|------|------|------|
| `directory` | 1 | 필수 | 인물사전 디렉토리 경로 |
| `--dry-run` | 옵션 | 선택 | 실제 파일 수정 없이 미리보기만 |
| `--limit` | 옵션 | 선택 | 처리할 파일 수 제한 (테스트용) |

## 날짜 추출 알고리즘

### 지원하는 패턴

본문에서 다음 패턴의 날짜를 추출합니다:

#### 헤딩 기반

```markdown
## 2024.11.21 커피챗
## 2024-11-21 미팅
## 241121 전화
### 2024.11.21 후속 미팅
```

#### 불릿 포인트 기반

```markdown
- 2024.11.21: 첫 미팅
- 2024-11-21: 후속 논의
```

### 추출 로직

1. 모든 패턴에서 날짜 추출
2. `YYYY-MM-DD` 형식으로 정규화
3. 유효한 날짜인지 검증 (`datetime.strptime`)
4. **가장 최근 날짜**를 `last_contact`로 선택

### 짧은 형식 처리

- `241121` → `2024-11-21` (20YY 형식으로 자동 변환)

## 업데이트 규칙

### YAML 필드 업데이트

```yaml
---
title: 김창환
date: 2024-01-15
last_contact: 2024-11-21  # 본문에서 추출된 최근 날짜
# ... 기타 필드
---
```

### 조건

- 본문에서 날짜를 발견한 경우에만 업데이트
- 기존 `last_contact` 값과 다른 경우에만 업데이트
- `last_contact` 필드가 없으면 추가
- 날짜를 찾지 못하면 필드를 추가하지 않음

## 출력 예시

```
[DRY RUN] 총 278개 파일 처리 중...

## 업데이트된 파일:

  김창환_리얼월드.md: (없음) → 2024-11-21 (추가)
  박유빈_마음AI.md: 2024-10-15 → 2024-11-18 (변경)
  조쉬_ASC.md: (없음) → 2024-12-01 (추가)
  ... 외 114개

## 통계:
  - 전체 파일: 278개
  - 업데이트됨: 117개
    - 신규 추가: 89개
    - 값 변경: 28개
  - 스킵 (미팅 없음): 125개
  - 스킵 (동일): 36개

[DRY RUN] 실제 파일은 수정되지 않았습니다.
실제 업데이트하려면 --dry-run 옵션을 제거하세요.
```

## 후속 작업

업데이트 완료 후:
1. `sheets-sync` 스킬로 구글 시트 CRM 동기화 (마지막연락일 필드 반영)
2. `git-commit-push` 스킬로 변경사항 커밋

## 의존성

- Python 3.8+
- PyYAML: `pip install pyyaml`
- 가상환경: `/path/to/vault/.venv`

## 주의사항

1. **Dry-run 먼저 실행**: 항상 `--dry-run`으로 확인 후 실제 업데이트
2. **정확한 날짜 추출**: 본문의 헤딩/불릿에서만 추출 (일반 텍스트 내 날짜는 무시)
3. **최근 날짜만**: 여러 미팅 중 가장 최근 날짜만 반영
4. **NFD/NFC 정규화**: macOS 파일 시스템 호환을 위한 유니코드 정규화 처리
5. **YAML 보존**: 기존 YAML 필드 순서 및 내용 보존

## 활용 시나리오

### 시나리오 1: recording-processor 후 업데이트

```bash
# 1. 녹음 파일 처리로 새로운 미팅 노트 생성 (00_Inbox)
# 2. vault-organizer로 04_Networking/인물사전으로 이동
# 3. last-contact-updater로 마지막 연락일 업데이트
# 4. sheets-sync로 구글 시트에 반영
```

### 시나리오 2: 수동 미팅 기록 후 업데이트

```bash
# 1. 인물사전 파일에 ## 2024.11.21 미팅 섹션 수동 추가
# 2. last-contact-updater 실행으로 YAML 자동 업데이트
# 3. sheets-sync로 CRM 동기화
```

## 스킬 위치

```
.claude/skills/last-contact-updater/
├── SKILL.md (이 파일)
└── scripts/
    └── update_last_contact.py
```
