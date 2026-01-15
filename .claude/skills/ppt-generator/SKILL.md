---
name: ppt-generator
description: >
  한국어에 최적화된 미니멀 프레젠테이션 생성.
  "PPT 만들어줘", "발표자료 생성", "프레젠테이션 제작" 요청 시 사용.
  python-pptx 기반, Pretendard/Noto Serif KR 폰트, 3가지 컬러 팔레트(Sage/Mono/Navy),
  7가지 레이아웃 패턴 제공. 미니멀하고 고급스러운 디자인 스타일.
---

# PPT Generator - 한국어 프레젠테이션 생성 스킬

한국어 프레젠테이션을 위한 미니멀 디자인 시스템 기반 PPTX 생성 스킬입니다.

## 사용 시점

- "PPT 만들어줘"
- "발표자료 생성해줘"
- "프레젠테이션 제작해줘"
- "슬라이드 만들어줘"
- "강의자료 만들어줘"

## 핵심 특징

- **한국어 최적화**: Pretendard(본문) + Noto Serif KR(제목) 폰트
- **3가지 팔레트**: Sage(기본), Mono, Navy
- **7가지 레이아웃**: Cover, Section, Stats Grid, Two Column, Three Column, Image+Text, Closing
- **python-pptx 기반**: 순수 Python으로 PPTX 파일 직접 생성

## 워크플로우

### 1단계: 슬라이드 구조 설계

사용자 입력을 바탕으로 슬라이드 구조를 먼저 설계합니다.

**필수 정보:**
- 주제: 발표의 핵심 주제
- 대상: 청중
- 목표: 유도하고 싶은 행동
- 슬라이드 수: 전체 개수

**설계 원칙:**
- 초반 30%: 문제 인식 및 공감
- 중반 40%: 구조 제안 및 관점 정리
- 후반 30%: 제안 및 전환 유도

### 2단계: 팔레트 선택

| 팔레트 | 분위기 | 적합한 주제 |
|--------|--------|-------------|
| Sage | 차분, 자연스러움 | 웰빙, 라이프스타일, ESG |
| Mono | 세련, 프로페셔널 | 테크, 포트폴리오, 스타트업 |
| Navy | 신뢰, 안정 | 금융, 컨설팅, 기업 |

상세 컬러값: [`references/color-palettes.md`](references/color-palettes.md)

### 3단계: 슬라이드 구성

7가지 레이아웃 중 선택:

1. **Cover** - 표지
2. **Section** - 섹션 구분 (다크 배경)
3. **Stats Grid** - 숫자/통계 강조
4. **Two Column** - 비교/대조
5. **Three Column** - 기능 나열
6. **Image + Text** - 스토리텔링
7. **Closing** - 마무리

레이아웃 상세: [`references/layouts.md`](references/layouts.md)

### 4단계: PPTX 생성

```bash
source /Users/inkeun/projects/obsidian/.venv/bin/activate && \
  python /Users/inkeun/projects/obsidian/.claude/skills/ppt-generator/scripts/generate_pptx.py \
    --config slides.json \
    --output output.pptx \
    --palette sage
```

## 환경 설정

루트 venv에 의존성 설치:
```bash
source /Users/inkeun/projects/obsidian/.venv/bin/activate
pip install python-pptx Pillow
```

## 사용 방법

### JSON 설정 파일 형식

```json
{
  "title": "발표 제목",
  "author": "발표자",
  "palette": "sage",
  "slides": [
    {
      "layout": "cover",
      "title": "발표 제목",
      "subtitle": "부제목",
      "author": "발표자",
      "date": "2026.01.13"
    },
    {
      "layout": "section",
      "badge": "SECTION 1",
      "title": "첫 번째 섹션"
    },
    {
      "layout": "stats_grid",
      "title": "핵심 지표",
      "stats": [
        {"number": "2.5억", "label": "월간 활성 사용자"},
        {"number": "150+", "label": "제휴 기업"},
        {"number": "99.9%", "label": "서비스 가동률"}
      ]
    },
    {
      "layout": "two_column",
      "title": "비교 분석",
      "left": {"heading": "AS-IS", "items": ["현재 상태 1", "현재 상태 2"]},
      "right": {"heading": "TO-BE", "items": ["목표 상태 1", "목표 상태 2"]}
    },
    {
      "layout": "three_column",
      "title": "핵심 기능",
      "columns": [
        {"heading": "기능 A", "description": "설명 A"},
        {"heading": "기능 B", "description": "설명 B"},
        {"heading": "기능 C", "description": "설명 C"}
      ]
    },
    {
      "layout": "image_text",
      "title": "스토리텔링",
      "image_path": "/path/to/image.png",
      "text": "이미지와 함께하는 설명 텍스트"
    },
    {
      "layout": "closing",
      "title": "감사합니다",
      "contact": "email@example.com"
    }
  ]
}
```

### CLI 옵션

- `--config`: JSON 설정 파일 경로 (필수)
- `--output`: 출력 PPTX 파일 경로 (기본: output.pptx)
- `--palette`: 컬러 팔레트 (sage/mono/navy, 기본: sage)

## 타이포그래피

| 요소 | 크기 | 폰트 |
|------|------|------|
| 메인 제목 | 44pt | Noto Serif KR Bold |
| 섹션 제목 | 36pt | Noto Serif KR Bold |
| 슬라이드 제목 | 32pt | Noto Serif KR Bold |
| 본문 | 16pt | Pretendard Regular |
| 레이블/캡션 | 14pt | Pretendard Medium |
| 각주 | 10pt | Pretendard Regular |

상세 가이드: [`references/typography.md`](references/typography.md)

## 출력 경로

생성된 PPTX 파일은 기본적으로 현재 디렉토리에 저장됩니다.
사용자가 특정 경로를 지정하지 않으면 `~/Downloads/` 폴더에 저장하는 것을 권장합니다.

## 예시: 5장짜리 발표자료 구성

```
1. Cover - 발표 제목, 발표자
2. Section - "01 현황 분석"
3. Stats Grid - 핵심 지표 3-4개
4. Two Column - 문제점 vs 해결방안
5. Closing - 감사합니다 + 연락처
```

## 주의사항

- 한 슬라이드에 텍스트 과다 배치 금지 - 여백 충분히 확보
- 각 슬라이드는 **하나의 핵심 메시지**만 전달
- 제목은 설명이 아닌 **메시지를 전달하는 단정형 문장**으로 작성
- 폰트가 설치되지 않은 경우 시스템 기본 폰트로 대체됨

## 설계 규칙 (슬라이드 구조)

1. 슬라이드는 요청된 개수로만 구성
2. 각 슬라이드는 하나의 핵심 메시지만 가짐
3. 제목은 메시지를 전달하는 단정형 문장으로 작성
4. 추상적인 표현 사용 금지
5. 문장은 짧고 명확하게 작성

## 검증 기준

- 제목만 읽어도 전체 흐름이 이해되는가
- 슬라이드만 훑어봐도 메시지가 전달되는가
- 초반 30%에서 문제 인식이 충분히 이루어졌는가
