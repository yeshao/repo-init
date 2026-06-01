# Reference: Full File Structure

Detailed description of every file and directory created by `init_ai_coding.py`.

## Table of Contents

- [agents/ai_policy.md](#agentsai_policymd)
- [agents/prompts/common.minimal.md](#agentspromptscommonminimalmd)
- [agents/prompts/common.md](#agentspromptscommonmd)
- [agents/prompts/knowledge_base.md](#agentspromptsknowledge_basemd)
- [agents/prompts/templates/](#agentstemplates)
- [agents/prompts/eval/](#agentseval)
- [agents/prompts/commands/](#agentscommands)
- [agents/skills/](#agentsskills)
- [agents/extensions/](#agentsextensions)
- [agents/projects/](#agentsprojects)
- [scripts/chromium_docs.py](#scriptschromium_docspy)

---

## agents/ai_policy.md

The **AI usage policy** defining the boundary between human and AI responsibility.
Based on Chromium's `ai_policy.md`. Contains:

- Core principle: AI is a tool, not an author
- Rules table: self-review obligation, original work declaration, human-to-human communication
- Recommended practices for documenting AI usage
- Scope declaration

**Customization**: Edit the rules and consequences to match your team's policies.

## agents/prompts/common.minimal.md

**Layer 1** — The foundational instruction layer shared by all developers.
Non-negotiable basics that every AI session needs:

- Build: Always confirm build directory and target before building
- Test: Use the project's standard test runner, don't manually build first
- Coding: Stay on task, comments explain "why" not "what"
- Pre-Submit: Run formatters and linters, only fix issues you introduced

**Customization**: Replace generic build/test commands with your project's actual commands.

## agents/prompts/common.md

**Layer 2** — The standard 8-step workflow for all code editing tasks:

1. **Deep Code Understanding** (mandatory, never skip)
   - Locate core files → Complete audit → State understanding → Avoid anti-patterns
2. **Write Code** — Only what the task requires
3. **Write / Update Tests** — Prefer existing test files
4. **Build** — Build affected targets only
5. **Fix Build Errors** — Read, understand, never speculate
6. **Run Tests** — Run affected + broader suite
7. **Fix Test Failures** — Understand why before fixing
8. **Iterate** — Loop steps 4-7 until all green

**Customization**: Adjust the number of steps and details to match your workflow.

## agents/prompts/knowledge_base.md

**Layer 3** — The Agentic RAG routing table. A static `if-then` rule engine that
maps detected task features to documentation paths:

- **Programming Pattern Routing**: IPC → read IPC docs, async → read threading docs, etc.
- **Feature Development Routing**: prefs → read prefs docs, metrics → read metrics docs, etc.
- **Debugging Routing**: header not found → check deps/paths/build files, linker errors → check deps/visibility, etc.

**Customization**: Add your project-specific routing rules. The more specific, the better.

## agents/prompts/templates/

Platform-specific context files. The `default.md` template includes:

- Prerequisite reading list
- Build targets
- Test execution commands

Create additional templates for each platform (`desktop.md`, `web.md`, `mobile.md`, etc.).

## agents/prompts/eval/

AI Agent regression test suite. Each eval case is a subdirectory with:

- `prompt.md` — Simulated user request
- `eval.md` — Expected outcomes and assertions

Suggested cases: `add-test-coverage`, `fix-broken-test`, `generate-change-description`,
`code-refactor`, `feature-flag`.

## agents/prompts/commands/

Task prompts (shortcut commands) for common operations. Each is a pre-written prompt
that encapsulates a complete workflow. Suggested commands:

| Command | Purpose |
|---------|---------|
| `fix-review-comments` | Address code review feedback |
| `gen-tests` | Generate unit tests for changed code |
| `change-description` | Generate change description from diff |
| `pre-upload-checklist` | Run pre-submission checks |
| `disable-test` | Safely disable a failing test |

## agents/skills/

On-demand expert modules. Each skill is a directory with a `SKILL.md` that activates
only when the task matches the skill's domain.

Suggested skills: `feature-flag`, `test-generation`, `code-refactor`, `metrics`,
`documentation`, `debugging`, `security-review`, `performance`.

## agents/extensions/

MCP (Model Context Protocol) extensions for external tool capabilities:
code search, documentation search, build info, issue tracker, git history.

## agents/projects/

Large-scale AI-driven engineering initiatives. Unlike skills (single tasks),
projects have long-running goals with full project structures including SKILL.md,
reference docs, Python scripts, and automation pipelines.

## scripts/chromium_docs.py

Document search tool implementing Agentic RAG. Builds a 3-index search system:

- `doc_index.json` — Full document metadata (title, summary, content, keywords)
- `keyword_index.json` — Inverted index for O(1) keyword lookup
- `category_index.json` — Category-based document grouping

Usage:
```bash
python3 scripts/chromium_docs.py --build-index --root /path/to/repo
python3 scripts/chromium_docs.py "mojo ipc"
python3 scripts/chromium_docs.py "threading" --category threading --top-k 3
```
