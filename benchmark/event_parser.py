"""
Event parser for OpenClaw agent output.

Parses behavior events from `openclaw agent --json` stdout/stderr.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Known event types matching YAML evaluation.trace.events
KNOWN_EVENT_TYPES = [
    "skill_dispatch",
    "tool_call",
    "subagent_spawn",
    "exec_command",
    "error_occurred",
    "self_corrected",
    "reasoning_output",
    "completion_claim",
    "verification_output",
    "write_operation",
    "retry_exec",
    "direct_code_write",
]

# Keyword → event type mappings for stdout text parsing
_KEYWORD_EVENT_MAP = {
    # skill_dispatch
    re.compile(r"skill_invoked|Calling skill|sessions_spawn|skill:\s*\w", re.I): "skill_dispatch",
    # tool_call
    re.compile(r"\bread\b|\bedit\b|\bwrite\b|\bexec\b|tool_call|Tool Call", re.I): "tool_call",
    # subagent_spawn
    re.compile(r"spawn|subagent|Starting.*agent|agent.*started", re.I): "subagent_spawn",
    # exec_command — use word boundary so it matches in JSON like {"command": "git status"}
    re.compile(r"\bgit\b|\bnpm\b|\bwrangler\b|\bpython3?\b|\bbash\b|\bsh\b|\bcurl\b", re.I): "exec_command",
    # error_occurred
    re.compile(r"\berror\b|\bError\b|\bfailed\b|\bfailure\b|Exception|traceback", re.I): "error_occurred",
    # self_corrected
    re.compile(r"retry|recover|fixing|self.correct|修正|重试", re.I): "self_corrected",
    # reasoning_output
    re.compile(r"reasoning|thinking|分析|推理|step\s+\d", re.I): "reasoning_output",
    # completion_claim
    re.compile(r"complete|done|finished|已完成|完成|任务完成", re.I): "completion_claim",
    # verification_output
    re.compile(r"verify|validation|验证|check.*pass", re.I): "verification_output",
    # write_operation
    re.compile(r"write.*file|file.*written|写入|创建文件", re.I): "write_operation",
    # direct_code_write
    re.compile(r"```[\w]+|code_block|direct.*code|直接写代码", re.I): "direct_code_write",
}

# Patterns that indicate a skill name was invoked
_SKILL_NAME_RE = re.compile(
    r"(?:skill|calling|invoked|skill_name|skill_name)\s*[:\-]?\s*[\"']?(\w[\w\-]*)[\"']?",
    re.I,
)
_SKILL_INVOKE_RE = re.compile(r"skill[_\-]?invoked|calling skill", re.I)


def _extract_skill_from_text(text: str) -> str | None:
    """Try to extract a skill name from a line of text."""
    # Look for known skill names
    known_skills = {
        "brainstorming", "frontend-design", "systematic-debugging",
        "test-driven-development", "verification-before-completion",
        "using-superpowers", "acp-router", "playwright", "tavily-search",
        "imagegen", "sora", "frontend-skill", "skill-creator",
        "self-improvement", "brainstorm", "writing-plans",
        "executing-plans", "subagent-driven-development",
        "requesting-code-review", "finishing-a-development-branch",
        "receiving-code-review", "normalize", "polish", "audit",
        "harden", "optimize", "animate", "delight", "adapt",
        "clarify", "critique", "distill", "extract", "bolder",
        "colorize", "quieter", "onboard", "teach-impeccable",
    }
    words = re.split(r"[\s,\-:]+", text)
    for word in words:
        if word.lower() in known_skills:
            return word.lower()
    # Try regex extraction
    m = _SKILL_NAME_RE.search(text)
    if m:
        return m.group(1).lower()
    return None


def _extract_tool_from_text(text: str) -> str | None:
    """Try to extract a tool name from a line of text."""
    tools = {"read", "edit", "write", "exec", "read_file", "write_file",
             "subprocess", "tool_call", "message", "tts", "image_generate",
             "web_search", "web_fetch", "canvas", "pdf", "image"}
    text_lower = text.lower()
    for tool in tools:
        if re.search(rf"\b{tool}\b", text_lower):
            return tool
    return None


def _parse_json_payload(stdout: str) -> list[dict[str, Any]]:
    """Try to parse tool calls from JSON sections in stdout."""
    events = []
    # Try to find JSON objects in the output
    try:
        # Try full JSON first
        parsed = json.loads(stdout.strip())
        # Walk the parsed structure looking for tool calls
        events.extend(_walk_json_for_events(parsed))
    except (json.JSONDecodeError, ValueError):
        # Try extracting JSON from lines
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{") or line.startswith("["):
                try:
                    parsed = json.loads(line)
                    events.extend(_walk_json_for_events(parsed))
                except (json.JSONDecodeError, ValueError):
                    continue
    return events


def _walk_json_for_events(obj: Any, path: str = "") -> list[dict[str, Any]]:
    """Recursively walk a parsed JSON object to find event-like structures."""
    events = []
    if isinstance(obj, dict):
        # Check for tool call indicators
        if "tool" in obj or "tool_call" in obj or "name" in obj:
            tool_name = obj.get("tool") or obj.get("tool_call") or obj.get("name", "")
            if tool_name:
                events.append({
                    "type": "tool_call",
                    "tool": str(tool_name),
                    "source": "json",
                    "path": path,
                })
        # Check for skill dispatch
        if "skill" in obj or "skill_invoked" in obj or "skill_name" in obj:
            skill_name = obj.get("skill") or obj.get("skill_invoked") or obj.get("skill_name", "")
            if skill_name:
                events.append({
                    "type": "skill_dispatch",
                    "skill": str(skill_name),
                    "source": "json",
                    "path": path,
                })
        # Check for subagent spawn
        if "subagent" in obj or "spawn" in obj or "agent_id" in obj:
            if obj.get("subagent") or obj.get("spawn"):
                events.append({
                    "type": "subagent_spawn",
                    "source": "json",
                    "path": path,
                })
        # Recurse into values
        for key, value in obj.items():
            if key not in ("payloads", "result", "messages"):
                events.extend(_walk_json_for_events(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            events.extend(_walk_json_for_events(item, f"{path}[{i}]"))
    return events


def _parse_text_events(text: str) -> list[dict[str, Any]]:
    """Parse behavior events from raw text output using keyword matching."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 3:
            continue

        for pattern, event_type in _KEYWORD_EVENT_MAP.items():
            if pattern.search(line):
                # Try to extract more context
                skill = None
                tool = None
                detail = line

                if event_type == "skill_dispatch":
                    skill = _extract_skill_from_text(line)
                elif event_type == "tool_call":
                    tool = _extract_tool_from_text(line)

                events.append({
                    "type": event_type,
                    "line": line[:200],
                    "skill": skill,
                    "tool": tool,
                })
                break  # One event per line

    return events


def parse_events(stdout: str, stderr: str) -> list[dict[str, Any]]:
    """
    Parse behavior events from openclaw agent output.

    Args:
        stdout: Raw stdout from openclaw agent --json
        stderr: Raw stderr from openclaw agent

    Returns:
        List of event dicts, e.g.:
        [{"type": "skill_dispatch", "skill": "brainstorming", "timestamp": 3.2},
         {"type": "tool_call", "tool": "read", "timestamp": 5.1}, ...]
    """
    all_events: list[dict[str, Any]] = []
    seen_lines: set[str] = set()

    # 1. Parse JSON payload (tool calls, skill dispatches)
    json_events = _parse_json_payload(stdout)
    for e in json_events:
        all_events.append({**e, "parser": "json"})

    # 2. Parse stdout text for keyword events
    text_events = _parse_text_events(stdout)
    for e in text_events:
        # Deduplicate
        line_key = e.get("line", "")[:100]
        if line_key and line_key not in seen_lines:
            seen_lines.add(line_key)
            all_events.append({**e, "parser": "text"})

    # 3. Parse stderr for errors
    for line in stderr.splitlines():
        line = line.strip()
        if re.search(r"\berror\b|\bError\b|\bfailed\b|\bException\b|\btraceback\b", line, re.I):
            all_events.append({
                "type": "error_occurred",
                "line": line[:200],
                "source": "stderr",
            })

    # 4. Add inferred reasoning_output events
    # If there are multi-line blocks with substantial reasoning, mark them
    reasoning_blocks = _find_reasoning_blocks(stdout)
    for block in reasoning_blocks:
        all_events.append({
            "type": "reasoning_output",
            "content_preview": block[:100],
            "source": "inferred",
        })

    # 5. Detect direct code writing
    if re.search(r"```\w+.*\n.{10,}", stdout) or re.search(r"write.*```", stdout, re.I):
        all_events.append({
            "type": "direct_code_write",
            "source": "inferred",
        })

    return all_events


def _find_reasoning_blocks(text: str) -> list[str]:
    """Find substantial reasoning/thinking blocks in text."""
    blocks = []
    current_block = []
    in_block = False

    for line in text.splitlines():
        stripped = line.strip()
        # Reasoning markers
        if re.match(r"(reasoning|thinking|分析|推理|step\s+\d)", stripped, re.I):
            in_block = True
            current_block = [stripped]
        elif in_block:
            if len(stripped) > 50 and not stripped.startswith("["):
                current_block.append(stripped)
            elif len(current_block) > 0 and stripped == "":
                # Empty line might end the block
                pass
            elif len(current_block) > 0 and not re.match(r"[\[\]]", stripped[0]):
                # Try to detect block end
                if len(current_block) >= 2:
                    block_text = " ".join(current_block)
                    if len(block_text) > 100:
                        blocks.append(block_text)
                current_block = []
                in_block = False

    # Don't forget the last block
    if len(current_block) >= 2:
        block_text = " ".join(current_block)
        if len(block_text) > 100:
            blocks.append(block_text)

    return blocks
