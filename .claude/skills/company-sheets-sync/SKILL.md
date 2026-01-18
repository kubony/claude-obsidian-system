# company-sheets-sync

법인사전 마크다운 파일을 구글시트 CRM으로 동기화하는 스킬.

## 사용 시점

- 법인사전 업데이트 후 구글시트 반영
- company-updater 에이전트의 Phase 4에서 호출
- "법인사전 시트 동기화해줘", "회사 CRM 업데이트"

## 기능

1. `04_Networking/01_법인사전/*.md` 스캔
2. YAML front matter 및 본문에서 필드 추출
3. 기존 CRM 시트의 '법인사전' 탭에 ID 기반 증분 동기화
4. 사용자 필터/정렬 유지

## 실행 방법

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/company-sheets-sync/scripts/sync_companies.py
```

## 시트 구조 (13개 필드)

| 컬럼 | 설명 | 소스 |
|------|------|------|
| ID | company_xxx | YAML `id` |
| 회사명 | 법인 이름 | 파일명 |
| 유형 | 스타트업/대기업/VC/커뮤니티 | YAML `type` |
| 업종 | AI/핀테크/헬스케어... | YAML `industry` |
| 설립년도 | YYYY | YAML `founded` |
| 대표자 | 이름 | YAML `ceo` |
| 홈페이지 | URL | YAML `website` |
| 소속인원수 | 숫자 | 인물사전 연계 |
| 인물목록 | 쉼표 구분 | 소속 인물 섹션 |
| 설명 | 100자 요약 | YAML `description` |
| 최종수정일 | YYYY-MM-DD | YAML `date` |
| 태그 | 쉼표 구분 | YAML `tags` |
| 파일경로 | 상대경로 | 파일 위치 |

## 동기화 방식

### ID 기반 증분 동기화
- 기존 ID 존재: 해당 행 업데이트
- 신규 ID: 새 행 추가
- 사용자 필터/정렬 유지됨

### 탭 구조
- 기존 시트의 '법인사전' 탭 사용
- 탭 없으면 자동 생성

## 환경변수

`.env` 파일에 설정 필요:

```bash
GOOGLE_SHEET_ID=your-google-sheet-id
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
```

## 의존성

- Python 3.9+
- google-api-python-client
- google-auth
- python-dotenv
- PyYAML

## 파일 구조

```
company-sheets-sync/
├── SKILL.md
├── scripts/
│   ├── sync_companies.py
│   └── company_parser.py
└── google_api/
    └── sheets.py  (sheets-sync에서 복사)
```
