---
name: repo-init
description: |
  Scaffold a complete AI Coding infrastructure (prompts, skills, knowledge base, eval
  suite) and a codebase analysis pipeline (scanner, architecture analyzer, knowledge
  graph, dashboard) into any repository. Use this whenever the user wants to set up AI
  coding infrastructure, create an agents/ directory, scaffold AI agent prompts and skills,
  add AI development guardrails, set up knowledge base routing, create eval test suites,
  generate platform templates, analyze a codebase, build a knowledge graph, create
  onboarding tours, launch a project dashboard, or understand a project structure.
  Triggers on: "AI coding setup", "agents directory", "scaffold AI infrastructure",
  "understand this codebase", "analyze project", "knowledge graph", "onboarding tour",
  "project dashboard", "AI agent setup", "prompt engineering", "AI guardrails".
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: automation
---

# repo-init

Scaffold a production-ready **AI Coding infrastructure** for any repository, inspired by Chromium's `agents/` directory and Understand-Anything's codebase analysis pipeline.

## When to Use

Use this skill when the user wants to:

- Initialize AI coding infrastructure for a repository
- Set up an `agents/` directory with prompts, skills, and knowledge base
- Create reusable AI agent prompt templates and skill modules
- Add AI-assisted development guardrails to a project
- Set up document routing / Agentic RAG for their AI agent
- Create evaluation test suites for AI behavior regression testing
- Scaffold platform-specific AI templates (desktop, web, mobile, backend)
- **Analyze and understand a codebase** (project scanning, architecture layers, knowledge graph)
- **Generate guided onboarding tours** for new team members
- **Launch an interactive dashboard** to explore project structure

**Trigger phrases include**: "AI coding setup", "agents directory", "AI agent scaffolding", "prompt engineering infrastructure", "AI skills for my team", "Chromium-style AI setup", "AI development guardrails", "understand this codebase", "analyze project structure", "knowledge graph", "onboarding tour", "project dashboard".

## How to Use

### Basic

```bash
python3 scripts/init_ai_coding.py --dir /path/to/repo --project-name "My Project"
```

### Preview First

```bash
python3 scripts/init_ai_coding.py --dir /path/to/repo --dry-run
```

### Overwrite Existing

```bash
python3 scripts/init_ai_coding.py --dir /path/to/repo --force
```

## What Gets Created

```
repo-root/
├── agents/
│   ├── ai_policy.md                    # AI usage policy & human accountability rules
│   ├── prompts/
│   │   ├── common.minimal.md          # Layer 1: Core build/test/coding instructions
│   │   ├── common.md                  # Layer 2: Standard 8-step workflow
│   │   ├── knowledge_base.md          # Layer 3: Agentic RAG document routing table
│   │   ├── templates/
│   │   │   ├── default.md             # Platform-agnostic template
│   │   │   └── README.md              # Guide for platform-specific templates
│   │   ├── eval/
│   │   │   ├── README.md              # Evaluation test suite documentation
│   │   │   └── example/               # Example eval case
│   │   └── commands/
│   │       └── README.md              # Task prompt / shortcut command templates
│   ├── skills/
│   │   ├── README.md                  # Skill creation guide
│   │   ├── example-skill/SKILL.md     # Example skill template
│   │   ├── understand/SKILL.md        # 🔍 Codebase analysis & knowledge graph skill
│   │   └── understand-dashboard/SKILL.md  # 📊 Interactive dashboard launcher
│   ├── extensions/
│   │   └── README.md                  # MCP extensions placeholder
│   └── projects/
│       └── README.md                  # Large-scale project templates placeholder
└── scripts/
    ├── init_ai_coding.py              # Main scaffolding script
    ├── chromium_docs.py               # Document search tool for Agentic RAG
    └── understand/
        ├── generate_context.py        # 🔑 Analyze codebase → build commands, doc routes, debug patterns
        ├── scan_project.py            # Project file inventory + import map + language detection
        ├── analyze_architecture.py    # Architecture layer detection (API, Service, Data, UI, etc.)
        ├── build_graph.py             # Knowledge graph builder (nodes, edges, layers, tour)
        └── launch_dashboard.py        # Interactive web dashboard for graph exploration
```

> **Tip**: Read `references/structure.md` for detailed descriptions of every file and directory.

## Examples

### Example 1: New Repository

**Input**:
```bash
mkdir my-project && cd my-project
python3 scripts/init_ai_coding.py --dir . --project-name "My Project"
```

**Output**:
```
  ✓  CREATED: agents/ai_policy.md
  ✓  CREATED: agents/prompts/common.minimal.md
  ✓  CREATED: agents/prompts/common.md
  ✓  CREATED: agents/prompts/knowledge_base.md
  ✓  CREATED: agents/prompts/templates/default.md
  ✓  CREATED: agents/prompts/templates/README.md
  ✓  CREATED: agents/prompts/eval/README.md
  ✓  CREATED: agents/prompts/eval/example/prompt.md
  ✓  CREATED: agents/prompts/eval/example/eval.md
  ✓  CREATED: agents/prompts/commands/README.md
  ✓  CREATED: agents/skills/README.md
  ✓  CREATED: agents/skills/example-skill/SKILL.md
  ✓  COPIED: agents/skills/understand/
  ✓  COPIED: agents/skills/understand-dashboard/
  ✓  COPIED: scripts/understand/
  ✓  CREATED: agents/extensions/README.md
  ✓  CREATED: agents/projects/README.md

  Summary: 14 created, 3 copied

  Validation:
    ✓  agents/ai_policy.md
    ✓  agents/prompts/common.minimal.md
    ✓  agents/prompts/common.md
    ✓  agents/prompts/knowledge_base.md
    ⚠  agents/skills/example-skill/SKILL.md is still a placeholder — replace or remove

    All critical files present. Ready for customization.
```

### Example 2: Analyze the Initialized Repository

After initialization, run the understand pipeline to analyze the codebase and get
suggested template customizations:

```bash
# Analyze the project — detects build commands, doc structure, frameworks, debug routes
python3 scripts/understand/generate_context.py .

# Read the generated context for suggested template customizations
cat .understand/context.md

# Build the full knowledge graph + guided tour
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json

# Launch the interactive dashboard
python3 scripts/understand/launch_dashboard.py . --port 3000
```

## After Initialization

After running the script, follow these steps:

1. **Analyze the codebase**: `python3 scripts/understand/generate_context.py .`
2. **Read the context**: `cat .understand/context.md` — this contains suggested build commands, doc routes, and debug patterns specific to your project
3. **Customize templates** using the suggestions from context.md:
   - Edit `agents/ai_policy.md` with your team's AI rules
   - Copy build/test commands from context into `agents/prompts/common.minimal.md`
   - Add doc routing rules from context into `agents/prompts/knowledge_base.md`
   - Fill in build targets from context into `agents/prompts/templates/default.md`
4. Replace `agents/skills/example-skill/` with real skills for your domain
5. Build the knowledge graph: `python3 scripts/understand/build_graph.py .`

See `references/customization-guide.md` for detailed instructions.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Editing generated files before reading them | You'll miss important context and design rationale | Read each file first, then customize |
| Putting all prompts in one file | Defeats layered composition; can't reuse or swap layers | Keep layers separate, compose with `@` references |
| Leaving example-skill in production | It's a placeholder, not a real skill | Replace with real skills or delete the directory |
| Skipping `ai_policy.md` customization | Default rules are Chromium-specific | Edit consequences and rules for your team |
| Not building the knowledge base | AI will rely on training data, not your actual docs | Add routing rules for your key doc paths |
| Running without `--dry-run` first | Can't see what will change | Always preview first on existing repos |
| Not running the understand pipeline | Miss out on codebase analysis, architecture docs, and onboarding tours | Run the 4-phase pipeline after init |

## Design Principles

- **Layered Prompts**: Small, composable prompt files instead of one monolithic prompt
- **Skills on Demand**: Expert modules activate only when relevant to the current task
- **Agentic RAG**: AI consults authoritative docs before answering — not just training data
- **Human Accountability**: AI assists; humans are responsible for every line of code
- **Eval-Driven Quality**: Regression tests for AI behavior, not just code
- **Codebase Understanding**: Every repo gets a built-in analysis pipeline — scan, analyze, graph, tour

See `references/design-principles.md` for the full rationale.

## Validation Checklist

After initialization, verify:

- [ ] `init_ai_coding.py` ran without errors
- [ ] All 14 template files created in `agents/`
- [ ] `agents/skills/understand/` and `agents/skills/understand-dashboard/` copied
- [ ] `scripts/understand/` directory copied with all 5 scripts
- [ ] `generate_context.py` runs successfully on the project
- [ ] `build_graph.py` produces a valid knowledge-graph.json
- [ ] `agents/ai_policy.md` customized for your team
- [ ] `agents/prompts/common.minimal.md` has project-specific build/test commands
- [ ] `agents/prompts/knowledge_base.md` routes to real docs in your repo
- [ ] `agents/prompts/templates/default.md` has valid build targets
- [ ] `agents/skills/example-skill/` replaced with real skills or removed
- [ ] `agents/prompts/eval/` has at least one real eval case for your domain

## Installing This Skill

To make this skill available in OpenCode, place it in your skills directory:

```bash
# Global installation (available for all projects)
cp -r /path/to/repo-init-skill ~/.config/opencode/skills/repo-init

# Project-local installation
cp -r /path/to/repo-init-skill .opencode/skills/repo-init
```

OpenCode discovers skills from:
- `~/.config/opencode/skills/<name>/SKILL.md` (global)
- `.opencode/skills/<name>/SKILL.md` (project-local)
- `~/.agents/skills/<name>/SKILL.md` (global, agent-compatible)
- `.agents/skills/<name>/SKILL.md` (project-local, agent-compatible)
