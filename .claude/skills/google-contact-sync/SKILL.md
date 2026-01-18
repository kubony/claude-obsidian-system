---
name: google-contact-sync
description: Google 연락처 CSV 파일에서 인물사전 파일의 contact 필드(phone, email, linkedin, kakao)를 자동으로 업데이트하는 스킬. 사용 시점: (1) "Google 연락처 동기화해줘" (2) "연락처 정보 업데이트해줘" (3) Google Contacts CSV를 내보낸 후 인물사전에 연락처 정보 일괄 추가가 필요할 때 (4) contact-matcher로 매칭 확인 후 실제 업데이트를 수행할 때
---

# Google Contact Sync

Google 연락처(CSV)에서 인물사전 파일의 contact 필드를 자동으로 업데이트하는 스킬입니다.

## 목적

Google Contacts에서 내보낸 CSV 파일을 파싱하여 인물사전 파일의 contact 필드(phone, email, linkedin, kakao)를 자동으로 채웁니다.

## 사용 시점

1. "Google 연락처 동기화해줘"
2. "연락처 정보 업데이트해줘"
3. Google Contacts에서 CSV 파일을 내보낸 후 인물사전에 연락처 정보를 일괄 추가할 때
4. `contact-matcher` 스킬로 매칭을 확인한 후 실제 업데이트를 수행할 때

## 연락처 파일 위치

```
/path/to/vault/.docs/contacts-google-your-email@example.com_20260104.csv
```

## 실행 방법

### Dry-run (미리보기)

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/google-contact-sync/scripts/update_contacts.py \
  "/path/to/vault/.docs/contacts-google-your-email@example.com_20260104.csv" \
  "/path/to/vault/04_Networking/00_인물사전" \
  --dry-run
```

### 실제 업데이트

```bash
source /path/to/vault/.venv/bin/activate && \
python /path/to/vault/.claude/skills/google-contact-sync/scripts/update_contacts.py \
  "/path/to/vault/.docs/contacts-google-your-email@example.com_20260104.csv" \
  "/path/to/vault/04_Networking/00_인물사전"
```

## 파라미터

| 파라미터 | 위치 | 필수 | 설명 |
|---------|------|------|------|
| `contact_file` | 1 | 필수 | Google Contacts CSV 파일 경로 |
| `person_dir` | 2 | 필수 | 인물사전 디렉토리 경로 |
| `--dry-run` | 옵션 | 선택 | 실제 파일 수정 없이 미리보기만 |

## Google CSV 필드 매핑

| Google CSV 필드 | 인물사전 필드 |
|----------------|--------------|
| First Name + Last Name | 매칭용 이름 |
| Organization Name | 매칭 참고 (소속) |
| Phone 1~4 - Value | contact.phone |
| E-mail 1~3 - Value | contact.email |

## 매칭 알고리즘

### 이름 매칭

1. CSV의 First Name + Last Name 조합 (한글은 Last Name + First Name)
2. 연락처 이름에서 불필요한 텍스트 제거:
   - 직위: 팀장, 대리, 선임, 책임, 과장, 부장, 이사, 사원
   - 날짜: YYYYMMDD 형식
3. 파일명(`이름_소속.md`)의 이름 부분과 비교
4. 정확히 일치하거나 이름이 포함되면 매칭 성공

### 소속 검증 (동명이인 방지) - 2026-01-11 추가

이름만으로 매칭 시 동명이인 문제가 발생할 수 있어 소속 검증 로직이 추가됨:

1. **1개 파일만 매칭된 경우에도 소속 검증**:
   - CSV의 Organization Name과 파일명의 소속(`이름_소속.md`)을 비교
   - 소속이 다르면 스킵 → `[SKIP] 소속 불일치` 로그 출력

2. **여러 파일이 매칭된 경우 (동명이인)**:
   - 소속으로 구분 시도
   - 소속 일치 파일이 1개면 매칭, 0개 또는 여러 개면 스킵

3. **이메일 도메인에서 소속 추론**:
   - CSV에 Organization Name이 없으면 이메일 도메인에서 추론
   - 예: `@hyundai-kefico.com` → 현대케피코
   - **개인 이메일 제외**: gmail.com, naver.com, kakao.com 등은 추론 불가

#### 이메일 도메인 매핑 (EMAIL_DOMAIN_TO_ORG)

| 도메인 | 추론 소속 |
|-------|----------|
| kefico.co.kr, hyundai-kefico.com | 현대케피코 |
| hyundai.com | 현대자동차 |
| lgchem.com | LG화학 |
| nuvi-labs.com | 누비랩 |
| antler.co | 앤틀러코리아 |
| maum.ai | 마음AI |
| ... | (스크립트 참조) |

### 필드 업데이트 규칙

- **기존 값이 없는 경우에만** 업데이트 (덮어쓰지 않음)
- 업데이트 대상 필드:
  - `contact.phone`: 전화번호 (010-XXXX-XXXX 형식으로 자동 변환)
  - `contact.email`: 이메일
  - `contact.linkedin`: LinkedIn URL
  - `contact.kakao`: 카카오 ID

## 출력 예시

```
[DRY RUN] Google CSV 파일 파싱 중...

총 1234개 연락처 발견

인물사전 파일 278개

## 업데이트된 파일:

  김창환_리얼월드.md: phone, email
  박유빈_마음AI.md: phone, linkedin
  조쉬_ASC.md: email
  ... 외 41개

## 통계:
  - 총 연락처: 1234개
  - 매칭됨: 156개
  - 업데이트됨: 44개
  - 스킵 (이미 있음): 112개
  - 매칭 실패: 1078개

[DRY RUN] 실제 파일은 수정되지 않았습니다.
실제 업데이트하려면 --dry-run 옵션을 제거하세요.
```

## YAML 필드 구조

업데이트되는 YAML contact 필드 구조:

```yaml
contact:
  phone: 010-1234-5678
  email: user@example.com
  linkedin: https://linkedin.com/in/username
  slack: null
  discord: null
  kakao: kakao_id
  instagram: null
  twitter: null
  github: null
  website: null
```

- 빈 필드는 `null`로 초기화됨
- 기존에 값이 있으면 보존됨

## 후속 작업

업데이트 완료 후:
1. `sheets-sync` 스킬로 구글 시트 CRM 동기화
2. `git-commit-push` 스킬로 변경사항 커밋

## 의존성

- Python 3.8+
- PyYAML: `pip install pyyaml`
- 가상환경: `/path/to/vault/.venv`

## 주의사항

1. **Dry-run 먼저 실행**: 항상 `--dry-run`으로 확인 후 실제 업데이트
2. **덮어쓰기 방지**: 기존에 값이 있으면 업데이트하지 않음
3. **백업 권장**: 대량 업데이트 전 Git 커밋 권장
4. **NFD/NFC 정규화**: macOS 파일 시스템 호환을 위한 유니코드 정규화 처리

## 알려진 제한사항

1. **동명이인 처리 한계**: 소속이 같은 동명이인(같은 회사의 "김철수" 2명)은 구분 불가 → 스킵됨
2. **소속 매칭 정확도**: "현대자동차" vs "현대" 같은 부분 일치는 매칭 안 됨
3. **이메일 도메인 확장**: 새 회사 추가 시 `update_contacts.py`의 `EMAIL_DOMAIN_TO_ORG` 수정 필요

## 스킬 위치

```
.claude/skills/google-contact-sync/
├── SKILL.md (이 파일)
└── scripts/
    └── update_contacts.py
```
