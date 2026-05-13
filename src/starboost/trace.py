from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .util import write_json


def parse_jsonl(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                event = {"type": "unparsed_line", "text": line}
            events.append(event)
    return events


def summarize_events(events_path: Path, output_path: Path) -> Dict[str, Any]:
    events = parse_jsonl(events_path)
    counts: Dict[str, int] = {}
    reasoning: List[Any] = []
    agent_messages: List[Any] = []
    command_outputs: List[Any] = []
    file_changes: List[Any] = []
    for event in events:
        event_type = str(event.get("type") or event.get("event") or event.get("msg", {}).get("type") or "unknown")
        counts[event_type] = counts.get(event_type, 0) + 1
        text = json.dumps(event, ensure_ascii=False)
        if "reasoning" in text.lower():
            reasoning.append(event)
        if "agent_message" in text or event_type == "agent_message":
            agent_messages.append(event)
        if "command_execution" in text or "exec_command" in text:
            command_outputs.append(event)
        if "file_change" in text or "apply_patch" in text:
            file_changes.append(event)
    summary = {
        "event_count": len(events),
        "event_type_counts": counts,
        "reasoning_items": reasoning[:50],
        "agent_messages": agent_messages[:50],
        "command_execution_items": command_outputs[:100],
        "file_change_items": file_changes[:100],
    }
    write_json(output_path, summary)
    return summary

