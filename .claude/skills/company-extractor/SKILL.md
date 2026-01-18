# company-extractor

인물사전 파일에서 회사/조직 목록을 추출하는 스킬.

## 사용 시점

- 법인사전 구축 시 회사 목록 파악
- company-updater 에이전트의 Phase 1에서 호출
- "회사 목록 추출해줘", "법인사전에 추가할 회사 찾아줘"

## 기능

1. `04_Networking/00_인물사전/*.md` 스캔
2. 파일명 패턴 `이름_소속.md`에서 소속(회사) 추출
3. 회사별 인원수 및 인물 목록 집계
4. 비법인 필터링 (가족, 간병, 본인 등)
5. 기존 법인사전 파일과 비교하여 신규 여부 판단
6. JSON 형식으로 출력

## 실행 방법

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/company-extractor/scripts/extract_companies.py
```

### 옵션

```bash
# 기본 실행 (JSON 출력)
python extract_companies.py

# 인원 기준 필터링 (3명 이상인 회사만)
python extract_companies.py --min-count 3

# 테이블 형식 출력
python extract_companies.py --format table

# 신규 회사만 출력
python extract_companies.py --new-only
```

## 출력 형식

### JSON (기본)

```json
{
  "companies": [
    {
      "name": "누비랩",
      "person_count": 22,
      "persons": ["김종호", "이유정", "주서희"],
      "is_new": true
    }
  ],
  "total_companies": 50,
  "new_companies": 45,
  "excluded": ["가족", "간병", "본인", "기타"]
}
```

### 테이블 (--format table)

```
| 회사명 | 인원수 | 신규 |
|--------|--------|------|
| 앤틀러5기 | 67 | O |
| 앤틀러7기 | 52 | O |
| ASC | 37 | O |
```

## 필터링 규칙

### 제외 대상 (비법인)

- 가족, 간병, 본인, 기타
- 개인셀러, ASC강사
- 못디동기 (대학 동기)
- 소속 없는 파일 (예: `박성수.md`)

## 의존성

- Python 3.9+
- unicodedata (표준 라이브러리)

## 파일 구조

```
company-extractor/
├── SKILL.md
└── scripts/
    └── extract_companies.py
```
