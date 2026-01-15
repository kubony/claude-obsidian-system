---
name: audio-transcriber
description: OpenAI Whisper API를 사용하여 오디오 파일을 텍스트로 변환합니다. m4a, WAV 등 다양한 포맷 지원.
---

# Audio Transcriber - 오디오 STT 스킬

OpenAI Whisper API를 사용하여 오디오 파일을 텍스트로 변환하는 스킬입니다.

## 사용 시점

- "녹음 파일 변환해줘"
- "오디오를 텍스트로 만들어줘"
- "STT 해줘"

## 기능

- OpenAI Whisper API 사용
- 지원 포맷: m4a, WAV, mp3, mp4, mpeg, mpga, webm
- 자동 청크 분할 (25MB 제한)
- 타임스탬프 포함 옵션
- 언어 자동 감지 (한국어/영어)

## 환경 설정

`.env` 파일에 API 키 필요:
```
OPENAI_API_KEY=sk-...
```

## 사용 방법

```bash
python scripts/transcribe.py <audio_file> [--output output.txt] [--language ko]
```

### 옵션

- `--output`: 출력 파일 경로 (기본: 입력파일명.txt)
- `--language`: 언어 코드 (기본: auto, 한국어는 ko)
- `--timestamp`: 타임스탬프 포함 여부
- `--model`: Whisper 모델 (기본: whisper-1)

## 출력 형식

```
[화자 식별 시도]
전사된 텍스트 내용...

[타임스탬프 포함 시]
[00:00:00] 텍스트 내용
[00:00:15] 다음 내용
```

## 처리 흐름

1. 오디오 파일 검증
2. 25MB 이하인지 확인 (초과 시 분할 권장)
3. OpenAI API 호출
4. 결과를 .txt 파일로 저장
5. 성공 여부 반환
