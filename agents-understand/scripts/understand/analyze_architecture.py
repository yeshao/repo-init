#!/usr/bin/env python3
"""
analyze_architecture.py — Analyze a codebase's architecture and assign files to layers.

Usage:
    python3 analyze_architecture.py <project-root> --output <output-path> [--scan <scan.json>]

Produces a JSON file with 3-10 architecture layers, each containing file node IDs.
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Layer pattern matching
# ---------------------------------------------------------------------------

DIR_PATTERNS = {
    "routes": "api", "api": "api", "controllers": "api", "handlers": "api",
    "endpoints": "api", "views": "api", "blueprints": "api", "routers": "api",
    "services": "service", "core": "service", "domain": "service",
    "lib": "service", "logic": "service", "internal": "service",
    "mailers": "service", "jobs": "service", "channels": "service",
    "signals": "service", "composables": "service", "management": "service",
    "commands": "service", "pkg": "service",
    "models": "data", "db": "data", "data": "data", "persistence": "data",
    "repository": "data", "entities": "data", "entity": "data",
    "dto": "data", "request": "data", "response": "data",
    "migrations": "data", "sql": "data", "database": "data", "schema": "data",
    "components": "ui", "views": "ui", "pages": "ui", "ui": "ui",
    "layouts": "ui", "screens": "ui",
    "middleware": "middleware", "plugins": "middleware",
    "interceptors": "middleware", "guards": "middleware",
    "utils": "utility", "helpers": "utility", "common": "utility",
    "shared": "utility", "tools": "utility", "templatetags": "utility",
    "config": "config", "constants": "config", "env": "config",
    "settings": "config",
    "__tests__": "test", "test": "test", "tests": "test",
    "spec": "test", "specs": "test",
    "types": "types", "interfaces": "types", "schemas": "types",
    "contracts": "types", "dtos": "types",
    "hooks": "hooks",
    "store": "state", "state": "state", "reducers": "state",
    "actions": "state", "slices": "state",
    "assets": "assets", "static": "assets", "public": "assets",
    "docs": "documentation", "documentation": "documentation", "wiki": "documentation",
    "deploy": "infrastructure", "deployment": "infrastructure",
    "infra": "infrastructure", "infrastructure": "infrastructure",
    "docker": "infrastructure",
    "k8s": "infrastructure", "kubernetes": "infrastructure",
    "helm": "infrastructure", "charts": "infrastructure",
    "terraform": "infrastructure", "tf": "infrastructure",
    ".github": "ci-cd", ".gitlab": "ci-cd", ".circleci": "ci-cd",
    "bin": "entry", "cmd": "entry",
    "src/main/java": "service", "src/test/java": "test",
}

FILE_PATTERNS = {
    "manage.py": "entry", "wsgi.py": "config", "asgi.py": "config",
    "config.ru": "entry",
}

FILE_EXT_PATTERNS = {
    ".test.": "test", ".spec.": "test",
    "test_": "test", "_test.": "test", "_spec.": "test",
    "Test.": "test", "Tests.": "test",
    ".d.ts": "types",
}


def get_layer_for_file(entry: dict) -> str:
    """Determine the architecture layer for a file."""
    path = entry["path"]
    parts = path.split("/")
    category = entry.get("fileCategory", "code")

    # Non-code categories
    if category == "docs":
        return "documentation"
    if category == "infra":
        # Distinguish CI/CD from infrastructure
        if ".github/workflows" in path or ".gitlab-ci" in path or ".circleci" in path or path.endswith("Jenkinsfile"):
            return "ci-cd"
        return "infrastructure"
    if category == "config":
        return "config"
    if category == "data":
        return "data"
    if category == "script":
        return "script"
    if category == "markup":
        return "ui"

    # Check filename patterns
    filename = parts[-1] if parts else ""
    if filename in FILE_PATTERNS:
        return FILE_PATTERNS[filename]

    # Check file extension patterns
    for pattern, layer in FILE_EXT_PATTERNS.items():
        if pattern in filename:
            return layer

    # Check directory patterns (most specific first)
    for part in parts[:-1]:  # Skip the filename itself
        if part in DIR_PATTERNS:
            return DIR_PATTERNS[part]

    # Check Java/Kotlin src/main and src/test structure
    for i, part in enumerate(parts):
        if part == "src" and i + 1 < len(parts):
            if parts[i + 1] == "main":
                return "service"
            if parts[i + 1] == "test":
                return "test"

    # Default: service layer for code files
    return "service"


def analyze_architecture(scan_data: dict) -> list[dict]:
    """Analyze the scan data and produce architecture layers."""
    files = scan_data.get("files", [])

    # Group files by layer
    layer_files: dict[str, list[str]] = {}
    for entry in files:
        layer = get_layer_for_file(entry)
        node_id = f"file:{entry['path']}"
        layer_files.setdefault(layer, []).append(node_id)

    # Define layer metadata
    LAYER_META = {
        "api": {"name": "API Layer", "description": "HTTP endpoints, route handlers, request/response processing"},
        "service": {"name": "Service Layer", "description": "Core business logic, domain services, and orchestration"},
        "data": {"name": "Data Layer", "description": "Database schemas, data models, migrations, and persistence"},
        "ui": {"name": "UI Layer", "description": "User interface components, pages, views, and presentation logic"},
        "middleware": {"name": "Middleware Layer", "description": "Cross-cutting concerns: auth, logging, validation, interceptors"},
        "utility": {"name": "Utility Layer", "description": "Shared helpers, common utilities, and cross-cutting functions"},
        "config": {"name": "Configuration", "description": "Project configuration files, environment settings, and build config"},
        "test": {"name": "Test Suite", "description": "Unit tests, integration tests, and test fixtures"},
        "types": {"name": "Type Definitions", "description": "Type interfaces, DTOs, schemas, and contract definitions"},
        "hooks": {"name": "Hooks", "description": "React hooks, custom hooks, and composable logic"},
        "state": {"name": "State Management", "description": "Application state, stores, reducers, and state logic"},
        "assets": {"name": "Assets", "description": "Static assets, images, fonts, and public files"},
        "infrastructure": {"name": "Infrastructure", "description": "Container definitions, deployment configs, and infrastructure-as-code"},
        "ci-cd": {"name": "CI/CD", "description": "Continuous integration, delivery pipelines, and automated workflows"},
        "documentation": {"name": "Documentation", "description": "Project documentation, guides, and references"},
        "script": {"name": "Scripts", "description": "Build scripts, automation scripts, and CLI tools"},
        "entry": {"name": "Entry Points", "description": "Application entry points and bootstrap files"},
    }

    # Build layers output (only include non-empty layers)
    layers = []
    for layer_id, node_ids in sorted(layer_files.items()):
        if not node_ids:
            continue
        meta = LAYER_META.get(layer_id, {"name": layer_id.title(), "description": f"Files in the {layer_id} layer"})
        layers.append({
            "id": f"layer:{layer_id}",
            "name": meta["name"],
            "description": meta["description"],
            "nodeIds": sorted(node_ids),
        })

    return layers


def main():
    parser = argparse.ArgumentParser(description="Analyze codebase architecture")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--scan", help="Path to scan.json (will run scan if not provided)")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Load or run scan
    if args.scan:
        scan_data = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    else:
        # Import and run scan inline
        sys.path.insert(0, str(Path(__file__).parent))
        from scan_project import scan_project
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            scan_path = f.name
        scan_data = scan_project(root, Path(scan_path))

    # Analyze
    layers = analyze_architecture(scan_data)

    # Write output
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(layers, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Architecture analysis complete. {len(layers)} layers identified.", file=sys.stderr)
    for layer in layers:
        print(f"  {layer['name']}: {len(layer['nodeIds'])} files", file=sys.stderr)


if __name__ == "__main__":
    main()
