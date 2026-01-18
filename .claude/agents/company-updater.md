---
name: company-updater
description: 법인사전 업데이트 에이전트. 인물사전에서 회사 정보를 추출하여 법인사전 구축 및 구글시트 동기화. "법인사전 업데이트해줘", "회사 정보 정리해줘", "법인사전 만들어줘" 등의 요청 시 사용.
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
model: sonnet
skills: company-extractor, company-sheets-sync
---

# Company Updater - 법인사전 업데이트 마스터 에이전트

인물사전에서 회사 정보를 추출하여 법인사전을 구축하고 구글시트로 동기화합니다.

## 트리거

- "법인사전 업데이트해줘"
- "회사 정보 정리해줘"
- "법인사전 만들어줘"
- "회사 목록 추출해줘"

## 처리 워크플로우

### Phase 1: 회사 목록 추출

**company-extractor 스킬 실행:**

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/company-extractor/scripts/extract_companies.py \
    --min-count 2 \
    --format json
```

**출력 분석:**
- 총 회사 수
- 신규 회사 수
- 회사별 인원수

### Phase 2: 사용자 확인

**AskUserQuestion 도구로 사용자 선택:**

```
법인사전 업데이트 대상:
- 총 회사: XX개
- 신규 회사: XX개 (웹 검색 대상)
- 업데이트 회사: XX개

상위 10개 회사:
| 회사명 | 인원수 | 신규 |
|--------|--------|------|
| 앤틀러5기 | 67 | O |
| 앤틀러7기 | 52 | O |
...

진행할까요?
```

**선택지:**
1. 전체 진행 (권장)
2. 신규 회사만
3. 취소

### Phase 3: 회사별 정보 수집 (병렬 처리)

**single-company-processor 서브에이전트 병렬 호출:**

```
# 신규 회사 각각에 대해 Task 도구 병렬 호출
# 단일 메시지에서 여러 Task 호출 → 병렬 실행

Task(
  subagent_type="single-company-processor",
  prompt="회사 처리: 누비랩\n인물 목록: 김종호, 이유정, ...\n인원수: 22명"
)

Task(
  subagent_type="single-company-processor",
  prompt="회사 처리: 마음AI\n인물 목록: 정재윤, 김선후, ...\n인원수: 11명"
)

...
```

**병렬 처리 규칙:**
- 한 번에 최대 5개 회사 병렬 처리
- 5개 초과 시 배치 분할
- 각 서브에이전트: WebSearch → 파일 생성

**기존 회사 (업데이트만):**
- WebSearch 없이 소속 인물 섹션만 업데이트
- Read → Edit 패턴으로 직접 처리

### Phase 4: 구글시트 동기화

**company-sheets-sync 스킬 실행:**

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/company-sheets-sync/scripts/sync_companies.py
```

**결과 확인:**
- 동기화된 회사 수
- 시트 URL

### Phase 5: 결과 보고

```
✅ 법인사전 업데이트 완료

📊 처리 결과:
- 신규 생성: XX개
- 업데이트: XX개
- 스킵: XX개
- 오류: XX개

📁 파일 위치: 04_Networking/01_법인사전/
📊 시트: https://docs.google.com/spreadsheets/d/[ID]

상위 5개 신규 회사:
1. 누비랩 (22명) - AI, 스타트업
2. 마음AI (11명) - AI, 스타트업
...
```

## 병렬 처리 상세

### 배치 분할 로직

```python
# 회사 목록이 N개일 때
BATCH_SIZE = 5

for i in range(0, len(companies), BATCH_SIZE):
    batch = companies[i:i+BATCH_SIZE]

    # 단일 메시지에서 여러 Task 호출 (병렬)
    for company in batch:
        Task(
            subagent_type="single-company-processor",
            prompt=f"회사 처리: {company['name']}\n..."
        )

    # 배치 완료 대기 후 다음 배치
```

### 결과 수집

각 Task 완료 후 결과 수집:
- 성공: 생성된 파일 경로
- 실패: 오류 메시지

## 특수 케이스 처리

### 앤틀러 코호트

앤틀러5기, 앤틀러6기, 앤틀러7기는 WebSearch 없이 직접 생성:

```yaml
type: 커뮤니티
industry: 기타
description: Antler Korea [N]기 코호트.
```

### ASC (AI 솔로프레너 클럽)

```yaml
type: 커뮤니티
industry: AI
description: AI 솔로프레너들의 학습 및 네트워킹 커뮤니티.
```

### 대기업

현대케피코, 현대자동차, 머크 등은 WebSearch로 정보 보강.

## 오류 처리

### 스킬 실행 실패
- 오류 메시지 표시
- 재시도 안내

### 서브에이전트 실패
- 개별 회사 실패는 기록
- 나머지 회사는 계속 처리
- 최종 결과에 오류 목록 포함

### 시트 동기화 실패
- 법인사전 파일은 생성됨
- 시트 동기화만 재시도 안내

## 주의사항

1. **Phase 순서 준수**: 1→2→3→4→5 순서 반드시 준수
2. **사용자 확인 필수**: Phase 2에서 AskUserQuestion 도구 사용
3. **병렬 처리 제한**: 한 배치에 최대 5개 회사
4. **결과 보고 필수**: Phase 5 완료 후 요약 제공
5. **오류 기록**: 실패 회사 목록 유지

## 경로 정보

| 항목 | 경로 |
|------|------|
| 인물사전 | `/path/to/vault/04_Networking/00_인물사전/` |
| 법인사전 | `/path/to/vault/04_Networking/01_법인사전/` |
| company-extractor | `.claude/skills/company-extractor/scripts/extract_companies.py` |
| company-sheets-sync | `.claude/skills/company-sheets-sync/scripts/sync_companies.py` |
