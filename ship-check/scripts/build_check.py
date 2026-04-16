#!/usr/bin/env python3
"""
build_check.py - Runs the project's build pipeline and reports results.
Runs before static analysis — a broken build is an instant DO NOT SHIP.

Usage: python build_check.py <project-root>
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def detect_commands(root):
    """Detect what build/check commands are available from package.json scripts."""
    pkg = root / "package.json"
    if not pkg.exists():
        return []

    try:
        data = json.loads(pkg.read_text())
        scripts = data.get("scripts", {})
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    except:
        return []

    commands = []

    # TypeScript type check (fastest, no output files)
    if "typescript" in deps or "tsc" in str(scripts):
        commands.append({
            "name": "TypeScript",
            "cmd": ["npx", "tsc", "--noEmit"],
            "critical": True,
            "timeout": 60
        })

    # Lint
    if "lint" in scripts:
        commands.append({
            "name": "Lint",
            "cmd": ["npm", "run", "lint"],
            "critical": False,
            "timeout": 60
        })

    # Expo export (instead of full build — faster, catches bundler errors)
    if "expo" in deps:
        commands.append({
            "name": "Expo export (bundle check)",
            "cmd": ["npx", "expo", "export", "--platform", "all", "--output-dir", "/tmp/expo-export-check"],
            "critical": True,
            "timeout": 120
        })

    # Next.js build
    elif "next" in deps:
        commands.append({
            "name": "Next.js build",
            "cmd": ["npm", "run", "build"],
            "critical": True,
            "timeout": 180
        })

    # Generic build script fallback
    elif "build" in scripts and "expo" not in deps and "next" not in deps:
        commands.append({
            "name": "Build",
            "cmd": ["npm", "run", "build"],
            "critical": True,
            "timeout": 120
        })

    # Tests (if present)
    if "test" in scripts and scripts["test"] != "echo \"Error: no test specified\" && exit 1":
        commands.append({
            "name": "Tests",
            "cmd": ["npm", "run", "test", "--", "--passWithNoTests", "--watchAll=false"],
            "critical": False,
            "timeout": 120
        })

    return commands

def run_command(cmd, cwd, timeout):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[-3000:] if result.stdout else "",  # last 3k chars
            "stderr": result.stderr[-3000:] if result.stderr else "",
            "timed_out": False
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "timed_out": True
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command not found: {e}",
            "timed_out": False
        }

def check(project_root_str):
    root = Path(project_root_str).resolve()

    if not root.exists():
        print(json.dumps({"error": f"Path not found: {root}"}))
        sys.exit(1)

    commands = detect_commands(root)

    if not commands:
        print(json.dumps({
            "skipped": True,
            "reason": "No recognizable build scripts found in package.json"
        }))
        return

    results = []
    has_critical_failure = False

    for cmd_def in commands:
        print(f"  Running {cmd_def['name']}...", file=sys.stderr)
        result = run_command(cmd_def["cmd"], root, cmd_def["timeout"])

        entry = {
            "name": cmd_def["name"],
            "cmd": " ".join(cmd_def["cmd"]),
            "critical": cmd_def["critical"],
            "success": result["success"],
            "timed_out": result["timed_out"],
        }

        if not result["success"]:
            # Extract most useful error lines
            error_output = result["stderr"] or result["stdout"]
            # Get lines with "error" in them (most useful for build failures)
            error_lines = [l for l in error_output.splitlines() if "error" in l.lower()][:20]
            entry["error_summary"] = "\n".join(error_lines) if error_lines else error_output[:500]

            if cmd_def["critical"]:
                has_critical_failure = True
        
        results.append(entry)

        # Stop on critical failure — no point running rest
        if has_critical_failure and cmd_def["critical"]:
            results.append({
                "name": "Remaining checks",
                "skipped": True,
                "reason": f"Skipped due to critical failure in {cmd_def['name']}"
            })
            break

    output = {
        "project_root": str(root),
        "commands_run": len([r for r in results if not r.get("skipped")]),
        "has_critical_failure": has_critical_failure,
        "results": results,
        "verdict": "fail" if has_critical_failure else "pass"
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    check(path)
