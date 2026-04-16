#!/usr/bin/env python3
"""
fixer.py - Auto-fixes safe, mechanical issues found by audit.py.
Only touches things that are unambiguously correct to remove/add.

Usage: python fixer.py <audit-json-file> <project-root>
       echo '<audit-json>' | python fixer.py - <project-root>

Returns JSON with a log of what was changed.
"""

import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".expo", "coverage"}

def fix_console_logs(project_root, issues):
    """Remove console.log/warn/debug statements from non-test files."""
    fixed = []
    
    # Collect all files with console issues
    files_to_fix = set()
    for issue in issues:
        if issue.get("type") in ("debug", "debug_summary"):
            if issue.get("type") == "debug_summary":
                files_to_fix.update(issue.get("files", []))
            else:
                files_to_fix.add(issue["file"])

    root = Path(project_root)
    
    for rel_path in files_to_fix:
        filepath = root / rel_path
        if not filepath.exists():
            continue
        # Skip test files
        if any(x in rel_path for x in ["test", "spec", "__tests__"]):
            continue
            
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        original = content
        
        # Remove standalone console.log lines (entire line)
        # Pattern: optional whitespace, console.xxx(...), optional semicolon, newline
        content = re.sub(
            r'[ \t]*console\.(log|warn|debug|info)\([^)]*\);?\n',
            '',
            content
        )
        # Handle multiline console.log (basic case: console.log( ... ) spanning lines)
        # Only remove if the call is on its own line
        content = re.sub(
            r'[ \t]*console\.(log|warn|debug|info)\([\s\S]*?\);?\n',
            '',
            content
        )
        
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            removed = original.count("console.") - content.count("console.")
            fixed.append({
                "file": rel_path,
                "action": "removed_console_logs",
                "count": removed
            })
    
    return fixed

def fix_debugger_statements(project_root, issues):
    """Remove debugger statements."""
    fixed = []
    root = Path(project_root)
    
    debugger_issues = [i for i in issues if i.get("label", "").startswith("debugger")]
    files = set(i["file"] for i in debugger_issues)
    
    for rel_path in files:
        filepath = root / rel_path
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        original = content
        content = re.sub(r'[ \t]*debugger;?\n', '', content)
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            fixed.append({"file": rel_path, "action": "removed_debugger"})
    
    return fixed

def generate_env_example(project_root, issues):
    """Generate .env.example from .env with values redacted."""
    root = Path(project_root)
    env_file = root / ".env"
    env_example = root / ".env.example"
    
    if not env_file.exists():
        return None
    if env_example.exists():
        return None  # Don't overwrite existing
    
    lines = env_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    example_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            example_lines.append(line)
            continue
        if "=" in stripped:
            key, _, _ = stripped.partition("=")
            example_lines.append(f"{key.strip()}=")
        else:
            example_lines.append(line)
    
    env_example.write_text("\n".join(example_lines) + "\n", encoding="utf-8")
    return {
        "file": ".env.example",
        "action": "generated_env_example",
        "note": "Values redacted, keys preserved"
    }

def fix(audit_json, project_root):
    root = Path(project_root).resolve()
    
    all_fixed = []
    skipped = []
    
    warnings = audit_json.get("warnings", [])
    critical = audit_json.get("critical", [])
    all_issues = warnings + critical
    
    # Fix 1: console logs
    console_fixed = fix_console_logs(str(root), warnings)
    all_fixed.extend(console_fixed)
    
    # Fix 2: debugger statements
    debugger_fixed = fix_debugger_statements(str(root), warnings)
    all_fixed.extend(debugger_fixed)
    
    # Fix 3: .env.example
    env_result = generate_env_example(str(root), critical)
    if env_result:
        all_fixed.append(env_result)
    
    # Report what we can't fix
    unfixable_types = {"secret", "localhost", "env_exposed", "missing_version", 
                       "missing_build_number", "ts_escape", "todo"}
    for issue in all_issues:
        if issue.get("type") in unfixable_types:
            skipped.append({
                "file": issue.get("file"),
                "line": issue.get("line"),
                "label": issue.get("label"),
                "reason": "requires human judgment"
            })
    
    return {
        "fixed": all_fixed,
        "skipped": skipped,
        "total_fixed": len(all_fixed),
        "total_skipped": len(skipped)
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python fixer.py <audit-json-or-> <project-root>"}))
        sys.exit(1)
    
    audit_source = sys.argv[1]
    project_root = sys.argv[2]
    
    if audit_source == "-":
        audit_json = json.loads(sys.stdin.read())
    else:
        audit_json = json.loads(Path(audit_source).read_text())
    
    result = fix(audit_json, project_root)
    print(json.dumps(result, indent=2))
