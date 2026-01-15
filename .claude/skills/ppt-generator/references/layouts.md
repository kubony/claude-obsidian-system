# Layouts - 레이아웃 레퍼런스

7가지 기본 레이아웃 패턴과 사용법.

---

## 1. Cover (표지)

발표의 첫 슬라이드. 제목, 부제목, 발표자 정보 포함.

### JSON 구조

```json
{
  "layout": "cover",
  "title": "발표 제목",
  "subtitle": "부제목 (선택)",
  "author": "발표자",
  "date": "2026.01.13"
}
```

### 사용 시점

- 발표 시작
- 가장 중요한 메시지를 한 줄로 전달

### 디자인 특징

- 중앙 정렬
- 제목은 가장 큰 폰트 (44pt)
- 여백을 충분히 확보

---

## 2. Section (섹션 구분)

발표의 큰 흐름을 구분하는 슬라이드. 다크 배경 사용.

### JSON 구조

```json
{
  "layout": "section",
  "badge": "SECTION 1",
  "title": "현황 분석"
}
```

### 사용 시점

- 주제 전환점
- 3-4개 섹션으로 발표 구조화
- 청중에게 진행 상황 안내

### 디자인 특징

- 다크 배경 (palette.dark_bg)
- 배지로 섹션 번호 표시
- 제목만 크게 중앙 배치

---

## 3. Stats Grid (통계 그리드)

숫자와 통계를 강조하는 슬라이드. 최대 4개 지표.

### JSON 구조

```json
{
  "layout": "stats_grid",
  "title": "핵심 지표",
  "stats": [
    {"number": "2.5억", "label": "월간 활성 사용자"},
    {"number": "150+", "label": "제휴 기업"},
    {"number": "99.9%", "label": "서비스 가동률"}
  ]
}
```

### 사용 시점

- 성과 발표
- KPI 요약
- 임팩트 강조

### 디자인 특징

- 숫자는 크고 굵게 (48pt)
- 레이블은 작게 (14pt)
- 가로로 균등 분할

---

## 4. Two Column (2단 비교)

두 가지를 비교하거나 대조하는 슬라이드.

### JSON 구조

```json
{
  "layout": "two_column",
  "title": "비교 분석",
  "left": {
    "heading": "AS-IS",
    "items": ["현재 상태 1", "현재 상태 2", "현재 상태 3"]
  },
  "right": {
    "heading": "TO-BE",
    "items": ["목표 상태 1", "목표 상태 2", "목표 상태 3"]
  }
}
```

### 사용 시점

- Before/After
- 문제점 vs 해결방안
- 경쟁사 비교
- 장단점 분석

### 디자인 특징

- 좌우 균등 분할
- 각 컬럼에 제목 + 불릿 리스트
- 최대 5개 항목 권장

---

## 5. Three Column (3단 컬럼)

세 가지 기능이나 요소를 나열하는 슬라이드.

### JSON 구조

```json
{
  "layout": "three_column",
  "title": "핵심 기능",
  "columns": [
    {"heading": "기능 A", "description": "기능 A에 대한 상세 설명"},
    {"heading": "기능 B", "description": "기능 B에 대한 상세 설명"},
    {"heading": "기능 C", "description": "기능 C에 대한 상세 설명"}
  ]
}
```

### 사용 시점

- 제품 기능 소개
- 서비스 구성요소
- 3단계 프로세스
- 팀 역할 분담

### 디자인 특징

- 세로로 3등분
- 각 컬럼에 제목 + 설명
- 아이콘 추가 가능 (추후)

---

## 6. Image + Text (이미지 + 텍스트)

이미지와 텍스트를 함께 보여주는 스토리텔링 슬라이드.

### JSON 구조

```json
{
  "layout": "image_text",
  "title": "스토리텔링",
  "image_path": "/path/to/image.png",
  "text": "이미지와 함께하는 설명 텍스트. 좀 더 길게 작성해도 됩니다."
}
```

### 사용 시점

- 사례 소개
- 제품 스크린샷
- 팀/인물 소개
- 비주얼 스토리텔링

### 디자인 특징

- 좌: 이미지 (5.5인치)
- 우: 텍스트 설명
- 이미지 없으면 placeholder 표시

---

## 7. Closing (마무리)

발표 마무리 슬라이드. 감사 인사와 연락처.

### JSON 구조

```json
{
  "layout": "closing",
  "title": "감사합니다",
  "contact": "email@example.com | linkedin.com/in/username"
}
```

### 사용 시점

- 발표 마무리
- Q&A 전환
- 연락처 안내

### 디자인 특징

- 중앙 정렬
- 심플한 메시지
- 연락처는 작게

---

## 8. Content (일반 콘텐츠)

위 레이아웃에 해당하지 않는 일반 슬라이드.

### JSON 구조

```json
{
  "layout": "content",
  "title": "슬라이드 제목",
  "content": "본문 내용. 여러 줄로 작성 가능."
}
```

또는 리스트 형태:

```json
{
  "layout": "content",
  "title": "슬라이드 제목",
  "content": ["항목 1", "항목 2", "항목 3"]
}
```

### 사용 시점

- 일반적인 설명 슬라이드
- 리스트 나열
- 텍스트 중심 내용

---

## 레이아웃 조합 예시

### 5장짜리 스타트업 피칭

```
1. cover - "문제를 해결하는 솔루션"
2. stats_grid - 시장 규모, 성장률
3. two_column - 기존 방식 vs 우리 방식
4. three_column - 제품 핵심 기능 3가지
5. closing - 투자 문의
```

### 10장짜리 컨설팅 제안서

```
1. cover - 프로젝트 제목
2. section - "01 현황 분석"
3. stats_grid - 문제 지표
4. two_column - 원인 vs 영향
5. section - "02 해결 방안"
6. three_column - 3단계 접근법
7. image_text - 사례 1
8. image_text - 사례 2
9. section - "03 기대 효과"
10. closing - 다음 단계 안내
```

---

## 주의사항

- 한 슬라이드 = 하나의 메시지
- 텍스트 과다 배치 금지
- 레이아웃 믹스로 시각적 리듬감 유지
- 섹션 슬라이드로 흐름 구분
