---
name: understand-dashboard
description: |
  Launch an interactive web dashboard to explore a codebase knowledge graph.
  Use when the user wants to visualize the project structure, browse the
  knowledge graph, search for files/functions, or explore guided tours.
  Triggers on: "show me the codebase", "open the dashboard", "visualize the
  project", "explore the knowledge graph", "show architecture", "dashboard".
---

# Understand Dashboard

Launch an interactive web dashboard to explore the knowledge graph produced by the `understand` skill.

## When to Use

- "Show me the codebase structure"
- "Open the knowledge graph dashboard"
- "Visualize the project architecture"
- "Explore the codebase"
- "Show me how this project is organized"

## Quick Start

```bash
# Launch the dashboard for the current project
python3 scripts/understand/launch_dashboard.py .

# Specify a custom port
python3 scripts/understand/launch_dashboard.py . --port 3000

# Open with a specific knowledge graph
python3 scripts/understand/launch_dashboard.py . --graph .understand/knowledge-graph.json
```

## Dashboard Features

- **Structural Graph View**: Interactive force-directed graph of files, functions, and classes
- **Domain View**: Business domains, flows, and steps as a horizontal graph
- **Layer View**: Files grouped by architectural layer with color coding
- **Search**: Fuzzy search across file names, function names, and summaries
- **Guided Tour**: Step-by-step walkthrough of the codebase
- **Node Details**: Click any node to see its summary, tags, code preview, and relationships

## Prerequisites

The knowledge graph must be built first:

```bash
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json
```
