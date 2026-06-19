# repo-init

> Scaffold a complete AI Coding infrastructure and codebase analysis pipeline into any repository — in one command.

[![CI](https://github.com/yeshao/repo-init/actions/workflows/ci.yml/badge.svg)](https://github.com/yeshao/repo-init/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`repo-init` initializes a production-ready AI Coding infrastructure (inspired by [Chromium's `agents/` directory](https://chromium.googlesource.com/chromium/src/+/main/agents/)) and a codebase analysis pipeline (inspired by [Understand-Anything](https://github.com/Lum1104/Understand-Anything)) into any repository.

## Why This Exists

AI coding agents fail on new repositories because they don't know:

- ❌ **How to build/test/lint** — every project has different commands
- ❌ **Framework conventions** — React ≠ Django ≠ Spring
- ❌ **Architecture** — where is the API layer? The data layer?
- ❌ **Documentation routes** — which doc answers which question?

Without this context, AI agents guess — and guessed code is buggy code. `repo-init` solves this by scaffolding a complete AI-aware infrastructure **and** auto-analyzing your codebase to populate it.

### Before → After

| Before | After `repo-init` |
|--------|-------------------|
| AI agent guesses build commands | `.understand/context.md` provides exact `build`, `test`, `lint` commands |
| AI doesn't know your framework | Templates pre-configured with framework-specific patterns |
| AI can't find relevant docs | Knowledge base routing table maps questions to doc paths |
| No AI behavior regression tests | Eval test suite catches prompt regressions |
| Manual codebase exploration | Interactive knowledge graph + guided onboarding tour |

## What It Does

### 1. AI Coding Infrastructure

Scaffolds a layered prompt system, reusable skills, a knowledge base with document routing, eval test suites, and project templates:

```
agents/
├── ai_policy.md                        # AI usage policy (human accountability)
├── prompts/
│   ├── common.minimal.md              # Core build/test/coding instructions
│   ├── common.md                      # 8-step standard workflow
│   ├── knowledge_base.md              # Agentic RAG document routing table
│   ├── templates/
│   │   ├── default.md                   # Platform build targets & test commands
│   │   └── README.md                   # Templates directory guide
│   ├── eval/
│   │   ├── README.md                   # Eval framework guide
│   │   └── example/
│   │       ├── prompt.md               # Example eval prompt
│   │       └── eval.md                 # Example eval assertions
│   └── commands/
│       └── README.md                   # Commands directory guide
├── skills/
│   ├── README.md                       # Skills directory guide
│   ├── example-skill/
│   │   └── SKILL.md                    # Example skill placeholder
│   ├── understand/
│   │   └── SKILL.md                    # Codebase analysis & knowledge graph
│   └── understand-dashboard/
│       └── SKILL.md                    # Interactive dashboard launcher
├── extensions/
│   └── README.md                       # MCP extensions placeholder
├── projects/
│   └── README.md                       # Large-scale AI project templates
├── references/
│   ├── customization-guide.md          # How to customize templates
│   ├── design-principles.md           # Design philosophy
│   └── structure.md                    # Project structure overview
scripts/
├── chromium_docs.py                    # Document search tool
└── understand/
    ├── generate_context.py             # Context generation (runs scan internally)
    ├── scan_project.py                 # File inventory & language detection
    ├── analyze_architecture.py         # Architecture layer detection
    ├── build_graph.py                  # Knowledge graph builder
    └── launch_dashboard.py             # Interactive web dashboard
```

Based on how Chromium structures AI-assisted development at scale — layered composable prompts, on-demand skills, Agentic RAG, and eval-driven quality.

### 2. Codebase Analysis Pipeline

A 5-phase Python pipeline that analyzes any codebase and produces structured knowledge:

| Phase | Script | Output |
|-------|--------|--------|
| **Context** | `generate_context.py` | Build commands, doc routes, debug patterns, framework detection |
| **Scan** | `scan_project.py` | File inventory, language detection, import maps |
| **Analyze** | `analyze_architecture.py` | Architecture layers (API, Service, Data, UI, etc.) |
| **Graph** | `build_graph.py` | Knowledge graph with nodes, edges, layers, and guided tour |
| **Dashboard** | `launch_dashboard.py` | Interactive web dashboard for exploration |

The context file (`.understand/context.md`) is specifically designed to be read by an LLM to auto-customize all the AI Coding templates with project-specific build commands, doc routes, and debug patterns.

> **Note:** `generate_context.py` runs the scan phase internally. Architecture analysis (`analyze_architecture.py`) is a separate step — run it after the context phase to get layer detection.

### How the Two Features Connect

This is the key insight: **the analysis pipeline feeds the infrastructure**.

```
init_ai_coding.py          generate_context.py
       │                         │
       ▼                         ▼
  agents/ templates          .understand/context.md
  (generic placeholders)     (project-specific: build cmds, frameworks, doc routes)
       │                         │
       └───────── LLM reads ──────┘
                    │
                    ▼
         Customized templates with
         YOUR project's conventions
```

1. Run `init_ai_coding.py` → scaffolds `agents/` with generic templates
2. Run `generate_context.py` → analyzes your codebase → produces `context.md`
3. An LLM reads `context.md` → auto-customizes `agents/prompts/common.md`, `agents/prompts/templates/default.md`, `agents/prompts/knowledge_base.md` with **your project's** build commands, framework patterns, and doc routes

## Quick Start

### One-Liner Install

```bash
# Download and install (Unix/macOS)
curl -fsSL https://raw.githubusercontent.com/yeshao/repo-init/main/scripts/install.sh | bash

# Or clone and install manually
git clone https://github.com/yeshao/repo-init.git
cd repo-init && bash scripts/install.sh
```

### Manual Install

```bash
# Install the skill (for OpenCode / compatible agents)
cp -r repo-init ~/.config/opencode/skills/repo-init
```

### Initialize a Repository

```bash
# Scaffold AI infrastructure
python3 scripts/init_ai_coding.py --dir /path/to/my-project --project-name "My Project"

# Preview before writing
python3 scripts/init_ai_coding.py --dir /path/to/my-project --dry-run

# Analyze the codebase
cd /path/to/my-project
python3 scripts/understand/generate_context.py .        # context + scan phases
cat .understand/context.md
python3 scripts/understand/analyze_architecture.py .      # architecture layer detection
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json
python3 scripts/understand/launch_dashboard.py . --port 3000
```

## What Gets Detected Automatically

The `generate_context.py` script (pure Python, no LLM needed) detects:

- **Build system** — 16 build tools (Cargo, npm, Go, Python, Ruby, Java, Swift, CMake, etc.) with correct build/test/lint/check commands
- **Frameworks** — 13 frameworks (React, Vue, Django, Flask, Rails, Spring, FastAPI, Express, Next.js, Docker, Terraform, etc.)
- **Documentation structure** — Categorizes docs into API reference, architecture, deployment, testing, security, troubleshooting
- **Language-specific patterns** — Common errors and debugging routes for 10 languages (Rust, Python, JavaScript, TypeScript, Go, Java, Ruby, PHP, C, C++)
- **Architecture layers** — Directory-based detection of API, Service, Data, UI, Middleware, Infrastructure layers

### Try It Now

```bash
# Clone and preview (safe — no files written to your target)
git clone https://github.com/yeshao/repo-init.git
cd repo-init
python3 scripts/init_ai_coding.py --dir /tmp/test-init --project-name "Test" --dry-run
```

## Requirements

- Python 3.9+
- No external dependencies — all scripts use only the standard library

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- **[Chromium](https://chromium.googlesource.com/chromium/src/+/main/agents/)** — for the AI Coding infrastructure design: layered prompts, skills system, knowledge base routing, eval suites, and the philosophy that "AI is a tool, not an author."
- **[Understand-Anything](https://github.com/Lum1104/Understand-Anything)** by [@Lum1104](https://github.com/Lum1104) — for the codebase analysis pipeline architecture: project scanning, architecture layer detection, knowledge graph generation, and guided onboarding tours.

## License

MIT
