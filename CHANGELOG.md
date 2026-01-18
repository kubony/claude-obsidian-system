# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-01-19

### Added

**Agents (14개)**
- `vault-organizer` - 메인 오케스트레이터: YAML 헤더 → 인물사전 → 인박스 정리 → git → 온톨로지 동기화
- `recording-processor` - 녹음 파일 병렬 처리 (오디오 → STT → 미팅노트)
- `single-recording-processor` - 단일 녹음 파일 처리 서브에이전트
- `recording-person-updater` - 미팅노트에서 인물 정보 추출 및 업데이트
- `document-processor` - PDF/이미지 OCR 처리
- `knowledge-orchestrator` - 자연어 쿼리 → SPARQL 응답
- `person-updater` - 인물사전 업데이트 + Google 연락처 동기화
- `company-updater` - 법인사전 업데이트 + WebSearch
- `single-company-processor` - 단일 회사 정보 처리 서브에이전트
- `yaml-header-inserter` - YAML 프론트매터 일괄 추가
- `project-organizer` - Active 프로젝트 폴더 정리
- `problem-definition-analyzer` - 문제정의.md 프레임워크 생성
- `visualizer-launcher` - 에이전트-스킬 관계 D3.js 시각화

**Skills (29개)**

*Core*
- `audio-transcriber` - OpenAI Whisper STT (25MB+ 자동 분할)
- `ontology-engine` - RDF/TTL 온톨로지 엔진
- `ontology-sync` - 볼트 → TTL 동기화
- `ontology-query` - SPARQL 쿼리 (17개 프리셋)
- `document-ocr` - Gemini Vision OCR
- `meeting-summarizer` - 미팅노트 구조화

*Google Integration*
- `sheets-sync` - 인물사전 → 구글시트 CRM (17개 필드)
- `company-sheets-sync` - 법인사전 → 구글시트 (13개 필드)
- `google-contact-sync` - Google Contacts CSV → 인물사전
- `gmail-reader` - Gmail 검색 및 조회
- `gmail-sender` - Gmail 발송
- `calendar-list` - Google Calendar 조회
- `calendar-create` - Google Calendar 일정 생성
- `calendar-sync` - 캘린더 동기화
- `keep-sync` - Google Keep 동기화

*Utilities*
- `git-commit-push` - Git 자동 커밋/푸시
- `recent-files-finder` - 최근 수정 파일 탐색
- `yaml-header-finder` - YAML 누락 파일 탐색
- `company-extractor` - 인물사전에서 회사 목록 추출
- `contact-matcher` - 연락처 매칭 분석
- `last-contact-updater` - 최근 연락일 업데이트

*Development*
- `skill-creator` - 새 스킬 생성 가이드
- `subagent-creator` - 새 서브에이전트 생성 가이드
- `slash-command-creator` - 슬래시 커맨드 생성 가이드
- `hook-creator` - Hook 설정 가이드

*Analysis*
- `session-analyzer` - 세션 실행 검증
- `history-insight` - 세션 히스토리 분석
- `agent-skill-visualizer` - 구조 시각화

*Content*
- `ppt-generator` - 한국어 최적화 PPTX 생성

### Architecture

- **멀티 에이전트 병렬 처리**: Task 도구로 서브에이전트 병렬 호출
- **RDF/SPARQL 온톨로지**: 자연어 → 시맨틱 쿼리
- **PARA 방법론**: Projects/Areas/Resources/Archives 폴더 구조
- **ID 기반 증분 동기화**: 구글시트 CRM 필터/정렬 유지

### Notes

- 모든 경로는 플레이스홀더로 제공 (`/path/to/vault`, `/path/to/recordings`)
- API 키는 `.env` 파일에서 환경변수로 관리
- Python 3.10+, ffmpeg, Claude Code CLI 필요
