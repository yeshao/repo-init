# Reference: Customization Guide

Step-by-step guide for customizing each generated file after initialization.

## Table of Contents

- [1. agents/ai_policy.md](#1-agentsai_policymd)
- [2. agents/prompts/common.minimal.md](#2-agentspromptscommonminimalmd)
- [3. agents/prompts/common.md](#3-agentspromptscommonmd)
- [4. agents/prompts/knowledge_base.md](#4-agentspromptsknowledge_basemd)
- [5. agents/prompts/templates/default.md](#5-agentspromptsdefaultmd)
- [6. agents/skills/example-skill/](#6-agentsexample-skill)
- [7. agents/prompts/eval/](#7-agentseval)
- [8. scripts/chromium_docs.py](#8-scriptschromium_docspy)

---

## 1. agents/ai_policy.md

**Must customize** — The default rules are Chromium-specific.

- Replace "Committer" with your team's role names
- Adjust consequences to match your team's enforcement policy
- Add project-specific rules (e.g., "All AI-generated code must include a `Generated-AI` tag in the commit message")

## 2. agents/prompts/common.minimal.md

**Must customize** — Contains generic build/test commands.

Replace the generic examples with your actual commands:

```markdown
## Build
- **Always confirm the build directory and target before building.**
- For this project: `bazel build //src/...` or `cargo build --release`
- Build output goes to `bazel-out/` or `target/`

## Test
- Use `bazel test //src/...` or `cargo test`
- For specific tests: `cargo test test_name_filter`
```

Add project-specific coding conventions:

```markdown
## Coding
- Use `snake_case` for functions, `PascalCase` for types
- All public APIs must have doc comments
- Error handling: use `thiserror` for library code, `anyhow` for application code
```

## 3. agents/prompts/common.md

**Should customize** — The 8-step workflow is solid but may need tuning.

- If your project doesn't have a separate build system, merge steps 4 and 6
- If you use a different test framework, update step 6
- Add project-specific anti-patterns to step 1d

## 4. agents/prompts/knowledge_base.md

**Must customize** — The default routes are generic examples.

Add your actual documentation paths:

```markdown
| Detected Feature | Action |
|-----------------|--------|
| Involves database queries | Read `docs/database/schema.md` first |
| Involves API endpoints | Read `docs/api/rest.md` first |
| Involves authentication | Read `docs/security/auth.md` first |
| Modifies `src/engine/` code | Read `docs/architecture/engine.md` first |
```

Add debugging routes for your common error patterns:

```markdown
| Error Type | Action |
|-----------|--------|
| "trait not implemented" | 1. Check trait bounds 2. Check feature flags 3. Verify type implements required traits |
| "lifetime mismatch" | 1. Check ownership flow 2. Verify lifetime annotations 3. Consider `Arc<>` for shared ownership |
```

## 5. agents/prompts/templates/default.md

**Must customize** — Contains placeholder build targets.

Replace with your actual targets:

```markdown
## Build Targets
- **Main target**: `bazel build //src/my_project`
- **Test target**: `bazel test //src/...`
- **Lint target**: `bazel run //:clippy`

## Test Execution
- Run all tests: `bazel test //src/...`
- Run specific test: `bazel test //src/module:test_name`
- Run with coverage: `bazel coverage //src/...`
```

## 6. agents/skills/example-skill/

**Must replace or delete** — This is a placeholder.

To create a real skill:

```bash
rm -rf agents/skills/example-skill
mkdir -p agents/skills/feature-flag
```

Then create `agents/skills/feature-flag/SKILL.md` with:
- Description of what the skill does
- Activation conditions (when to load)
- Step-by-step checklist
- Anti-patterns to avoid

## 7. agents/prompts/eval/

**Should build up** — Start with 2-3 core eval cases.

Good first eval cases:

1. **add-test-coverage** — AI adds unit tests for a specific function
2. **fix-broken-test** — AI diagnoses and fixes a failing test
3. **code-refactor** — AI safely refactors a specific pattern

Each eval case needs:
- `prompt.md`: A realistic user request
- `eval.md`: Expected files changed, content assertions, process assertions

## 8. scripts/chromium_docs.py

**Optional setup** — Build the document index:

```bash
python3 scripts/chromium_docs.py --build-index --root /path/to/repo
```

The index is cached at `~/.cache/ai-coding-docs/`. Rebuild when docs change.
