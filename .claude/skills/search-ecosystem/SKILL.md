---
name: search-ecosystem
description: Claude Code 에코시스템에서 스킬/에이전트/커맨드를 통합 검색. 로컬 설치된 항목과 Plugin Marketplace 결과를 함께 표시하여 중복 개발 방지.
trigger: "/search-ecosystem [검색어]", "스킬 찾아줘", "비슷한 에이전트 있어?"
tools:
  - Glob
  - Grep
  - Read
  - WebSearch
  - Bash
model: sonnet
---

# Claude Code 에코시스템 검색 스킬

Claude Code의 로컬 스킬/에이전트/커맨드와 Plugin Marketplace를 통합 검색하여, 중복 개발을 방지하고 기존 솔루션을 빠르게 발견합니다.

## 목적

- **중복 방지**: 새 스킬 작성 전 기존 솔루션 확인
- **시간 절약**: 25,000+ 커뮤니티 스킬 활용
- **통합 검색**: 로컬 + 전역 + Marketplace를 한 번에

## 사용 시점

1. "스킬 찾아줘", "비슷한 에이전트 있어?"
2. 새 스킬/에이전트 개발 전 기존 솔루션 확인
3. 특정 기능 구현 방법 탐색

## 워크플로우

### Phase 1: 로컬 검색

1. **프로젝트 로컬 (.claude/)**
   ```bash
   # 스킬 검색
   find .claude/skills -name "SKILL.md" -type f
   grep -r "검색어" .claude/skills/*/SKILL.md

   # 에이전트 검색
   grep -r "검색어" .claude/agents/*.md

   # 커맨드 검색
   grep -r "검색어" .claude/commands/*.md
   ```

2. **전역 (~/.claude/)**
   ```bash
   find ~/.claude/skills -name "SKILL.md" -type f 2>/dev/null
   grep -r "검색어" ~/.claude/skills/*/SKILL.md 2>/dev/null
   grep -r "검색어" ~/.claude/agents/*.md 2>/dev/null
   grep -r "검색어" ~/.claude/commands/*.md 2>/dev/null
   ```

3. **공유 저장소 (~/projects/claudesystem/.claude/)**
   ```bash
   find ~/projects/claudesystem/.claude/skills -name "SKILL.md" -type f 2>/dev/null
   grep -r "검색어" ~/projects/claudesystem/.claude/skills/*/SKILL.md 2>/dev/null
   ```

### Phase 2: Plugin Marketplace 웹 검색

1. **SkillsMP 검색**
   ```
   WebSearch: "site:skillsmp.com {검색어}"
   ```

2. **GitHub 검색**
   ```
   WebSearch: "claude-code-skill {검색어} site:github.com"
   WebSearch: "claude-code-plugin {검색어} site:github.com"
   ```

3. **커뮤니티 마켓플레이스**
   ```
   WebSearch: "{검색어} claude code marketplace"
   ```

### Phase 3: 결과 통합 및 출력

**출력 형식:**
```markdown
# 🔍 Claude Code 에코시스템 검색 결과: "{검색어}"

## 📦 로컬 설치됨 (N개)

### 프로젝트 로컬 (.claude/)
- **스킬명** (스킬 | 에이전트 | 커맨드)
  - 설명: [description]
  - 트리거: [trigger]
  - 경로: [파일 경로]

### 전역 (~/.claude/)
- ...

### 공유 저장소 (~/projects/claudesystem/.claude/)
- ...

## 🌐 Plugin Marketplace (N개)

### SkillsMP
- **스킬명**
  - 설명: [요약]
  - 링크: [URL]
  - 설치: `/plugin install [name]`

### GitHub
- **저장소명**
  - 설명: [README 요약]
  - 링크: [URL]
  - 설치: `/plugin marketplace add [owner/repo]`

## 💡 추천

### 사용 가능
[이미 설치된 항목 중 관련성 높은 것]

### 설치 추천
[Marketplace에서 관련성 높은 것]

### 새로 개발 필요
[기존 솔루션이 없는 경우]
```

## 검색 전략

### 키워드 확장
- 동의어 고려: "녹음" → "recording", "transcribe", "audio"
- 관련 키워드: "PDF" → "document", "ocr", "extract"

### 관련성 점수
1. **높음**: 이름/설명에 검색어 포함
2. **중간**: 도구/트리거에 검색어 포함
3. **낮음**: 본문에만 검색어 포함

### 필터링
- 중복 제거 (같은 스킬이 여러 위치에 있는 경우)
- 관련성 낮은 결과 제외

## 예시

### 사용자 요청
"PDF 텍스트 추출하는 스킬 찾아줘"

### 검색 수행
1. 로컬 검색: "pdf", "extract", "text"
2. Marketplace 검색: "pdf extract claude code"
3. 결과 통합

### 출력
```markdown
# 🔍 Claude Code 에코시스템 검색 결과: "PDF 텍스트 추출"

## 📦 로컬 설치됨 (1개)

### 프로젝트 로컬 (.claude/)
- **document-ocr** (스킬)
  - 설명: Gemini 3 Pro Vision API → PDF/이미지 OCR, 수기메모 지원
  - 트리거: document-processor 에이전트에서 호출
  - 경로: .claude/skills/document-ocr/SKILL.md

## 🌐 Plugin Marketplace (3개)

### SkillsMP
- **pdf-extractor**
  - 설명: Extract text from PDF files using pdfplumber
  - 링크: https://skillsmp.com/skills/pdf-extractor
  - 설치: `/plugin install pdf-extractor`

- **document-parser**
  - 설명: Parse various document formats (PDF, DOCX, TXT)
  - 링크: https://skillsmp.com/skills/document-parser
  - 설치: `/plugin install document-parser`

### GitHub
- **claude-pdf-tools**
  - 설명: Comprehensive PDF manipulation toolkit
  - 링크: https://github.com/example/claude-pdf-tools
  - 설치: `/plugin marketplace add example/claude-pdf-tools`

## 💡 추천

### 사용 가능
✅ **document-ocr** (이미 설치됨)
- OCR 기능 포함, 수기 메모도 지원
- Gemini Vision API 사용

### 설치 추천
⭐ **pdf-extractor** (SkillsMP)
- 단순 텍스트 추출에 특화
- pdfplumber 기반, 빠르고 가벼움

### 새로 개발 필요
❌ 기존 솔루션으로 충분합니다.
```

## 제한사항

- WebSearch 결과의 정확도는 검색 엔진 성능에 의존
- Marketplace 결과는 최신 정보가 아닐 수 있음
- 설치 전 스킬 상세 정보 확인 필요

## 향후 개선

1. **Python 스크립트 구현**: 더 정교한 검색 및 점수 계산
2. **캐싱**: 자주 검색하는 키워드 결과 저장
3. **자동 설치 제안**: AskUserQuestion으로 설치 여부 확인
4. **의존성 확인**: 스킬 설치 전 의존성 체크

## 사용 예시

```bash
# 사용자 요청
"녹음 파일 처리하는 스킬 있어?"

# Claude의 응답
"/search-ecosystem 스킬을 사용하여 검색하겠습니다."

# 검색 수행
1. 로컬: "recording", "audio", "transcribe"
2. Marketplace: "audio transcription claude code"
3. 결과 통합 및 출력

# 사용자가 설치 결정
"/plugin install whisper-transcriber"
```

## 관련 문서

- CLAUDE.md: "확장 관리 및 마켓플레이스" 섹션
- 00_Inbox/claude-code-plugin-marketplace-exploration.md
