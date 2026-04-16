#!/usr/bin/env python3
"""
audit.py - Pre-release codebase scanner for JS/TS projects.
Scans for critical issues, warnings, and info signals.

Usage: python audit.py <project-root>
"""

import json
import os
import re
import sys
from pathlib import Path

# File extensions to scan
SCAN_EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".expo", "coverage", "__pycache__"}

# Secret patterns (regex)
SECRET_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI/Anthropic API key"),
    (r'sk-ant-[a-zA-Z0-9\-]{20,}', "Anthropic API key"),
    (r'AIza[0-9A-Za-z\-_]{35}', "Google API key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
    (r'xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}', "Slack bot token"),
    (r'(?i)(api_key|apikey|api_secret|secret_key)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key assignment"),
    (r'(?i)(password|passwd)\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
    (r'(?i)bearer\s+[a-zA-Z0-9\-._~+/]{20,}', "Hardcoded bearer token"),
]

# Console/debug patterns
DEBUG_PATTERNS = [
    (r'console\.(log|error|warn|debug|info)\(', "console statement"),
    (r'\bdebugger\b', "debugger statement"),
]

# TODO patterns
TODO_PATTERNS = [
    (r'(?i)\b(TODO|FIXME|HACK|XXX)\b', "TODO/FIXME comment"),
]

# Localhost patterns
LOCALHOST_PATTERNS = [
    (r'(?i)(localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?', "localhost reference"),
]

# TypeScript escape hatches
TS_PATTERNS = [
    (r'@ts-ignore', "ts-ignore"),
    (r'@ts-nocheck', "ts-nocheck"),
    (r'as\s+any\b', "as any cast"),
]

# Async error handling
ASYNC_PATTERNS = [
    (r'await\s+\w+\(', "await without try/catch (check manually)"),
]

def get_project_name(root):
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            return data.get("name", root.name)
        except:
            pass
    return root.name

def detect_platform(root):
    pkg = root / "package.json"
    platforms = []
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "expo" in deps:
                platforms.append("expo")
            if "next" in deps:
                platforms.append("nextjs")
        except:
            pass
    return platforms

def scan_file(filepath, root):
    issues = {"critical": [], "warning": [], "info": []}
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        rel = str(filepath.relative_to(root))

        for i, line in enumerate(lines, 1):
            # Skip commented import lines and node_modules references
            stripped = line.strip()

            # Critical: secrets
            for pattern, label in SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Skip if it looks like an env var reference
                    if "process.env" in line or "import.meta.env" in line:
                        continue
                    preview = line.strip()[:80]
                    issues["critical"].append({
                        "file": rel, "line": i,
                        "type": "secret", "label": label,
                        "preview": preview
                    })

            # Critical: localhost (skip test files)
            if not any(x in rel for x in ["test", "spec", "__tests__", ".test.", ".spec."]):
                for pattern, label in LOCALHOST_PATTERNS:
                    if re.search(pattern, line):
                        issues["critical"].append({
                            "file": rel, "line": i,
                            "type": "localhost", "label": label,
                            "preview": line.strip()[:80]
                        })

            # Warning: console statements (skip test files)
            if not any(x in rel for x in ["test", "spec", "__tests__", ".test.", ".spec."]):
                for pattern, label in DEBUG_PATTERNS:
                    if re.search(pattern, line):
                        issues["warning"].append({
                            "file": rel, "line": i,
                            "type": "debug", "label": label,
                            "preview": line.strip()[:80]
                        })

            # Warning: TODOs
            for pattern, label in TODO_PATTERNS:
                if re.search(pattern, line):
                    issues["warning"].append({
                        "file": rel, "line": i,
                        "type": "todo", "label": label,
                        "preview": line.strip()[:80]
                    })

            # Warning: ts-ignore abuse
            for pattern, label in TS_PATTERNS:
                if re.search(pattern, line):
                    issues["warning"].append({
                        "file": rel, "line": i,
                        "type": "ts_escape", "label": label,
                        "preview": line.strip()[:80]
                    })

    except Exception as e:
        pass

    return issues

def check_env_files(root):
    issues = {"critical": [], "warning": [], "info": []}

    env_file = root / ".env"
    env_example = root / ".env.example"
    gitignore = root / ".gitignore"

    # Check if .env is gitignored
    if env_file.exists():
        gitignored = False
        if gitignore.exists():
            content = gitignore.read_text()
            gitignored = ".env" in content or "*.env" in content
        if not gitignored:
            issues["critical"].append({
                "file": ".env", "line": 0,
                "type": "env_exposed",
                "label": ".env file not in .gitignore",
                "preview": "Risk of committing secrets to git"
            })
        if not env_example.exists():
            issues["warning"].append({
                "file": ".env.example", "line": 0,
                "type": "missing_env_example",
                "label": ".env.example missing",
                "preview": "Other devs won't know what env vars are needed"
            })

    return issues

def check_expo(root):
    issues = {"critical": [], "warning": [], "info": []}

    # Check app.json / app.config.js
    app_json = root / "app.json"
    app_config = root / "app.config.js"

    config_file = app_json if app_json.exists() else app_config if app_config.exists() else None

    if config_file and app_json.exists():
        try:
            data = json.loads(app_json.read_text())
            expo = data.get("expo", {})
            if not expo.get("version"):
                issues["critical"].append({
                    "file": "app.json", "line": 0,
                    "type": "missing_version",
                    "label": "Missing expo.version in app.json",
                    "preview": "Required for App Store submission"
                })
            android = expo.get("android", {})
            ios = expo.get("ios", {})
            if not android.get("versionCode"):
                issues["warning"].append({
                    "file": "app.json", "line": 0,
                    "type": "missing_version_code",
                    "label": "Missing android.versionCode",
                    "preview": "Required for Play Store submission"
                })
            if not ios.get("buildNumber"):
                issues["warning"].append({
                    "file": "app.json", "line": 0,
                    "type": "missing_build_number",
                    "label": "Missing ios.buildNumber",
                    "preview": "Required for App Store submission"
                })
        except:
            pass

    # Check for EAS config
    eas_json = root / "eas.json"
    if not eas_json.exists():
        issues["info"].append({
            "file": "eas.json", "line": 0,
            "type": "missing_eas",
            "label": "No eas.json found",
            "preview": "Needed if using EAS Build/Submit"
        })

    return issues

def check_info(root):
    info = {}
    info["has_readme"] = (root / "README.md").exists() or (root / "readme.md").exists()
    info["has_license"] = (root / "LICENSE").exists() or (root / "LICENSE.md").exists()
    info["has_env_example"] = (root / ".env.example").exists()
    info["has_changelog"] = (root / "CHANGELOG.md").exists() or (root / "CHANGELOG").exists()

    # Tests
    test_dirs = ["__tests__", "tests", "test", "spec"]
    has_tests = any((root / d).exists() for d in test_dirs)
    if not has_tests:
        # Check for .test. or .spec. files
        for ext in SCAN_EXTS:
            found = list(root.rglob(f"*.test{ext}")) + list(root.rglob(f"*.spec{ext}"))
            found = [f for f in found if not any(skip in str(f) for skip in SKIP_DIRS)]
            if found:
                has_tests = True
                break
    info["has_tests"] = has_tests

    return info

def scan(project_root_str):
    root = Path(project_root_str).resolve()
    if not root.exists():
        print(json.dumps({"error": f"Path not found: {root}"}))
        sys.exit(1)

    project_name = get_project_name(root)
    platforms = detect_platform(root)

    all_issues = {"critical": [], "warning": [], "info_items": []}

    # Scan source files
    for filepath in root.rglob("*"):
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue
        if filepath.suffix in SCAN_EXTS and filepath.is_file():
            file_issues = scan_file(filepath, root)
            all_issues["critical"].extend(file_issues["critical"])
            all_issues["warning"].extend(file_issues["warning"])

    # Env file checks
    env_issues = check_env_files(root)
    all_issues["critical"].extend(env_issues["critical"])
    all_issues["warning"].extend(env_issues["warning"])

    # Platform checks
    if "expo" in platforms:
        expo_issues = check_expo(root)
        all_issues["critical"].extend(expo_issues["critical"])
        all_issues["warning"].extend(expo_issues["warning"])
        all_issues["info_items"].extend(expo_issues["info"])

    # Info
    info = check_info(root)

    # Deduplicate console.log — group by type
    console_issues = [i for i in all_issues["warning"] if i["type"] == "debug"]
    other_warnings = [i for i in all_issues["warning"] if i["type"] != "debug"]
    if console_issues:
        # Summarize instead of listing every single one
        files = list({i["file"] for i in console_issues})
        all_issues["warning"] = other_warnings + [{
            "file": f"{len(files)} files",
            "line": 0,
            "type": "debug_summary",
            "label": f"console statements ({len(console_issues)} instances across {len(files)} files)",
            "preview": "Run grep to see all locations",
            "files": files[:5]
        }]

    output = {
        "project": project_name,
        "root": str(root),
        "platforms": platforms,
        "critical": all_issues["critical"],
        "warnings": all_issues["warning"],
        "info": info,
        "info_items": all_issues["info_items"],
        "verdict": "block" if all_issues["critical"] else "caution" if all_issues["warning"] else "ready"
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    scan(path)
