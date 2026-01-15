#!/usr/bin/env python3
"""
Claude Code 에이전트/스킬 활동 로깅 스크립트.

Hooks에서 stdin으로 JSON 데이터를 받아 .claude/stream.jsonl에 활동 로그를 기록합니다.

Hook Input Format (stdin):
{
  "hook_event_name": "PreToolUse" | "PostToolUse",
  "tool_name": "Task" | "Skill",
  "tool_input": {
    "subagent_type": "agent-name",  // Task 도구
    "skill": "skill-name"           // Skill 도구
  }
}
"""

import sys
import json
import time
import uuid
import os
from pathlib import Path

# 프로젝트 루트 찾기 (환경변수 또는 스크립트 위치 기반)
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent))
LOG_FILE = PROJECT_ROOT / ".claude" / "stream.jsonl"
ID_TRACK_FILE = PROJECT_ROOT / ".claude" / ".activity_ids.json"

# 최대 로그 파일 크기 (1MB)
MAX_LOG_SIZE = 1_000_000


def get_or_create_id(event: str, node_type: str, name: str) -> str:
    """실행 ID 관리 - start시 생성, end시 조회"""
    id_map = {}
    if ID_TRACK_FILE.exists():
        try:
            id_map = json.loads(ID_TRACK_FILE.read_text())
        except:
            id_map = {}

    key = f"{node_type}:{name}"

    if event == "start":
        new_id = str(uuid.uuid4())[:8]
        id_map[key] = new_id
        ID_TRACK_FILE.write_text(json.dumps(id_map))
        return new_id
    else:
        exec_id = id_map.pop(key, str(uuid.uuid4())[:8])
        ID_TRACK_FILE.write_text(json.dumps(id_map))
        return exec_id


def truncate_log_if_needed():
    """로그 파일이 너무 크면 최근 1000줄만 유지"""
    if not LOG_FILE.exists():
        return
    if LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        lines = LOG_FILE.read_text().splitlines()[-1000:]
        LOG_FILE.write_text('\n'.join(lines) + '\n')


def log_activity(event: str, node_type: str, name: str):
    """활동 로그 기록"""
    truncate_log_if_needed()
    exec_id = get_or_create_id(event, node_type, name)

    log_entry = {
        "ts": int(time.time() * 1000),
        "event": event,
        "type": node_type,
        "name": name,
        "id": exec_id
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    return exec_id


def main():
    try:
        # stdin에서 JSON 읽기
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # JSON 파싱 실패 시 조용히 종료
    except:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # 이벤트 타입 결정
    if hook_event == "PreToolUse":
        event = "start"
    elif hook_event == "PostToolUse":
        event = "end"
    else:
        sys.exit(0)

    # 도구별 처리
    if tool_name == "Task":
        node_type = "agent"
        name = tool_input.get("subagent_type", "")
    elif tool_name == "Skill":
        node_type = "skill"
        name = tool_input.get("skill", "")
    else:
        sys.exit(0)

    if not name:
        sys.exit(0)

    log_activity(event, node_type, name)
    sys.exit(0)


if __name__ == "__main__":
    main()
