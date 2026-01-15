---
description: 세션 마무리 - 문서화, 자동화, 학습, 후속작업 분석 (다중 에이전트)
---

# Session Wrap-up

현재 세션에서 대화한 내용을 분석하여 다음 4가지 관점에서 제안을 생성합니다.

## 실행 방법

Skill tool을 사용하여 `session-wrap` 스킬을 호출하세요:

```
Skill tool: session-wrap
```

## 인자 (선택사항)

`$ARGUMENTS`가 제공되면 빠른 커밋 모드로 동작:
- `/wrap` → 전체 분석 워크플로우 실행
- `/wrap 오늘 작업 완료` → 제공된 메시지로 바로 커밋 후 간략 분석

## 분석 영역 (4개 에이전트 병렬 실행)

1. **doc-updater**: CLAUDE.md 또는 프로젝트 문서에 추가할 내용
2. **automation-scout**: 스킬/커맨드/에이전트로 자동화할 패턴
3. **learning-extractor**: TIL 형식의 학습 포인트
4. **followup-suggester**: 우선순위별 후속 작업

## 출력

각 에이전트의 제안을 종합하여 사용자에게 선택지 제공:
- 어떤 제안을 실행할지 선택
- 선택된 항목만 실행
