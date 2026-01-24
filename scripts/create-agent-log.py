#!/usr/bin/env python3
"""
Agent Log Generator

Creates agent logs following AGENT_LOG_TEMPLATE.md format.
Integrates with three-pass workflow.

Usage:
    # Create new log
    python3 .repo/automation/scripts/create-agent-log.py \
        --agent-id <id> \
        --task-id <task-id> \
        --intent <intent> \
        [--log-file <path>]
    
    # Update log (add actions)
    python3 .repo/automation/scripts/create-agent-log.py \
        --log-file <path> \
        --add-action <action-type> \
        --filepath <filepath> \
        --reasoning <reasoning>
    
    # Add evidence
    python3 .repo/automation/scripts/create-agent-log.py \
        --log-file <path> \
        --add-evidence <evidence-type> \
        --command <command> \
        --output <output>

Exit codes:
    0 - Success
    1 - Error
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def create_log_template(
    agent_id: str,
    task_id: str,
    intent: str,
    status: str = "pending"
) -> Dict:
    """Create new agent log from template."""
    return {
        "intent": intent,
        "plan": [],
        "actions": [],
        "evidence": [],
        "decisions": [],
        "risks": [],
        "follow_ups": [],
        "reasoning_summary": "",
        "notes": "No secrets. No private data. No raw chain-of-thought.",
        "metadata": {
            "agent_id": agent_id,
            "task_id": task_id,
            "status": status,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
    }


def load_log(log_path: Path) -> Dict:
    """Load existing log file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    content = log_path.read_text(encoding="utf-8")
    return json.loads(content)


def save_log(log_path: Path, log_data: Dict):
    """Save log file."""
    log_data["metadata"]["updated"] = datetime.now().isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log_data, indent=2), encoding="utf-8")


def add_action(
    log_data: Dict,
    action_type: str,
    filepath: str,
    reasoning: str,
    verification: Optional[str] = None
):
    """Add action to log."""
    action = {
        "type": action_type,
        "filepath": filepath,
        "timestamp": datetime.now().isoformat(),
        "reasoning": reasoning,
    }
    
    if verification:
        action["verification"] = verification
    
    log_data["actions"].append(action)


def add_evidence(
    log_data: Dict,
    evidence_type: str,
    command: str,
    output: str,
    status: str = "passed"
):
    """Add evidence to log."""
    evidence = {
        "type": evidence_type,
        "command": command,
        "output": output,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    
    log_data["evidence"].append(evidence)


def main():
    parser = argparse.ArgumentParser(description="Create and manage agent logs")
    
    # Create new log
    parser.add_argument("--agent-id", type=str, help="Agent identifier")
    parser.add_argument("--task-id", type=str, help="Task ID")
    parser.add_argument("--intent", type=str, help="Intent/goal")
    parser.add_argument("--status", type=str, default="pending", 
                       choices=["pending", "in_progress", "completed", "failed"],
                       help="Initial status")
    
    # Update existing log
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument("--add-action", type=str, 
                       choices=["create", "modify", "delete", "read", "verify", "test"],
                       help="Add action to log")
    parser.add_argument("--filepath", type=str, help="File path for action")
    parser.add_argument("--reasoning", type=str, help="Reasoning for action")
    parser.add_argument("--verification", type=str, help="Verification evidence")
    
    parser.add_argument("--add-evidence", type=str,
                       choices=["build", "test", "lint", "type-check"],
                       help="Add evidence to log")
    parser.add_argument("--command", type=str, help="Command that was run")
    parser.add_argument("--output", type=str, help="Command output")
    parser.add_argument("--evidence-status", type=str, default="passed",
                       choices=["passed", "failed", "skipped"],
                       help="Evidence status")
    
    parser.add_argument("--logs-dir", type=str, default=".repo/logs",
                       help="Directory for log files")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent.parent.parent
    logs_dir = repo_root / args.logs_dir
    
    # Create new log
    if args.agent_id and args.task_id and args.intent:
        log_data = create_log_template(args.agent_id, args.task_id, args.intent, args.status)
        log_filename = f"log-{args.task_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        log_path = logs_dir / log_filename
        
        if not args.dry_run:
            save_log(log_path, log_data)
            print(f"✅ Created agent log: {log_path}")
        else:
            print(f"DRY RUN: Would create log: {log_path}")
            print(json.dumps(log_data, indent=2))
        
        sys.exit(0)
    
    # Update existing log
    if args.log_file:
        log_path = Path(args.log_file) if Path(args.log_file).is_absolute() else repo_root / args.log_file
        
        if not log_path.exists():
            print(f"Error: Log file not found: {log_path}")
            sys.exit(1)
        
        log_data = load_log(log_path)
        
        if args.add_action:
            if not args.filepath or not args.reasoning:
                print("Error: --filepath and --reasoning required for --add-action")
                sys.exit(1)
            
            add_action(log_data, args.add_action, args.filepath, args.reasoning, args.verification)
            
            if not args.dry_run:
                save_log(log_path, log_data)
                print(f"✅ Added action to log: {log_path}")
            else:
                print("DRY RUN: Would add action:")
                print(json.dumps(log_data["actions"][-1], indent=2))
        
        if args.add_evidence:
            if not args.command or not args.output:
                print("Error: --command and --output required for --add-evidence")
                sys.exit(1)
            
            add_evidence(log_data, args.add_evidence, args.command, args.output, args.evidence_status)
            
            if not args.dry_run:
                save_log(log_path, log_data)
                print(f"✅ Added evidence to log: {log_path}")
            else:
                print("DRY RUN: Would add evidence:")
                print(json.dumps(log_data["evidence"][-1], indent=2))
        
        sys.exit(0)
    
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
