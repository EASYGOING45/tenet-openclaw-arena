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
# ORDER MATTERS: more specific patterns must come before generic ones
_KEYWORD_EVENT_MAP = [
    # skill_dispatch — must check BEFORE exec_command to avoid matching "git" in skill names
    (re.compile(r"skill_invoked|Calling skill|sessions_spawn|skill:\s*\w|\bsubagent\b", re.I), "skill_dispatch"),
    # tool_call
    (re.compile(r"\bread\b|\bedit\b|\bwrite\b|\bexec\b|tool_call|Tool Call", re.I), "tool_call"),
    # subagent_spawn
    (re.compile(r"spawn|subagent|Starting.*agent|agent.*started", re.I), "subagent_spawn"),
    # exec_command — match actual CLI invocations (avoid matching "git" in skill names)
    (re.compile(r'\bgit\s+(?:status|add|commit|push|pull|log|diff|checkout|branch|merge|rebase|config|init|clone|fetch|remote|stash|tag|show)\b', re.I), "exec_command"),
    (re.compile(r'\bnpm\s+(?:install|run|build|test|start|dev|deploy|publish|version)\b', re.I), "exec_command"),
    (re.compile(r'\bwrangler\s+(?:deploy|publish|dev|config|secret|kv|r2|d1)\b', re.I), "exec_command"),
    (re.compile(r'\bpython3?\s+(?:\-m\s+)?\S+', re.I), "exec_command"),
    (re.compile(r'\b(?:bash|sh|curl)\s+\S+', re.I), "exec_command"),
    # error_occurred
    (re.compile(r"\berror\b|\bError\b|\bfailed\b|\bfailure\b|Exception|traceback", re.I), "error_occurred"),
    # self_corrected
    (re.compile(r"retry|recover|fixing|self.correct|修正|重试", re.I), "self_corrected"),
    # reasoning_output
    (re.compile(r"reasoning|thinking|分析|推理|step\s+\d", re.I), "reasoning_output"),
    # completion_claim
    (re.compile(r"complete|done|finished|已完成|完成|任务完成", re.I), "completion_claim"),
    # verification_output
    (re.compile(r"verify|validation|验证|check.*pass", re.I), "verification_output"),
    # write_operation
    (re.compile(r"write.*file|file.*written|写入|创建文件", re.I), "write_operation"),
    # direct_code_write
    (re.compile(r"```[\w]+|code_block|direct.*code|直接写代码", re.I), "direct_code_write"),
]
# Keep as LIST to preserve priority order (first match wins)

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
                # Try to extract command text from nested params
                line_content = ""
                params = obj.get("params") or obj.get("parameters") or obj.get("arguments") or {}
                if isinstance(params, dict):
                    cmd = params.get("command") or params.get("cmd") or params.get("shell") or params.get("script", "")
                    text = params.get("text") or ""
                    if cmd:
                        line_content = f"command={cmd} {text}".strip()
                    elif text:
                        line_content = text[:200]
                elif isinstance(params, str):
                    line_content = params[:200]

                events.append({
                    "type": "tool_call",
                    "tool": str(tool_name),
                    "line": line_content,
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


_COMMAND_FIELD_RE = re.compile(
    r"\"(?:command|cmd|command_text|shell)\"\s*:\s*\"([^\"]*(?:git|npm|wrangler|python|bash|sh|curl)[^\"]*)\"",
    re.I,
)


def _extract_command_from_text(text: str) -> str | None:
    """Extract the actual shell command from a line of text."""
    m = _COMMAND_FIELD_RE.search(text)
    if m:
        return m.group(1)
    # Fallback: look for "git ..." "npm ..." etc patterns
    for pattern in [r"(git\s+\S+.*?)(?:\",|\"|\s*$)", r"(npm\s+\S+.*?)(?:\",|\"|\s$)", r"(wrangler\s+\S+.*?)(?:\",|\"|\s$)"]:
        m = re.search(pattern, text, re.I)
        if m:
            return m.group(1).strip()
    return None


def _parse_text_events(text: str) -> list[dict[str, Any]]:
    """Parse behavior events from raw text output using keyword matching."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 3:
            continue

        for pattern, event_type in _KEYWORD_EVENT_MAP:
            if pattern.search(line):
                # Try to extract more context
                skill = None
                tool = None
                detail = line

                if event_type == "skill_dispatch":
                    skill = _extract_skill_from_text(line)
                elif event_type == "tool_call":
                    tool = _extract_tool_from_text(line)

                # Extract command text for exec_command / tool_call events
                if event_type in ("exec_command", "tool_call"):
                    cmd = _extract_command_from_text(line)
                    if cmd:
                        detail = cmd

                events.append({
                    "type": event_type,
                    "line": detail[:200],
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

    # 1. Parse JSON payload (tool calls, skill dispatches)
    json_events = _parse_json_payload(stdout)

    # 2. Parse stdout text for keyword events
    text_events = _parse_text_events(stdout)

    # 3. Merge: prefer text events (they have line content) over JSON events (line may be empty)
    # Dedupe by (type, line_prefix) — keep entry with non-empty line
    type_to_event: dict[tuple, dict] = {}
    for e in json_events:
        key = (e.get("type", ""), e.get("line", "")[:50])
        if key not in type_to_event or not type_to_event[key].get("line"):
            type_to_event[key] = {**e, "parser": "json"}
    for e in text_events:
        key = (e.get("type", ""), e.get("line", "")[:50])
        if key not in type_to_event or e.get("line"):
            type_to_event[key] = {**e, "parser": "text"}

    all_events = list(type_to_event.values())

    # 4. Parse stderr for errors
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
