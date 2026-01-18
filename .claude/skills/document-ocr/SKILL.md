---
name: document-ocr
description: OpenAI Vision API를 사용하여 PDF 파일과 이미지에서 텍스트를 추출합니다. 수기 메모, 스캔 문서, 사진 등에서 OCR 수행. 사용 시점: (1) "PDF 텍스트 추출해줘" (2) "이미지에서 글자 읽어줘" (3) "수기 메모 정리해줘" (4) "스캔 문서 변환해줘" (5) "사진 속 텍스트 추출해줘" (6) "문서 OCR 해줘"
---

# Document OCR - PDF/이미지 텍스트 추출 스킬

Gemini Vision API를 사용하여 PDF와 이미지에서 텍스트를 추출하는 스킬입니다.
수기 메모 인식에 특화되어 있습니다.

## 권장 워크플로우

**2단계 처리로 최상의 결과:**

1. **OCR (Gemini 3 Pro)**: 스크립트로 텍스트 추출 → 시각적 구조 상세 기록
2. **맥락 정리 (Claude)**: OCR 결과를 읽고 자연스럽게 재구성

```bash
# 1단계: OCR 수행
source /path/to/vault/.venv/bin/activate && \
  python .claude/skills/document-ocr/scripts/extract_text.py input.pdf --handwritten

# 2단계: Claude에게 정리 요청
# "00_Inbox/결과파일.md 읽고 맥락에 맞게 정리해줘"
```

## 사용 방법

```bash
source /path/to/vault/.venv/bin/activate && \
  python /path/to/vault/.claude/skills/document-ocr/scripts/extract_text.py \
  <input_file> [options]
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o, --output` | 출력 파일 경로 | 입력파일명.md |
| `-l, --language` | 언어 힌트 | ko |
| `-m, --model` | Gemini 모델 | gemini-3-pro-preview |
| `--handwritten` | 수기 메모 모드 | false |
| `--pages` | PDF 페이지 지정 | 전체 |
| `--api-key` | API 키 환경변수명 | GEMINI_API_KEY_FOR_AGENT |

### 예시

```bash
# 기본 사용 (gemini-3-pro-preview)
python scripts/extract_text.py document.pdf

# 수기 메모 처리
python scripts/extract_text.py memo.jpg --handwritten

# 특정 페이지만
python scripts/extract_text.py report.pdf --pages 1-5

# Flash 모델 사용 (빠름, 저렴)
python scripts/extract_text.py doc.pdf --model gemini-2.5-flash
```

## 지원 모델

| 모델 | 특징 |
|------|------|
| `gemini-3-pro-preview` | 최고 품질, 시각적 구조 상세 (기본) |
| `gemini-2.5-pro` | 좋은 품질 |
| `gemini-2.5-flash` | 빠름, 비용 효율적 |

## 환경 설정

`.env` 파일에 API 키 필요:
```
GEMINI_API_KEY_FOR_AGENT=...
```

## 출력 형식

```markdown
---
title: [파일명]
date: YYYY-MM-DD
tags:
  - OCR
  - 문서
source: [원본 파일명]
---

# [파일명] OCR 결과

## 페이지 1
[추출된 텍스트 - 시각적 구조 포함]
```

## 지원 파일 형식

PDF, PNG, JPEG, WebP, GIF, HEIC

## 의존성

루트 venv에 설치: google-genai, pdf2image, Pillow, pillow-heif, poppler
