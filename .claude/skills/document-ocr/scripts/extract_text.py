#!/usr/bin/env python3
"""
Gemini Vision API를 사용한 PDF/이미지 OCR
수기 메모 인식에 최적화
"""
import os
import sys
import argparse
import base64
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# 지원 파일 형식
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.heic', '.heif'}
PDF_EXTENSIONS = {'.pdf'}


def convert_heic_to_jpeg(heic_path: Path) -> Path:
    """HEIC를 JPEG로 변환"""
    try:
        from pillow_heif import register_heif_opener
        from PIL import Image
        register_heif_opener()

        img = Image.open(heic_path)
        temp_path = Path(tempfile.mktemp(suffix='.jpg'))
        img.convert('RGB').save(temp_path, 'JPEG', quality=95)
        return temp_path
    except ImportError:
        print("⚠️  HEIC 변환을 위해 pillow-heif 설치 필요: pip install pillow-heif")
        return None


def pdf_to_images(pdf_path: Path, pages: list = None) -> list:
    """
    PDF를 이미지 리스트로 변환

    Args:
        pdf_path: PDF 파일 경로
        pages: 처리할 페이지 번호 리스트 (None이면 전체)

    Returns:
        (이미지 경로, 페이지 번호) 튜플 리스트
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("❌ pdf2image 설치 필요: pip install pdf2image")
        print("   또한 poppler 설치 필요: brew install poppler")
        return []

    try:
        print(f"📄 PDF 변환 중: {pdf_path.name}")

        # PDF를 이미지로 변환 (200 DPI)
        images = convert_from_path(pdf_path, dpi=200)
        total_pages = len(images)
        print(f"   총 {total_pages}페이지")

        # 임시 디렉토리에 이미지 저장
        temp_dir = Path(tempfile.mkdtemp(prefix="pdf_ocr_"))
        image_paths = []

        for i, img in enumerate(images, 1):
            # 페이지 필터링
            if pages and i not in pages:
                continue

            img_path = temp_dir / f"page_{i:03d}.png"
            img.save(img_path, 'PNG')
            image_paths.append((img_path, i))
            print(f"   ✓ 페이지 {i}/{total_pages} 변환 완료")

        return image_paths

    except Exception as e:
        print(f"❌ PDF 변환 실패: {e}")
        return []


def extract_text_from_image(image_path: Path, client, model_name: str = "gemini-2.5-pro",
                            language: str = "ko", handwritten: bool = None) -> str:
    """
    이미지에서 텍스트 추출 (Gemini Vision API)

    Args:
        image_path: 이미지 파일 경로
        client: Gemini 클라이언트
        model_name: Gemini 모델명
        language: 언어 힌트
        handwritten: 수기 메모 모드 (None이면 자동 감지)

    Returns:
        추출된 텍스트
    """
    # HEIC 변환
    original_path = image_path
    if image_path.suffix.lower() in {'.heic', '.heif'}:
        converted = convert_heic_to_jpeg(image_path)
        if converted:
            image_path = converted
        else:
            return "[HEIC 변환 실패]"

    # 이미지 로드
    with open(image_path, "rb") as f:
        image_data = f.read()

    # 프롬프트 구성
    lang_hint = "한국어" if language == "ko" else "English" if language == "en" else language

    if handwritten:
        prompt = f"""이 이미지는 수기로 작성된 메모/노트입니다.
모든 손글씨 텍스트를 정확하게 읽어서 추출해주세요.

규칙:
1. 손글씨를 최대한 정확하게 읽어 텍스트로 변환
2. 읽기 어려운 부분은 [불명확] 또는 (?) 표시
3. 화살표(→), 원, 밑줄 등 시각적 강조 요소 반영
4. 원본의 구조(들여쓰기, 번호, 계층)를 최대한 유지
5. {lang_hint}로 작성된 내용입니다

출력 형식: 마크다운"""
    else:
        prompt = f"""이 이미지에서 모든 텍스트를 추출하세요.

규칙:
1. 인쇄된 텍스트와 손글씨 모두 포함
2. 표, 목록 등 구조를 마크다운으로 변환
3. 읽을 수 없는 부분은 [불명확] 표시
4. 이미지 내 텍스트가 없으면 "[텍스트 없음]" 반환
5. {lang_hint}가 주 언어로 예상됨

출력 형식: 마크다운 (제목, 목록, 표 등 활용)"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_data,
                            ),
                            media_resolution={"level": "media_resolution_high"}
                        )
                    ]
                )
            ]
        )

        # 임시 변환 파일 정리
        if image_path != original_path:
            image_path.unlink(missing_ok=True)

        return response.text

    except Exception as e:
        print(f"❌ Gemini API 호출 실패: {e}")
        return f"[OCR 실패: {e}]"


def parse_pages(pages_str: str) -> list:
    """
    페이지 문자열 파싱 (예: "1,3,5" 또는 "1-5")
    """
    if not pages_str:
        return None

    pages = []
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


def extract_document(input_path: str, output_path: str = None, language: str = "ko",
                     model: str = "gemini-3-pro-preview", handwritten: bool = None,
                     pages: str = None, api_key_name: str = "GEMINI_API_KEY_FOR_AGENT") -> bool:
    """
    문서에서 텍스트 추출

    Args:
        input_path: 입력 파일 경로 (PDF 또는 이미지)
        output_path: 출력 파일 경로 (None이면 자동 생성)
        language: 언어 힌트
        model: Gemini 모델명
        handwritten: 수기 메모 모드
        pages: PDF 페이지 지정
        api_key_name: 환경변수에서 읽을 API 키 이름

    Returns:
        성공 여부
    """
    input_file = Path(input_path)

    # 파일 존재 확인
    if not input_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return False

    # API 키 확인
    api_key = os.getenv(api_key_name)
    if not api_key:
        print(f"❌ {api_key_name}가 설정되지 않았습니다.")
        return False

    # Gemini 클라이언트 초기화
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1alpha'}
    )

    # 출력 파일 경로 설정
    if output_path is None:
        output_path = input_file.with_suffix('.md')
    output_file = Path(output_path)

    # 파일 타입 확인
    ext = input_file.suffix.lower()

    print(f"📖 문서 OCR 시작: {input_file.name}")
    print(f"🤖 모델: {model}")
    print(f"🌐 언어: {language}")

    extracted_texts = []
    temp_dir = None

    try:
        if ext in PDF_EXTENSIONS:
            # PDF 처리
            page_list = parse_pages(pages)
            image_pages = pdf_to_images(input_file, page_list)

            if not image_pages:
                return False

            temp_dir = image_pages[0][0].parent

            for img_path, page_num in image_pages:
                print(f"\n🔍 페이지 {page_num} OCR 중...")
                text = extract_text_from_image(img_path, client, model, language, handwritten)
                extracted_texts.append((page_num, text))

        elif ext in IMAGE_EXTENSIONS:
            # 이미지 직접 처리
            print(f"\n🔍 이미지 OCR 중...")
            text = extract_text_from_image(input_file, client, model, language, handwritten)
            extracted_texts.append((1, text))

        else:
            print(f"❌ 지원하지 않는 파일 형식: {ext}")
            print(f"   지원 형식: {PDF_EXTENSIONS | IMAGE_EXTENSIONS}")
            return False

        # 마크다운 출력 생성
        today = datetime.now().strftime("%Y-%m-%d")

        output_lines = [
            "---",
            f"title: {input_file.stem}",
            f"date: {today}",
            "tags:",
            "  - OCR",
            "  - 문서",
            f"source: {input_file.name}",
            "---",
            "",
            f"# {input_file.stem} OCR 결과",
            "",
        ]

        for page_num, text in extracted_texts:
            if len(extracted_texts) > 1:
                output_lines.append(f"## 페이지 {page_num}")
                output_lines.append("")
            output_lines.append(text)
            output_lines.append("")

        # 파일 저장
        output_content = "\n".join(output_lines)
        output_file.write_text(output_content, encoding='utf-8')

        print(f"\n✅ OCR 완료!")
        print(f"📝 출력 파일: {output_file}")
        print(f"📊 추출된 페이지: {len(extracted_texts)}개")
        print(f"📏 텍스트 길이: {len(output_content):,} 글자")

        return True

    finally:
        # 임시 파일 정리
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Vision API로 PDF/이미지 OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s document.pdf
  %(prog)s image.png -o result.md
  %(prog)s handwritten.jpg --handwritten
  %(prog)s report.pdf --pages 1,3,5
  %(prog)s report.pdf --pages 1-10
  %(prog)s doc.pdf --model gemini-2.5-flash
        """
    )
    parser.add_argument("input_file", help="입력 파일 (PDF 또는 이미지)")
    parser.add_argument("-o", "--output", help="출력 마크다운 파일 경로")
    parser.add_argument("-l", "--language", default="ko",
                        help="언어 힌트 (ko, en 등, 기본: ko)")
    parser.add_argument("-m", "--model", default="gemini-3-pro-preview",
                        help="Gemini 모델 (기본: gemini-3-pro-preview)")
    parser.add_argument("--handwritten", action="store_true",
                        help="수기 메모 모드 활성화")
    parser.add_argument("--pages", help="PDF 특정 페이지만 처리 (예: 1,3,5 또는 1-5)")
    parser.add_argument("--api-key", default="GEMINI_API_KEY_FOR_AGENT",
                        help="API 키 환경변수 이름 (기본: GEMINI_API_KEY_FOR_AGENT)")

    args = parser.parse_args()

    success = extract_document(
        args.input_file,
        args.output,
        args.language,
        args.model,
        args.handwritten if args.handwritten else None,
        args.pages,
        args.api_key
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
