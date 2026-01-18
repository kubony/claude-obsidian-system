---
name: ontology-query
description: TTL 온톨로지에 SPARQL 질의를 수행하는 스킬. 인물, 프로젝트, 미팅 정보를 검색하고 knowledge-orchestrator가 호출.
---

# Ontology Query

knowledge.ttl 파일에 SPARQL 질의를 수행합니다.

## 역할

- TTL 파일 로드 및 SPARQL 쿼리 실행
- 17개 프리셋 쿼리 제공
- 커스텀 SPARQL 쿼리 지원

## 실행 방법

```bash
cd /path/to/vault/.claude/skills/ontology-query && \
source /path/to/vault/.claude/skills/ontology-engine/.venv/bin/activate && \
python scripts/query_knowledge.py /path/to/vault/.claude/skills/ontology-engine/knowledge.ttl \
  --preset <preset_name> --param "<parameter>"
```

## 프리셋 쿼리

### 인물 관련
| 프리셋 | 설명 | 파라미터 |
|--------|------|----------|
| `all_persons` | 모든 인물 목록 | - |
| `person_meetings` | 특정 인물과의 미팅 | 인물명 |
| `person_topics` | 특정 인물과 논의한 주제 | 인물명 |
| `person_network` | 특정 인물이 아는 사람들 | 인물명 |
| `person_projects` | 특정 인물이 참여한 프로젝트 | 인물명 |
| `org_members` | 특정 조직 소속 인물 | 조직명 |

### 프로젝트 관련
| 프리셋 | 설명 | 파라미터 |
|--------|------|----------|
| `all_projects` | 모든 프로젝트 목록 | - |
| `active_projects` | 활성 프로젝트 | - |
| `archived_projects` | 아카이브된 프로젝트 | - |
| `project_details` | 특정 프로젝트 상세 | 프로젝트명 |
| `project_meetings` | 특정 프로젝트의 미팅 | 프로젝트명 |
| `project_participants` | 프로젝트 참여 인물 | 프로젝트명 |
| `search_projects` | 프로젝트 키워드 검색 | 키워드 |

### 미팅/기타
| 프리셋 | 설명 | 파라미터 |
|--------|------|----------|
| `recent_meetings` | 최근 미팅 10개 | - |
| `meetings_by_date` | 특정 기간 미팅 | YYYY-MM |
| `search_keyword` | 키워드로 미팅 검색 | 키워드 |
| `stats` | 전체 통계 | - |

## 사용 예시

```bash
# 모든 인물 조회
python scripts/query_knowledge.py knowledge.ttl --preset all_persons

# 특정 인물과의 미팅 조회
python scripts/query_knowledge.py knowledge.ttl --preset person_meetings --param "홍길동"

# 앤틀러 소속 인물 조회
python scripts/query_knowledge.py knowledge.ttl --preset org_members --param "앤틀러"

# 커스텀 SPARQL 쿼리
python scripts/query_knowledge.py knowledge.ttl --query "SELECT ?name WHERE { ?p a :Person ; :name ?name }"
```

## 의존성

- **venv**: ontology-engine의 .venv 공유 사용
- **패키지**: rdflib
- **입력**: knowledge.ttl (ontology-sync가 생성)

## 사용 주체

- **knowledge-orchestrator**: 사용자 질의를 프리셋으로 라우팅
- **수동 실행**: 직접 SPARQL 쿼리 필요 시
