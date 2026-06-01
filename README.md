# repo-init

> Scaffold a complete AI Coding infrastructure and codebase analysis pipeline into any repository — in one command.

`repo-init` initializes a production-ready AI Coding infrastructure (inspired by [Chromium's `agents/` directory](https://chromium.googlesource.com/chromium/src/+/main/agents/)) and a codebase analysis pipeline (inspired by [Understand-Anything](https://github.com/Lum1104/Understand-Anything)) into any repository.

## What It Does

### 1. AI Coding Infrastructure

Scaffolds a layered prompt system, reusable skills, a knowledge base with document routing, eval test suites, and project templates:

```
agents/
├── ai_policy.md                    # AI usage policy (human accountability)
├── prompts/
│   ├── common.minimal.md          # Core build/test/coding instructions
│   ├── common.md                  # 8-step standard workflow
│   ├── knowledge_base.md          # Agentic RAG document routing table
│   ├── templates/default.md       # Platform build targets & test commands
│   ├── eval/                      # AI behavior regression test suite
│   └── commands/                  # Task prompt shortcut templates
├── skills/
│   ├── understand/SKILL.md        # Codebase analysis & knowledge graph
│   └── understand-dashboard/SKILL.md  # Interactive dashboard launcher
├── extensions/                    # MCP extensions placeholder
└── projects/                      # Large-scale AI project templates
```

Based on how Chromium structures AI-assisted development at scale — layered composable prompts, on-demand skills, Agentic RAG, and eval-driven quality.

### 2. Codebase Analysis Pipeline

A 4-phase Python pipeline that analyzes any codebase and produces structured knowledge:

| Phase | Script | Output |
|-------|--------|--------|
| **Context** | `generate_context.py` | Build commands, doc routes, debug patterns, framework detection |
| **Scan** | `scan_project.py` | File inventory, language detection, import maps |
| **Analyze** | `analyze_architecture.py` | Architecture layers (API, Service, Data, UI, etc.) |
| **Graph** | `build_graph.py` | Knowledge graph with nodes, edges, layers, and guided tour |
| **Dashboard** | `launch_dashboard.py` | Interactive web dashboard for exploration |

The context file (`.understand/context.md`) is specifically designed to be read by an LLM to auto-customize all the AI Coding templates with project-specific build commands, doc routes, and debug patterns.

## Quick Start

```bash
# Install the skill
cp -r repo-init ~/.config/opencode/skills/repo-init

# Initialize a repository
python3 scripts/init_ai_coding.py --dir /path/to/my-project --project-name "My Project"

# Preview before writing
python3 scripts/init_ai_coding.py --dir /path/to/my-project --dry-run

# Analyze the codebase
cd /path/to/my-project
python3 scripts/understand/generate_context.py .
cat .understand/context.md
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json
python3 scripts/understand/launch_dashboard.py . --port 3000
```

## What Gets Detected Automatically

The `generate_context.py` script (pure Python, no LLM needed) detects:

- **Build system** — 14+ build tools (Cargo, npm, Go, Python, Ruby, Java, etc.) with correct build/test/lint/check commands
- **Frameworks** — 50+ frameworks across 7 ecosystems (React, Django, Flask, Rails, Spring, etc.)
- **Documentation structure** — Categorizes docs into API reference, architecture, deployment, testing, security, troubleshooting
- **Language-specific patterns** — Common errors and debugging routes for 10+ languages
- **Architecture layers** — Directory-based detection of API, Service, Data, UI, Middleware, Infrastructure layers

## Requirements

- Python 3.9+
- No external dependencies — all scripts use only the standard library

## License

MIT
