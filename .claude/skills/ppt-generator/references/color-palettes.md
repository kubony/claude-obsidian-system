# Color Palettes - 컬러 팔레트 레퍼런스

## Sage (기본)

차분하고 자연스러운 분위기. 웰빙, 라이프스타일, ESG 관련 발표에 적합.

| 용도 | 변수명 | HEX | 설명 |
|------|--------|-----|------|
| 배경 | surface | #f5f5f0 | 따뜻한 오프화이트 |
| 텍스트 | surface_foreground | #1a1a1a | 거의 검정 |
| 주요색 | primary | #b8c4b8 | 세이지 그린 |
| 강조색 | accent | #2d2d2d | 다크 그레이 |
| 보조배경 | muted | #e8e8e3 | 밝은 베이지 |
| 보조텍스트 | muted_foreground | #666666 | 중간 그레이 |
| 다크배경 | dark_bg | #2d2d2d | 섹션용 다크 |
| 다크텍스트 | dark_fg | #f5f5f0 | 다크배경 위 텍스트 |

---

## Mono

세련되고 프로페셔널한 분위기. 테크, 포트폴리오, 스타트업 발표에 적합.

| 용도 | 변수명 | HEX | 설명 |
|------|--------|-----|------|
| 배경 | surface | #ffffff | 순백색 |
| 텍스트 | surface_foreground | #111111 | 거의 검정 |
| 주요색 | primary | #f0f0f0 | 밝은 그레이 |
| 강조색 | accent | #111111 | 진한 검정 |
| 보조배경 | muted | #f5f5f5 | 아주 밝은 그레이 |
| 보조텍스트 | muted_foreground | #666666 | 중간 그레이 |
| 다크배경 | dark_bg | #111111 | 섹션용 다크 |
| 다크텍스트 | dark_fg | #ffffff | 다크배경 위 텍스트 |

---

## Navy

신뢰감과 안정감. 금융, 컨설팅, 기업 발표에 적합.

| 용도 | 변수명 | HEX | 설명 |
|------|--------|-----|------|
| 배경 | surface | #f8f9fc | 차가운 화이트 |
| 텍스트 | surface_foreground | #1a1f36 | 네이비 다크 |
| 주요색 | primary | #dce3f0 | 밝은 네이비블루 |
| 강조색 | accent | #1a1f36 | 네이비 |
| 보조배경 | muted | #eef1f6 | 밝은 블루그레이 |
| 보조텍스트 | muted_foreground | #5c6478 | 중간 블루그레이 |
| 다크배경 | dark_bg | #1a1f36 | 섹션용 네이비 |
| 다크텍스트 | dark_fg | #f8f9fc | 다크배경 위 텍스트 |

---

## 팔레트 선택 가이드

| 상황 | 권장 팔레트 |
|------|-------------|
| 스타트업 피칭 | Mono |
| IR 자료 | Navy |
| 브랜드/마케팅 | Sage |
| 기술 발표 | Mono |
| 컨설팅 제안서 | Navy |
| 교육/강의 | Sage |
| 포트폴리오 | Mono |
| ESG/지속가능성 | Sage |

---

## CSS 변수 형식 (참고용)

```css
/* Sage */
:root {
  --color-surface: #f5f5f0;
  --color-surface-foreground: #1a1a1a;
  --color-primary: #b8c4b8;
  --color-accent: #2d2d2d;
  --color-muted: #e8e8e3;
  --color-muted-foreground: #666666;
}

/* Mono */
:root {
  --color-surface: #ffffff;
  --color-surface-foreground: #111111;
  --color-primary: #f0f0f0;
  --color-accent: #111111;
  --color-muted: #f5f5f5;
  --color-muted-foreground: #666666;
}

/* Navy */
:root {
  --color-surface: #f8f9fc;
  --color-surface-foreground: #1a1f36;
  --color-primary: #dce3f0;
  --color-accent: #1a1f36;
  --color-muted: #eef1f6;
  --color-muted-foreground: #5c6478;
}
```
