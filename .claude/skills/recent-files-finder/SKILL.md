---
name: recent-files-finder
description: Git status 기반으로 최근 추가/수정된 파일을 찾는 스킬. 사용 시점: (1) "최근 추가된 파일 찾아줘" (2) "새로 만든 파일 목록" (3) "수정된 파일 확인" (4) "인물 관련 새 파일 찾기" (5) 인물사전 업데이트 전 대상 파일 파악 시
---

# Recent Files Finder

Git status를 활용해 최근 추가/수정된 파일을 검색하는 스킬.

## 사용 방법

```bash
python .claude/skills/recent-files-finder/scripts/find_recent_files.py [options]
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `--type`, `-t` | 파일 유형: `all`(기본), `untracked`, `modified`, `added` |
| `--ext`, `-e` | 확장자 필터 (예: `-e .md`) - 여러 번 사용 가능 |
| `--path`, `-p` | 경로 패턴 필터 (예: `-p Networking`) - 여러 번 사용 가능 |
| `--person`, `-P` | 인물 관련 파일만 필터링 |
| `--count`, `-c` | 파일 개수만 출력 |

## 예시

```bash
# 모든 새 파일/수정 파일 (마크다운만)
python .claude/skills/recent-files-finder/scripts/find_recent_files.py -e .md

# 인물 관련 파일만
python .claude/skills/recent-files-finder/scripts/find_recent_files.py -e .md --person

# 특정 폴더의 새 파일
python .claude/skills/recent-files-finder/scripts/find_recent_files.py -t untracked -p "취업작전"

# 개수만 확인
python .claude/skills/recent-files-finder/scripts/find_recent_files.py --person -c
```

## 인물 관련 파일 판별 기준

`--person` 옵션은 다음 패턴으로 인물 관련 파일을 필터링:
- `인물사전`, `Networking` 경로
- `미팅`, `커피챗`, `면접`, `대화` 키워드
- `~님`, `_책임`, `_대표`, `_과장`, `_팀장` 패턴
