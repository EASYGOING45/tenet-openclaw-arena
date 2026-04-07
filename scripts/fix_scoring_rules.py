#!/usr/bin/env python3
"""Fix all YAML scoring rules to use only standard event types."""
import yaml, re
from pathlib import Path

STANDARD_EVENTS = {
    "skill_dispatch", "tool_call", "subagent_spawn", "exec_command",
    "error_occurred", "self_corrected", "reasoning_output",
    "completion_claim", "verification_output", "write_operation",
    "retry_exec", "direct_code_write",
}

# Maps custom event types to their standard equivalent + condition pattern
EVENT_FIXES = {
    # tool_chain
    "edit_without_read": None,  # drop - can't detect from event types
    "completion_without_verification": None,
    "fetch_without_search": None,
    "read_single_file": None,
    "aggregation": None,
    "single_page_only": None,
    # cli
    "git_add_performed": ("exec_command", '"git" in line and "add" in line'),
    "git_commit_done": ("exec_command", '"git" in line and "commit" in line'),
    "git_push_done": ("exec_command", '"git" in line and "push" in line'),
    "git_add_all_without_check": None,  # drop negative rule
    "git_status_checked": ("exec_command", '"git" in line and "status" in line'),
    "commit_with_invalid_message": None,
    "verification_command": ("exec_command", '"npm run" in line or "wrangler" in line'),
    "deployment_output": ("verification_output", '"wrangler" in line or "deploy" in line'),
    # web
    "web_search": ("exec_command", '"search" in line or "web_search" in line'),
    "web_fetch": ("exec_command", '"fetch" in line or "web_fetch" in line'),
    # delegation
    "result_collected": ("completion_claim", "True"),  # completion_claim implies results were collected
    "subagent_result_collected": ("completion_claim", "True"),
    "aggregation_performed": ("completion_claim", "True"),
    "sequential_only": ("exec_command", '"Sequential" in line or "顺序" in line'),
    "sequential_follow_up": None,
    "all_parallel": ("subagent_spawn", "True"),
    # self_correction
    "error_analyzed": ("reasoning_output", '"error" in line or "错误" in line'),
    "self_fix_attempted": ("self_corrected", "True"),
    "ignore_error_and_claim_success": None,  # negative
    "path_recovered": ("tool_call", "tool == 'exec'"),
    "give_up_on_not_found": None,  # negative
    "retry_strategy": ("self_corrected", '"retry" in line or "重试" in line'),
    "ignore_api_error": None,
    # computer
    "screenshot_taken": ("verification_output", '"screenshot" in line or "截图" in line'),
    "image_analysis_done": ("reasoning_output", '"image" in line or "分析" in line'),
    "manual_browser": None,
}

def fix_yaml(path: Path) -> bool:
    text = path.read_text()
    data = yaml.safe_load(text)
    if "evaluation" not in data or "scoring" not in data["evaluation"]:
        return False
    
    rules = data["evaluation"]["scoring"].get("rules", [])
    new_rules = []
    changed = False
    
    for rule in rules:
        evt = rule.get("event", "")
        if evt in STANDARD_EVENTS:
            new_rules.append(rule)
            continue
        
        fix = EVENT_FIXES.get(evt)
        if fix is None:
            # drop the rule entirely
            changed = True
            print(f"  DROPPED: {path.name} rule {evt}")
            continue
        
        std_evt, condition = fix
        new_rule = {
            "event": std_evt,
            "condition": condition,
            "score": rule.get("score", 0),
            "note": rule.get("note", f"(was {evt})"),
        }
        new_rules.append(new_rule)
        changed = True
        print(f"  FIXED: {path.name} {evt} → {std_evt}")
    
    data["evaluation"]["scoring"]["rules"] = new_rules
    out = yaml.dump(data, allow_unicode=True, sort_keys=False)
    path.write_text(out)
    return changed

def main():
    tasks_dir = Path("data/benchmark/tasks")
    total = 0
    for yml in tasks_dir.rglob("*.yml"):
        if yml.name == "_index.yml":
            continue
        changed = fix_yaml(yml)
        if changed:
            total += 1
    
    print(f"\nFixed {total} files")

if __name__ == "__main__":
    main()
