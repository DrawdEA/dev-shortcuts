#!/usr/bin/env python3
"""
scan_deps.py - Scans package.json and fetches live data from npm registry
for each dependency. Outputs structured JSON for Claude to interpret.

Usage: python scan_deps.py [path/to/package.json]
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

def fetch_npm(package_name):
    """Fetch package metadata from npm registry."""
    url = f"https://registry.npmjs.org/{package_name}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}

def months_since(iso_date_str):
    """Return months since a date string."""
    try:
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return round(delta.days / 30)
    except:
        return None

def has_types(data, pkg_name):
    """Check if package ships TypeScript types."""
    latest = data.get("dist-tags", {}).get("latest", "")
    version_data = data.get("versions", {}).get(latest, {})
    
    if version_data.get("types") or version_data.get("typings"):
        return True
    if "@types/" + pkg_name in (version_data.get("devDependencies") or {}):
        return False  # types are separate
    deps = {**( version_data.get("dependencies") or {}), **(version_data.get("peerDependencies") or {})}
    return False

def analyze_package(pkg_name, version_range):
    """Fetch and analyze a single package."""
    data = fetch_npm(pkg_name)
    
    if "error" in data:
        return {
            "name": pkg_name,
            "version_range": version_range,
            "status": "error",
            "error": data["error"]
        }
    
    latest = data.get("dist-tags", {}).get("latest", "unknown")
    deprecated = data.get("versions", {}).get(latest, {}).get("deprecated")
    
    # Last publish date
    time_data = data.get("time", {})
    modified = time_data.get("modified") or time_data.get(latest)
    months_old = months_since(modified) if modified else None
    
    # Weekly downloads (from registry metadata if available)
    # npm registry doesn't serve download counts directly, flag for Claude
    
    # TypeScript support
    latest_version_data = data.get("versions", {}).get(latest, {})
    has_ts = bool(latest_version_data.get("types") or latest_version_data.get("typings"))
    
    # Check if @types package exists (Claude will note this)
    separate_types = f"@types/{pkg_name}"
    
    # Readme quality signal (length as proxy)
    readme = data.get("readme", "")
    readme_length = len(readme)
    
    # Homepage / repo
    repo = data.get("repository", {})
    if isinstance(repo, dict):
        repo_url = repo.get("url", "").replace("git+", "").replace(".git", "")
    else:
        repo_url = str(repo) if repo else ""
    
    # Version freshness: compare installed range vs latest
    installed_major = None
    try:
        clean = version_range.lstrip("^~>=<")
        installed_major = int(clean.split(".")[0])
        latest_major = int(latest.split(".")[0])
        major_behind = latest_major - installed_major
    except:
        major_behind = None

    # Maintenance signals
    if months_old is not None:
        if months_old < 3:
            maintenance = "active"
        elif months_old < 12:
            maintenance = "moderate"
        elif months_old < 24:
            maintenance = "slow"
        else:
            maintenance = "abandoned"
    else:
        maintenance = "unknown"

    # Vibe/agentic compatibility score factors
    vibe_flags = []
    vibe_risks = []

    if deprecated:
        vibe_risks.append(f"DEPRECATED: {deprecated}")
    if not has_ts:
        vibe_risks.append("No bundled TypeScript types — Claude may hallucinate API shape")
    if readme_length < 500:
        vibe_risks.append("Sparse README — low documentation signal for LLMs")
    if maintenance in ("slow", "abandoned"):
        vibe_risks.append(f"Last publish {months_old}mo ago — training data may be stale")
    if major_behind and major_behind >= 2:
        vibe_risks.append(f"Pinned to v{installed_major}, latest is v{latest_major} — Claude may generate newer API")
    if maintenance == "active" and has_ts:
        vibe_flags.append("Well-typed + active — high Claude reliability")
    if readme_length > 5000:
        vibe_flags.append("Rich docs — good LLM context signal")

    return {
        "name": pkg_name,
        "version_range": version_range,
        "latest": latest,
        "months_since_publish": months_old,
        "maintenance": maintenance,
        "deprecated": deprecated,
        "has_bundled_types": has_ts,
        "separate_types_package": separate_types,
        "readme_length_chars": readme_length,
        "repo_url": repo_url,
        "major_behind": major_behind,
        "vibe_flags": vibe_flags,
        "vibe_risks": vibe_risks,
    }

def scan(package_json_path):
    with open(package_json_path) as f:
        pkg = json.load(f)

    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }

    # Skip non-npm entries
    skip_prefixes = ("node:", "file:", "workspace:", "link:")
    deps = {k: v for k, v in all_deps.items() 
            if not any(v.startswith(p) for p in skip_prefixes)}

    print(f"Scanning {len(deps)} packages from {package_json_path}...", file=sys.stderr)
    
    results = []
    for i, (name, version) in enumerate(deps.items(), 1):
        print(f"  [{i}/{len(deps)}] {name}", file=sys.stderr)
        result = analyze_package(name, version)
        results.append(result)

    output = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "package_json": package_json_path,
        "total": len(results),
        "results": results
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "package.json"
    scan(path)
