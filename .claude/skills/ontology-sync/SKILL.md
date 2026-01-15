---
name: ontology-sync
description: Obsidian 볼트를 RDF/TTL 온톨로지로 변환하는 스킬. 인물사전, 프로젝트, 미팅 정보를 추출하여 knowledge.ttl 파일 생성. vault-organizer의 정리 작업 후 자동 호출되어 지식 베이스 동기화.
---

# Ontology Sync

Obsidian 볼트의 마크다운 파일을 RDF/TTL 온톨로지로 변환합니다.

## 역할

- 인물사전(04_Networking/00_인물사전/) → Person 엔티티
- 프로젝트(00_A_Projects/, 90_Archives/) → Project 엔티티
- 미팅/대화 기록 → Meeting 엔티티
- 위키링크 → 관계(knows, involvedIn)

## 실행 방법

```bash
cd /Users/inkeun/projects/obsidian/.claude/skills/ontology-sync && \
source /Users/inkeun/projects/obsidian/.claude/skills/ontology-engine/.venv/bin/activate && \
python scripts/vault_to_ttl.py /Users/inkeun/projects/obsidian \
  --output /Users/inkeun/projects/obsidian/.claude/skills/ontology-engine/knowledge.ttl
```

## 출력

| 항목 | 설명 |
|------|------|
| `knowledge.ttl` | RDF 트리플 파일 (Turtle 형식) |

## 변환 대상

### 소스 폴더
- `04_Networking/00_인물사전/*.md` → Person
- `00_A_Projects/Active/`, `00_A_Projects/Planning/` → Project (활성)
- `90_Archives/` → Project (아카이브)

### 추출 정보
- **Person**: 파일명, YAML(title, tags, summary), 소속(_소속.md)
- **Project**: 폴더명(YYMM 프로젝트명), 태그, 요약
- **Meeting**: `## YYYY.MM.DD` 섹션 → 날짜 + 내용
- **Organization**: 파일명의 `_소속` 부분
- **Topic**: 미팅 내용의 해시태그 및 키워드
- **관계**: `[[위키링크]]` → knows/involvedIn 관계

## 스키마 클래스

| 클래스 | 설명 |
|--------|------|
| `:Person` | 인물 |
| `:Project` | 프로젝트 |
| `:Meeting` | 미팅/대화/로그 |
| `:Organization` | 소속 조직 |
| `:Topic` | 대화 주제 |

## 스키마 관계

| 관계 | 도메인 → 레인지 |
|------|-----------------|
| `:participant` | Meeting → Person |
| `:affiliatedWith` | Person → Organization |
| `:involvedIn` | Person → Project |
| `:relatedTo` | Meeting → Project |
| `:hasTopic` | Meeting → Topic |
| `:knows` | Person → Person |

## 의존성

- **venv**: ontology-engine의 .venv 공유 사용
- **패키지**: rdflib, pyyaml

## 사용 주체

- **vault-organizer**: 볼트 정리 완료 후 Phase 5에서 호출
- **수동 실행**: TTL 갱신이 필요할 때
