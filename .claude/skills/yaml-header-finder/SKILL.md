---
name: yaml-header-finder
description: YAML 헤더가 누락된 마크다운 파일을 찾습니다. md파일에서 YAML front matter가 없는 파일을 검색하거나, yaml-header-inserter 서브에이전트 실행 전에 대상 파일을 파악할 때 사용하세요.
---

# YAML Header Finder

YAML 헤더가 누락된 마크다운 파일을 효율적으로 찾는 skill입니다.

## 사용 방법

### 스크립트 실행

```bash
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py <directory> [options]
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `--limit N`, `-l N` | 최대 N개 결과만 반환 (기본: 무제한) |
| `--exclude PATTERN`, `-e PATTERN` | 제외할 경로 패턴 (여러 번 사용 가능) |
| `--count-only`, `-c` | 파일 개수만 출력 |
| `--relative`, `-r` | 상대 경로로 출력 |

### 예시

```bash
# 전체 vault에서 YAML 헤더 없는 파일 찾기
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py .

# 04_Networking 폴더만 검색
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py ./04_Networking

# 최대 10개만 찾기
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py . --limit 10

# 개수만 확인
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py . --count-only

# 특정 폴더 제외
python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py . --exclude "90_Archives" --exclude "SNS"
```

## 기본 제외 폴더

다음 폴더들은 자동으로 제외됩니다:
- `.obsidian` - Obsidian 설정
- `.git` - Git 저장소
- `.venv` - Python 가상환경
- `node_modules` - Node.js 모듈
- `Templates` - 옵시디언 템플릿 (의도적으로 헤더 없음)

## yaml-header-inserter와 함께 사용

1. 먼저 이 skill로 YAML 헤더가 없는 파일 목록 확인:
   ```bash
   python .claude/skills/yaml-header-finder/scripts/find_missing_yaml.py ./04_Networking --limit 5
   ```

2. 출력된 파일 목록을 yaml-header-inserter 서브에이전트에 전달하여 헤더 삽입

이 방식으로 전체 파일을 읽지 않고도 대상 파일만 효율적으로 처리할 수 있습니다.

## 출력 형식

기본 출력:
```
/path/to/file1.md
/path/to/file2.md

총 2개 파일에 YAML 헤더가 누락되어 있습니다.
```

`--relative` 옵션 사용 시:
```
04_Networking/person1.md
04_Networking/person2.md
```

`--count-only` 옵션 사용 시:
```
42
```
