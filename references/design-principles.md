# Reference: Design Principles

The rationale behind the AI Coding infrastructure design, derived from Chromium's approach.

## Layered Prompts (Not Monolithic)

**Problem**: A single massive prompt file is hard to maintain, causes context bloat,
and makes it impossible to compose different instructions for different scenarios.

**Solution**: Four layers that compose together:

```
Layer 1: common.minimal.md     ← Always loaded, non-negotiable basics
Layer 2: common.md             ← Always loaded, standard workflow
Layer 3: templates/<platform>.md ← Loaded per platform
Layer 4: commands/<task>.md    ← Loaded per task
```

Each layer is small, focused, and independently testable. Developers compose their
configuration by referencing the layers they need.

## Skills on Demand (Not Always Loaded)

**Problem**: Loading all expert knowledge for every task wastes context and can
cause the AI to confuse domains.

**Solution**: Skills are directories with `SKILL.md` files that the AI agent loads
only when it determines the task matches the skill's domain. This is the same
pattern as OpenCode's native skill system.

Key distinction:
- **Prompts** = always loaded, define how the AI behaves
- **Skills** = loaded on demand, define how the AI handles specific domains

## Agentic RAG (Not Passive Retrieval)

**Problem**: AI models answer from training data, which may be outdated or
incorrect for your specific codebase.

**Solution**: Three-layer knowledge enhancement:

1. **Static routing table** (`knowledge_base.md`): `if-then` rules mapping task
   features to documentation paths. Fast, deterministic, no embedding needed.
2. **Dynamic document search** (`chromium_docs.py`): Weighted keyword search across
   all markdown files. Used when static routing doesn't cover the query.
3. **MCP extensions**: External knowledge sources for real-time information.

Core principle: **"Consult, then Answer"** — the AI must read authoritative docs
before answering, never rely solely on training data.

## Human Accountability (Not AI Authority)

**Problem**: AI-generated code can be subtly wrong, insecure, or misaligned with
project conventions. If the AI is the "author," quality degrades.

**Solution**: The `ai_policy.md` establishes clear rules:
- The human developer is always the author and is fully responsible
- AI is a tool, not a co-author
- Submitting code you don't understand has consequences
- All AI usage should be documented in change descriptions

## Eval-Driven Quality (Not Hope-Based)

**Problem**: When you modify prompts, you don't know if the AI's behavior has
regressed until a real task fails.

**Solution**: An evaluation test suite (`agents/prompts/eval/`) with:
- Realistic task prompts
- Expected outcome specifications
- Automated assertions (files changed, content checks, tool calls)

Run evals after every prompt modification to catch regressions early.
