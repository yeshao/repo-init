#!/usr/bin/env python3
"""
build_graph.py — Build a knowledge graph from scan and architecture data.

Usage:
    python3 build_graph.py <project-root> --output <output-path>

Produces a knowledge-graph.json with nodes, edges, layers, and tour.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def build_graph(scan_data: dict, layers: list[dict]) -> dict:
    """Build the knowledge graph from scan data and layers."""
    files = scan_data.get("files", [])
    import_map = scan_data.get("importMap", {})
    project = scan_data.get("project", {})

    nodes = []
    edges = []

    # Create file-level nodes
    for entry in files:
        node_id = f"file:{entry['path']}"
        nodes.append({
            "id": node_id,
            "type": get_node_type(entry),
            "name": Path(entry["path"]).name,
            "filePath": entry["path"],
            "summary": f"{get_node_type(entry).title()} file: {Path(entry['path']).name}",
            "tags": get_tags(entry),
            "complexity": estimate_file_complexity(entry["sizeLines"]),
        })

    # Create import edges
    for source_path, targets in import_map.items():
        source_id = f"file:{source_path}"
        for target_path in targets:
            target_id = f"file:{target_path}"
            edges.append({
                "source": source_id,
                "target": target_id,
                "type": "imports",
                "direction": "forward",
                "weight": 0.7,
            })

    # Create layer containment edges
    for layer in layers:
        for node_id in layer.get("nodeIds", []):
            edges.append({
                "source": layer["id"],
                "target": node_id,
                "type": "contains",
                "direction": "forward",
                "weight": 1.0,
            })

    # Create configures edges for config files
    for entry in files:
        if entry.get("fileCategory") == "config":
            node_id = f"file:{entry['path']}"
            # Config files configure the project entry points
            for other in files:
                if other.get("fileCategory") == "code" and other["path"].endswith(("index.ts", "index.js", "main.py", "main.go", "lib.rs", "mod.rs")):
                    edges.append({
                        "source": node_id,
                        "target": f"file:{other['path']}",
                        "type": "configures",
                        "direction": "forward",
                        "weight": 0.6,
                    })

    # Create documents edges for doc files
    for entry in files:
        if entry.get("fileCategory") == "docs":
            node_id = f"file:{entry['path']}"
            # Docs document the project
            for other in files:
                if other.get("fileCategory") == "code":
                    edges.append({
                        "source": node_id,
                        "target": f"file:{other['path']}",
                        "type": "documents",
                        "direction": "forward",
                        "weight": 0.5,
                    })
                    break  # Only connect to first code file to avoid noise

    # Create deploys edges for infra files
    for entry in files:
        if entry.get("fileCategory") == "infra":
            node_id = f"file:{entry['path']}"
            for other in files:
                if other.get("fileCategory") == "code":
                    edges.append({
                        "source": node_id,
                        "target": f"file:{other['path']}",
                        "type": "deploys",
                        "direction": "forward",
                        "weight": 0.7,
                    })
                    break

    # Build tour
    tour = build_tour(files, layers, import_map)

    return {
        "version": "1.0.0",
        "project": {
            "name": project.get("name", "Unknown"),
            "description": project.get("description", ""),
            "languages": project.get("languages", []),
            "frameworks": project.get("frameworks", []),
            "analyzedAt": datetime.now().isoformat(),
        },
        "nodes": nodes,
        "edges": edges,
        "layers": layers,
        "tour": tour,
    }


def get_node_type(entry: dict) -> str:
    """Get the knowledge graph node type for a file."""
    category = entry.get("fileCategory", "code")
    type_map = {
        "code": "file",
        "config": "config",
        "docs": "document",
        "infra": "service",
        "data": "table",
        "script": "file",
        "markup": "file",
    }
    # Refine infra types
    if category == "infra":
        path = entry["path"]
        if ".github/workflows" in path or ".gitlab-ci" in path or path.endswith("Jenkinsfile"):
            return "pipeline"
        if path.endswith(".tf") or path.endswith(".tfvars"):
            return "resource"
    # Refine data types
    if category == "data":
        path = entry["path"]
        if path.endswith((".graphql", ".gql", ".proto", ".prisma")):
            return "schema"
        if path.endswith((".sql",)):
            return "table"
    return type_map.get(category, "file")


def get_tags(entry: dict) -> list[str]:
    """Generate tags for a file."""
    tags = []
    path = entry["path"]
    category = entry.get("fileCategory", "code")
    name = Path(path).name

    if category == "code":
        if "index" in name:
            tags.append("entry-point")
        if ".test." in path or ".spec." in path or "test_" in path or "_test." in path:
            tags.append("test")
        if any(kw in path.lower() for kw in ["util", "helper", "common", "shared"]):
            tags.append("utility")
        if any(kw in path.lower() for kw in ["route", "controller", "handler", "api"]):
            tags.append("api-handler")
        if any(kw in path.lower() for kw in ["model", "entity", "schema"]):
            tags.append("data-model")
        if any(kw in path.lower() for kw in ["service", "domain", "logic"]):
            tags.append("service")
        if any(kw in path.lower() for kw in ["component", "view", "page", "layout"]):
            tags.append("component")
        if not tags:
            tags.append("code")
    elif category == "config":
        tags.append("configuration")
        if name in ("package.json", "Cargo.toml", "go.mod", "pyproject.toml"):
            tags.append("manifest")
    elif category == "docs":
        tags.append("documentation")
        if name.lower().startswith("readme"):
            tags.append("entry-point")
    elif category == "infra":
        tags.append("infrastructure")
        if "docker" in name.lower():
            tags.append("containerization")
        if ".github" in path:
            tags.append("ci-cd")
    elif category == "data":
        tags.append("database")
    elif category == "script":
        tags.append("automation")

    return tags[:5]


def estimate_file_complexity(lines: int) -> str:
    """Estimate file complexity from line count."""
    if lines < 50:
        return "simple"
    elif lines < 200:
        return "moderate"
    else:
        return "complex"


def build_tour(files: list[dict], layers: list[dict], import_map: dict) -> list[dict]:
    """Build a guided tour through the codebase."""
    tour = []
    step = 1

    # Step 1: README
    readme_files = [f for f in files if f["fileCategory"] == "docs" and f["path"].lower().startswith("readme")]
    if readme_files:
        tour.append({
            "order": step,
            "title": "Project Overview",
            "description": f"Start with {readme_files[0]['path']} to understand the project's purpose, architecture, and how to get started.",
            "nodeIds": [f"file:{readme_files[0]['path']}"],
        })
        step += 1

    # Step 2: Entry point
    entry_files = [f for f in files if "index" in f["path"].lower() and f["fileCategory"] == "code"]
    if entry_files:
        tour.append({
            "order": step,
            "title": "Application Entry Point",
            "description": f"The main entry point at {entry_files[0]['path']} bootstraps the application and imports core modules.",
            "nodeIds": [f"file:{entry_files[0]['path']}"],
        })
        step += 1

    # Step 3+: Architecture layers
    for layer in layers:
        layer_files = layer.get("nodeIds", [])
        if not layer_files:
            continue
        # Pick up to 3 representative files
        rep_files = layer_files[:3]
        tour.append({
            "order": step,
            "title": layer["name"],
            "description": layer["description"] + f" ({len(layer_files)} files).",
            "nodeIds": rep_files,
        })
        step += 1

    # Cap at 15 steps
    tour = tour[:15]

    # Renumber
    for i, t in enumerate(tour):
        t["order"] = i + 1

    return tour


def main():
    parser = argparse.ArgumentParser(description="Build knowledge graph")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--scan", help="Path to scan.json (will run scan if not provided)")
    parser.add_argument("--layers", help="Path to layers.json (will analyze if not provided)")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Load or run scan
    if args.scan:
        scan_data = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        from scan_project import scan_project
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            scan_path = f.name
        scan_data = scan_project(root, Path(scan_path))

    # Load or analyze layers
    if args.layers:
        layers = json.loads(Path(args.layers).read_text(encoding="utf-8"))
    else:
        from analyze_architecture import analyze_architecture
        layers = analyze_architecture(scan_data)

    # Build graph
    graph = build_graph(scan_data, layers)

    # Write output
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Knowledge graph built: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(graph['layers'])} layers, {len(graph['tour'])} tour steps.", file=sys.stderr)


if __name__ == "__main__":
    main()
