---
name: keep-sync
description: Google Keep 메모를 가져와서 Obsidian으로 동기화하는 스킬. Keep API를 통해 메모 목록 조회, 개별 메모 가져오기, Obsidian 마크다운으로 변환.
version: 1.0.0
author: 서인근
tags:
  - 구글킵
  - Google Keep
  - 메모
  - 동기화
skill_type: managed
---

# keep-sync

Google Keep 메모를 Obsidian으로 동기화하는 스킬입니다.

## 개요

Google Keep API를 통해 메모를 가져와서 Obsidian 마크다운 파일로 변환합니다.

**동기화 방향**: Google Keep → Obsidian (단방향)

## 사용 시점

다음과 같은 요청이 있을 때 이 스킬을 사용하세요:

1. **"킵 메모 가져와줘"**
2. **"구글 킵 동기화"**
3. **"Keep 메모 목록"**
4. **"킵에서 메모 불러와줘"**

## 실행 명령어

```bash
# 메모 목록 조회
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/keep-sync/scripts/fetch_notes.py --list

# 모든 메모 가져오기
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/keep-sync/scripts/fetch_notes.py --fetch-all

# 특정 메모 가져오기
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/keep-sync/scripts/fetch_notes.py --note-id "notes/xxxxx"
```

## 환경변수 (`.env`)

```bash
GOOGLE_CREDENTIALS_PATH=/path/to/vault/.creds/crawler-hrm.json
```

## 의존성

- Python 3.10+
- google-auth (`pip install google-auth`)
- google-api-python-client (`pip install google-api-python-client`)

## 주요 파일

| 파일 | 설명 |
|------|------|
| `scripts/fetch_notes.py` | 메인 스크립트 - Keep API 호출 |
| `google_api/keep.py` | Google Keep API Manager |
| `SKILL.md` | 스킬 메타데이터 |

## API 엔드포인트

- `GET /v1/notes` - 메모 목록
- `GET /v1/{name=notes/*}` - 특정 메모 가져오기
- `POST /v1/notes` - 메모 생성
- `DELETE /v1/{name=notes/*}` - 메모 삭제

## 주의사항

1. **Google Workspace 필요**: Keep API는 엔터프라이즈 환경용. 일반 Gmail 계정으로는 403 에러 발생 가능.
2. **서비스 계정 제한**: 서비스 계정으로 Keep API 접근 시 도메인 전체 위임(domain-wide delegation) 필요할 수 있음.
3. **OAuth 대안**: 서비스 계정이 안 되면 OAuth 2.0 사용자 인증으로 전환 필요.

## 관련 문서

- [Google Keep API Reference](https://developers.google.com/workspace/keep/api/reference/rest?hl=ko)
- CLAUDE.md: 프로젝트 전체 가이드
