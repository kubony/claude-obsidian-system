---
name: ontology-engine
description: Obsidian 볼트를 인물/프로젝트 중심 RDF/TTL 온톨로지로 변환하고 SPARQL 질의를 수행하는 개인 지식 엔진. 사용 시점: (1) "[인물명]에 대해 알려줘/설명해줘" (2) "[인물명]과 나눈 대화 보여줘" (3) "앤틀러 소속 인물 찾아줘" (4) "인물사전에서 [키워드] 검색" (5) "최근 미팅 목록" (6) "진행 중인 프로젝트 보여줘" (7) "[프로젝트명] 관련 정보" (8) "챗봇 관련 프로젝트 찾아줘" (9) 인물 간 관계나 미팅/프로젝트 기록을 구조적으로 질의할 때.
---

# Ontology Engine

Obsidian 인물사전 및 프로젝트를 RDF 온톨로지로 변환하고 SPARQL로 질의하는 개인 지식 엔진.

## 필수: 가상환경 사용

**중요:** 시스템 Python에 직접 설치 금지. 루트 `.venv` 사용.

**경로:** `/path/to/vault/.venv`

모든 스크립트 실행 시 아래 패턴 사용:
```bash
source /path/to/vault/.venv/bin/activate && cd /path/to/vault/.claude/skills/ontology-engine && python scripts/...
```

## 워크플로우

```
1. 변환: vault_to_ttl.py 실행 → knowledge.ttl 생성
2. 질의: query_knowledge.py로 SPARQL 질의 수행
```

## 1. 변환 (볼트 → TTL)

```bash
source /path/to/vault/.venv/bin/activate && cd /path/to/vault/.claude/skills/ontology-engine && python scripts/vault_to_ttl.py /path/to/vault --output knowledge.ttl
```

**변환 대상:**
- `04_Networking/00_인물사전/*.md` → Person
- `00_A_Projects/Active/`, `00_A_Projects/Planning/` → Project (활성)
- `90_Archives/` → Project (아카이브)

**추출 정보:**
- Person: 파일명, YAML(title, tags, summary)
- Project: 폴더명 (YYMM 프로젝트명), 태그, 요약
- Meeting: `## YYYY.MM.DD` 섹션 → 날짜 + 내용
- Organization: 파일명의 `_소속` 부분
- Topic: 미팅 내용의 해시태그 및 키워드
- 관계: `[[위키링크]]` → knows/involvedIn 관계

## 2. 질의 (SPARQL)

### 프리셋 쿼리

**모든 명령은 루트 venv 활성화 후 스킬 디렉토리에서 실행:**

```bash
source /path/to/vault/.venv/bin/activate && cd /path/to/vault/.claude/skills/ontology-engine

# 모든 인물
python scripts/query_knowledge.py knowledge.ttl --preset all_persons

# 특정 인물과의 미팅 (예: "조쉬에 대해 알려줘" → person_meetings)
python scripts/query_knowledge.py knowledge.ttl --preset person_meetings --param "조쉬"

# 특정 인물과 논의한 주제
python scripts/query_knowledge.py knowledge.ttl --preset person_topics --param "신동순"

# 특정 월 미팅
python scripts/query_knowledge.py knowledge.ttl --preset meetings_by_date --param "2024-11"

# 조직별 인물
python scripts/query_knowledge.py knowledge.ttl --preset org_members --param "앤틀러"

# 최근 미팅 10개
python scripts/query_knowledge.py knowledge.ttl --preset recent_meetings

# 키워드 검색
python scripts/query_knowledge.py knowledge.ttl --preset search_keyword --param "투자"

# 통계
python scripts/query_knowledge.py knowledge.ttl --preset stats

# === 프로젝트 관련 ===

# 모든 프로젝트
python scripts/query_knowledge.py knowledge.ttl --preset all_projects

# 활성 프로젝트
python scripts/query_knowledge.py knowledge.ttl --preset active_projects

# 아카이브된 프로젝트
python scripts/query_knowledge.py knowledge.ttl --preset archived_projects

# 프로젝트 검색
python scripts/query_knowledge.py knowledge.ttl --preset search_projects --param "챗봇"

# 특정 프로젝트 상세
python scripts/query_knowledge.py knowledge.ttl --preset project_details --param "영정사진"
```

### 대화형 모드

```bash
python scripts/query_knowledge.py knowledge.ttl --interactive
```

### 커스텀 SPARQL

```bash
python scripts/query_knowledge.py knowledge.ttl --query "
  SELECT ?name WHERE { ?p a :Person ; :name ?name }
"
```

## 스키마 (references/schema.ttl)

| 클래스 | 설명 |
|-------|-----|
| :Person | 인물 |
| :Project | 프로젝트 |
| :Meeting | 미팅/대화/로그 |
| :Organization | 소속 조직 |
| :Topic | 대화 주제 |

| 관계 | 도메인 → 레인지 |
|-----|---------------|
| :participant | Meeting → Person |
| :affiliatedWith | Person → Organization |
| :involvedIn | Person → Project |
| :relatedTo | Meeting → Project |
| :hasTopic | Meeting → Topic |
| :knows | Person → Person |

| 속성 | 타입 |
|-----|-----|
| :name | string |
| :date | date |
| :summary | string |
| :filePath | string |
| :tag | string |

## 의존성

```bash
pip install rdflib pyyaml
```

## 예시 질의 패턴

**"신동순과 2024년에 나눈 대화"**
```sparql
SELECT ?date ?summary WHERE {
  ?p :name ?n . FILTER(CONTAINS(?n, "신동순"))
  ?m :participant ?p ; :date ?d ; :summary ?summary .
  FILTER(YEAR(?d) = 2024)
} ORDER BY ?d
```

**"투자 관련 미팅에 참석한 모든 인물"**
```sparql
SELECT DISTINCT ?name WHERE {
  ?m :hasTopic ?t . ?t :name ?tn .
  FILTER(CONTAINS(LCASE(?tn), "투자"))
  ?m :participant ?p . ?p :name ?name .
}
```
