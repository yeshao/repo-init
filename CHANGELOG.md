# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2025-01-XX

### Added
- **AI Coding Infrastructure**: `init_ai_coding.py` scaffolds a Chromium-style `agents/` directory with layered prompts, skills, knowledge base, eval test suites, and platform templates
- **Codebase Analysis Pipeline**: 4-phase Python pipeline (`generate_context.py`, `scan_project.py`, `analyze_architecture.py`, `build_graph.py`, `launch_dashboard.py`)
- **Knowledge Graph**: Interactive web dashboard for codebase exploration
- **Agentic RAG**: Document routing table + search tool for context-aware AI responses
- **One-liner Installer**: `scripts/install.sh` with auto-detection for OpenCode and agent-compatible skill directories
- **CI**: GitHub Actions workflow testing dry-run, full init, skip-existing, force-overwrite, pipeline execution, and knowledge graph generation
- **Contributing Guide**: `CONTRIBUTING.md` with issue/PR guidelines and code conventions
- **Eval Suite**: JSON-defined test cases for automated regression testing

### Key Features
- `--dry-run` mode for safe previewing
- `--force` mode for overwriting existing files
- Zero external dependencies (standard library only)
- Python 3.9+ support
