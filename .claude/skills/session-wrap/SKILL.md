---
name: session-wrap
description: 세션 마무리 워크플로우 - 다중 에이전트로 문서화/자동화/학습/후속작업 분석. 사용 시점: (1) "/wrap" (2) "세션 정리해줘" (3) "오늘 작업 마무리" (4) 작업 세션 종료 시. 현재 대화 내용을 분석하여 4가지 관점에서 제안 생성.
---

# Session Wrap-up Workflow

세션 종료 시 현재 대화 내용을 분석하여 문서화, 자동화, 학습, 후속작업을 제안합니다.

## 워크플로우 개요

```
Phase 1: 4개 분석 에이전트 병렬 실행
    ├── doc-updater (문서 갱신 제안)
    ├── automation-scout (자동화 기회 탐색)
    ├── learning-extractor (학습 포인트 추출)
    └── followup-suggester (후속 작업 제안)
           ↓
Phase 2: 중복 검증 (기존 콘텐츠와 비교)
           ↓
Phase 3: 사용자 선택 → 선택된 항목 실행
```

---

## 에이전트 파일 위치

4개의 분석 에이전트는 `.claude/agents/session-wrap/`에 위치:

| 에이전트 | 파일 | 역할 |
|----------|------|------|
| doc-updater | `session-wrap/doc-updater.md` | CLAUDE.md 등 문서 갱신 제안 |
| automation-scout | `session-wrap/automation-scout.md` | 스킬/커맨드/에이전트 자동화 기회 |
| learning-extractor | `session-wrap/learning-extractor.md` | TIL 형식 학습 포인트 추출 |
| followup-suggester | `session-wrap/followup-suggester.md` | 우선순위별 후속 작업 제안 |

---

## Phase 1: 병렬 분석 (4개 Task 동시 실행)

**중요**: 4개의 Task를 **단일 메시지**에서 병렬로 호출하세요.

**subagent_type은 반드시 `general-purpose` 사용** (커스텀 타입 불가)

```
# 단일 메시지에서 4개 Task 병렬 호출

Task 1: doc-updater
- subagent_type: "general-purpose"
- description: "문서 갱신 분석"
- prompt: |
    .claude/agents/session-wrap/doc-updater.md 파일의 지침을 따라
    현재 세션 대화 내용을 분석하여 CLAUDE.md 등 문서 갱신 제안을 생성하세요.

Task 2: automation-scout
- subagent_type: "general-purpose"
- description: "자동화 기회 탐색"
- prompt: |
    .claude/agents/session-wrap/automation-scout.md 파일의 지침을 따라
    현재 세션에서 자동화할 수 있는 패턴을 탐색하세요.

Task 3: learning-extractor
- subagent_type: "general-purpose"
- description: "학습 포인트 추출"
- prompt: |
    .claude/agents/session-wrap/learning-extractor.md 파일의 지침을 따라
    현재 세션에서 배운 내용을 TIL 형식으로 추출하세요.

Task 4: followup-suggester
- subagent_type: "general-purpose"
- description: "후속 작업 제안"
- prompt: |
    .claude/agents/session-wrap/followup-suggester.md 파일의 지침을 따라
    현재 세션에서 미완료된 작업과 후속 작업을 분석하세요.
```

**참고**:
- 각 에이전트는 현재 대화 컨텍스트에 접근 가능
- 에이전트 파일을 Read 도구로 읽어서 지침 확인 가능
- general-purpose는 모든 도구(Read, Glob, Grep, Bash 등) 사용 가능

---

## Phase 2: 중복 검증

4개 에이전트 결과를 수집한 후, 기존 콘텐츠와 비교하여 중복 제거:

1. **CLAUDE.md** 읽기 → doc-updater 제안과 비교
2. **.claude/skills/** 목록 확인 → automation-scout 제안과 비교
3. **기존 TIL** 확인 → learning-extractor 제안과 비교
4. **기존 TODO** 확인 → followup-suggester 제안과 비교

중복 항목은 제외하고 새로운 제안만 유지.

---

## Phase 3: 사용자 선택 및 실행

### 3.1 제안 요약 제시

```markdown
# 세션 마무리 분석 결과

## 📝 문서 갱신 (N개 제안)
[doc-updater 결과 요약]

## 🤖 자동화 기회 (N개 제안)
[automation-scout 결과 요약]

## 💡 학습 포인트 (N개 항목)
[learning-extractor 결과 요약]

## ✅ 후속 작업 (N개 항목)
[followup-suggester 결과 요약]
```

### 3.2 사용자 선택 받기

AskUserQuestion 도구로 선택지 제공:

```
질문: "어떤 항목을 실행하시겠습니까?"
옵션:
1. 전체 실행 (모든 제안 적용)
2. 선택 실행 (항목별 선택)
3. 문서만 업데이트
4. 학습 포인트만 저장
5. 나중에 (아무것도 실행 안함)
```

### 3.3 선택된 항목 실행

- **문서 갱신**: Edit 도구로 해당 파일 수정
- **자동화**: skill-creator 또는 slash-command-creator 스킬 호출
- **학습 포인트**: `00_Inbox/TIL_YYYYMMDD.md` 파일로 저장
- **후속 작업**: `00_Inbox/TODO_YYYYMMDD.md` 또는 기존 TODO에 추가

---

## 빠른 커밋 모드

`/wrap [커밋 메시지]` 형태로 호출 시:

1. 제공된 메시지로 git commit & push (git-commit-push 스킬 사용)
2. 간략 분석만 수행 (전체 병렬 분석 생략)
3. 결과 요약 출력

```bash
# 예시
/wrap 오늘 작업 완료
# → git commit -m "오늘 작업 완료" && git push
# → 간략 세션 요약 출력
```

---

## 출력 저장 위치

| 항목 | 저장 위치 |
|------|----------|
| 문서 갱신 | 해당 파일 직접 수정 |
| 자동화 제안 | `.claude/skills/` 또는 `.claude/commands/` |
| 학습 포인트 | `00_Inbox/TIL_YYYYMMDD.md` |
| 후속 작업 | `00_Inbox/TODO_YYYYMMDD.md` |

---

## 주의사항

1. **컨텍스트 의존**: 현재 대화 내용을 분석하므로 세션 중간에 호출해도 됨
2. **병렬 실행 필수**: Phase 1의 4개 에이전트는 반드시 단일 메시지에서 병렬 호출
3. **사용자 확인**: 실제 파일 수정 전 항상 사용자 승인 필요
4. **Git 커밋**: 문서 갱신 후 자동 커밋하지 않음 (별도 요청 필요)
