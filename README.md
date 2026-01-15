# Claude Code Obsidian System

Claude Code 기반 Obsidian 볼트 자동화 시스템입니다.

## 개요

- **14개 커스텀 에이전트** - 볼트 정리, 녹음 처리, 지식 쿼리 등
- **31개 커스텀 스킬** - STT, OCR, 온톨로지, CRM 동기화 등
- **RDF/TTL 온톨로지 엔진** - 시맨틱 쿼리 지원
- **병렬 처리 아키텍처** - 다중 파일 동시 처리

## 설치

### 1. 볼트 루트에 복사

```bash
# Obsidian 볼트로 이동
cd /path/to/your/obsidian-vault

# .claude 폴더 복사
cp -r /path/to/claude-obsidian-system/.claude .
```

### 2. Python 가상환경 설정

```bash
# 볼트 루트에서 venv 생성
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install openai python-dotenv gspread google-auth \
  google-api-python-client pytrends lxml rdflib pyyaml \
  python-pptx Pillow
```

### 3. 환경변수 설정

루트 `.env` 파일 생성:

```bash
# OpenAI (STT용)
OPENAI_API_KEY=your-openai-api-key

# Google Sheets 동기화 (선택)
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Gemini (OCR용, 선택)
GEMINI_API_KEY=your-gemini-api-key
```

### 4. 경로 커스터마이징

파일들에 하드코딩된 경로를 본인 환경에 맞게 수정하세요:

```bash
# 일괄 치환 예시
find .claude -type f \( -name "*.md" -o -name "*.py" \) \
  -exec sed -i '' 's|/Users/inkeun/projects/obsidian|/path/to/your/vault|g' {} \;
```

**주요 경로:**
- `/Users/inkeun/projects/obsidian` → 볼트 루트
- `/Users/inkeun/Documents/00_녹음파일/` → 녹음 폴더
- `.creds/` → Google API 인증 파일

## 구조

```
.claude/
├── agents/           # 서브에이전트 정의 (14개)
│   ├── vault-organizer.md      # 메인 오케스트레이터
│   ├── recording-processor.md  # 녹음 처리
│   ├── knowledge-orchestrator.md # 지식 쿼리
│   └── ...
├── skills/           # 스킬 정의 (31개)
│   ├── audio-transcriber/      # OpenAI Whisper STT
│   ├── ontology-engine/        # RDF/SPARQL 엔진
│   ├── sheets-sync/            # 구글시트 CRM
│   └── ...
├── commands/         # 슬래시 커맨드
└── visualizer/       # 에이전트-스킬 시각화
```

## 주요 에이전트

| 에이전트 | 트리거 | 기능 |
|----------|--------|------|
| vault-organizer | "볼트 정리해줘" | YAML 헤더 추가 → 인물사전 → 인박스 정리 → git |
| recording-processor | "녹음파일 정리해줘" | 오디오 → STT → 미팅노트 |
| knowledge-orchestrator | "[인물]에 대해 알려줘" | 자연어 → SPARQL → 응답 |
| document-processor | "PDF 정리해줘" | OCR → 구조화된 노트 |

## 주요 스킬

| 스킬 | 기능 |
|------|------|
| audio-transcriber | OpenAI Whisper STT (25MB+ 자동 분할) |
| ontology-engine | 볼트 → RDF/TTL, SPARQL 쿼리 |
| meeting-summarizer | 텍스트 → 구조화된 미팅노트 |
| sheets-sync | 인물사전 → 구글시트 CRM |
| ppt-generator | 한국어 최적화 PPTX 생성 |

## 사용법

Claude Code CLI에서:

```bash
# 볼트 정리
"볼트 정리해줘"

# 녹음 처리
"녹음파일 정리해줘"

# 지식 쿼리
"김철수에 대해 알려줘"
"앤틀러 소속 인물 찾아줘"
"최근 미팅 목록"

# 세션 마무리
/wrap
```

## 볼트 구조 요구사항

이 시스템은 다음 폴더 구조를 가정합니다:

```
00_Inbox/                # 새 파일 기본 위치
00_A_Projects/Active/    # 진행중 프로젝트
04_Networking/
  └── 00_인물사전/       # 인물 파일 (*.md)
  └── 01_법인사전/       # 회사 파일 (*.md)
10_Resources/            # 지식 베이스
90_Archives/             # 완료된 프로젝트
```

## 커스터마이징

### 에이전트 추가

`.claude/agents/` 폴더에 마크다운 파일 생성:

```markdown
---
name: my-agent
description: 에이전트 설명
tools:
  - Read
  - Write
  - Bash
model: sonnet
---

# My Agent

에이전트 지침...
```

### 스킬 추가

`.claude/skills/my-skill/SKILL.md` 생성 (SKILL.md 표준 참조)

## 의존성

- Python 3.10+
- Node.js 18+ (시각화용)
- ffmpeg (오디오 분할용)
- Claude Code CLI

## 라이선스

MIT
