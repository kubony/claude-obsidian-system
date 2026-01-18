---
name: sheets-sync
description: 옵시디언 인물사전(04_Networking/00_인물사전/)을 구글 시트로 동기화하여 CRM처럼 관리. 280+ 마크다운 파일에서 ID, 이름, 별명, 소속, 직급, 전화번호, 이메일, LinkedIn, GitHub, 최근미팅일자, 총미팅횟수, 마지막연락일, 최종수정일, 태그, 요약, 주요경력, 파일경로 등 17개 필드를 추출하여 ID 기반 증분 업데이트로 동기화합니다. 필터/정렬이 유지됩니다.
version: 3.0.0
author: 서인근
tags:
  - 구글시트
  - CRM
  - 인물사전
  - 동기화
  - 네트워킹
skill_type: managed
---

# sheets-sync

옵시디언 인물사전을 구글 시트 CRM으로 동기화하는 스킬입니다.

## 개요

280개 이상의 인물 마크다운 파일(`04_Networking/00_인물사전/*.md`)을 파싱하여 구글 시트에 동기화합니다. 각 파일에서 17개 필드를 추출하고, **ID 기반 증분 업데이트** 방식으로 시트를 갱신합니다.

**동기화 방향**: 인물사전 → 구글시트 (단방향)
**동기화 방식**: ID 매핑 기반 증분 업데이트 (필터/정렬 유지)

## 사용 시점

다음과 같은 요청이 있을 때 이 스킬을 사용하세요:

1. **"구글시트 동기화해줘"**
2. **"인물사전 시트 업데이트"**
3. **"CRM 동기화"**
4. **"인물 정보 시트에 반영해줘"**
5. **"구글시트 CRM 업데이트"**

## 추출 필드 (17개)

| 필드명 | 데이터 소스 | 설명 |
|--------|------------|------|
| **ID** | YAML `id` 또는 파일 경로 해시 | 고유 식별자 (person_xxxxxxxxxxxxxxxx) |
| 이름 | YAML `title` / 파일명 | 인물 이름 (괄호, 직급 suffix 자동 제거) |
| 별명 | 본문 "## 기본 정보" `닉네임` | 닉네임/별명 |
| 소속 | 파일명 (`이름_소속.md`) | 소속 조직/회사 |
| 직급 | 파일명 또는 YAML title suffix | 교수, 팀장, 대표 등 직급 |
| 전화번호 | YAML `contact.phone` / 본문 | 전화번호 |
| 이메일 | YAML `contact.email` / 본문 | 이메일 주소 |
| LinkedIn | YAML `contact.linkedin` / 본문 | LinkedIn 프로필 URL |
| GitHub | YAML `contact.github` / 본문 | GitHub 프로필 |
| 최근미팅일자 | 본문 `## YYYY.MM.DD` | 가장 최근 미팅 날짜 |
| 총미팅횟수 | 본문 미팅 섹션 개수 | 총 미팅 횟수 |
| 마지막연락일 | YAML `last_contact` | 마지막으로 연락한 날짜 |
| 최종수정일 | YAML `date` | 파일 최종 수정일 |
| 태그 | YAML `tags[]` | 쉼표 구분 태그 목록 |
| 요약 | YAML `summary` | 인물 요약 설명 |
| 주요경력 | 본문 "## 배경 및 경력" | 경력 요약 (200자 제한) |
| 파일경로 | 상대경로 | 파일 위치 |

## 실행 명령어

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/sheets-sync/scripts/sync_to_sheets.py
```

## 환경변수 (`.env`)

```bash
# Google Sheets CRM Sync
GOOGLE_SHEET_ID=your-google-sheet-id
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
```

## 의존성

- Python 3.10+
- gspread (`pip install gspread`)
- google-auth (`pip install google-auth`)
- PyYAML (`pip install pyyaml`)
- manage_gapi (로컬 프로젝트: `/path/to/user/projects/manage_gapi`)

## 주요 파일

| 파일 | 설명 |
|------|------|
| `scripts/sync_to_sheets.py` | 메인 동기화 스크립트 |
| `scripts/person_parser.py` | 마크다운 파싱 유틸리티 |
| `SKILL.md` | 스킬 메타데이터 |

## 실행 흐름

1. **환경변수 로드**: `.env`에서 `GOOGLE_SHEET_ID`, `GOOGLE_CREDENTIALS_PATH` 읽기
2. **구글 시트 인증**: GoogleSheetAPIManager로 서비스 계정 인증
3. **파일 스캔**: `04_Networking/00_인물사전/*.md` 파일 280개+ 탐색
4. **데이터 파싱**: 각 파일에서 17개 필드 추출
   - ID: YAML `id` 또는 파일 경로 해시
   - 이름: YAML `title` (괄호/직급 자동 제거)
   - 별명: 본문에서 "닉네임" 패턴 추출
   - 소속/직급: 파일명 파싱
   - 연락처: YAML `contact` 객체 (phone, email, linkedin, github)
   - 미팅정보: 본문 날짜 섹션 파싱
   - 마지막연락일: YAML `last_contact`
5. **정렬**: 이름 가나다순 정렬 (한글 → 영문)
6. **ID 매핑 읽기**: 시트의 A열에서 기존 ID 목록 조회
7. **증분 업데이트**:
   - 기존 ID → 해당 행 업데이트 (batch_update_values)
   - 신규 ID → 새 행 추가 (append)
8. **성공 메시지**: 업데이트/추가 개수 + 시트 URL 출력

## 출력 예시

```
============================================================
인물사전 → 구글시트 동기화 시작
============================================================

✅ 구글시트 인증 완료
📂 인물 파일 278개 발견
✅ 278명 파싱 완료
🔄 시트 업데이트 중 (ID 기반 증분 동기화)...
  ✓ 275행 업데이트
  ✓ 3행 추가
✅ 시트 동기화 완료: 275행 업데이트, 3행 추가

============================================================
✅ 완료: 278명의 정보를 구글시트에 동기화했습니다.
시트 URL: https://docs.google.com/spreadsheets/d/your-google-sheet-id
============================================================
```

## 에러 처리

| 에러 | 원인 | 해결방법 |
|------|------|----------|
| `GOOGLE_SHEET_ID 환경변수 없음` | `.env` 미설정 | `.env` 파일에 `GOOGLE_SHEET_ID` 추가 |
| `JSON 키 파일 없음` | 서비스 계정 JSON 누락 | `.creds/crawler-hrm.json` 파일 확인 |
| `구글시트 접근 실패` | 권한 부족 | 서비스 계정에 시트 편집 권한 부여 |
| `파일 파싱 실패` | YAML 형식 오류 | 경고 출력 후 다음 파일 계속 처리 |

## 주의사항

1. **증분 동기화**: ID 기반 매핑으로 기존 행은 업데이트, 신규 인물은 추가. **필터/정렬이 유지됩니다.**
2. **시트 편집**: 시트에서 데이터를 수동 편집해도 다음 동기화 시 마크다운 파일 내용으로 덮어쓰기됨. 데이터 수정은 마크다운에서 수행.
3. **필터/정렬 유지**: 시트에서 적용한 필터, 정렬, 행 이동은 동기화 후에도 유지됨 (ID 기반 매핑).
4. **ID 필드**: 모든 인물 파일은 YAML에 `id` 필드 필요. 없으면 파일 경로 해시로 자동 생성.
5. **한글 정렬**: macOS `ko_KR.UTF-8` 로케일 사용. 로케일 없으면 기본 유니코드 정렬.
6. **API 할당량**: 무료 계정은 분당 100개 요청. 배치 업데이트로 10-20개만 사용하므로 충분.

## 향후 개선 사항

- [ ] vault-organizer 통합 (Phase 7 추가)
- [ ] 증분 동기화 (git diff로 변경 파일만 업데이트)
- [ ] 경력 요약 LLM 생성 (OpenAI API)
- [ ] 시트 → 마크다운 양방향 동기화 (선택사항)

## 관련 문서

- **CLAUDE.md**: 프로젝트 전체 가이드
- **manage_gapi**: GoogleSheetAPIManager 클래스 문서
- **Plan 파일**: `/path/to/user/.claude/plans/ethereal-twirling-cerf.md`

## 라이선스

개인 사용 전용
