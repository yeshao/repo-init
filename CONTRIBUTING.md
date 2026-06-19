# Contributing to repo-init

Contributions are welcome! This document outlines how to get started.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion, please open an issue with:

- A clear description of the problem or idea
- Steps to reproduce (for bugs)
- Your Python version and OS

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-change`
3. Make your changes
4. Run the evals to verify nothing broke (see below)
5. Push and open a PR with a clear description

### Running Evals

The eval suite (`evals/evals.json`) contains test cases that verify core functionality. To run them:

```bash
# Install to a temp location
python3 scripts/init_ai_coding.py --dir /tmp/test-evals --project-name "Evals Test"

# Verify all expected files exist
test -f /tmp/test-evals/agents/ai_policy.md && echo "PASS: ai_policy.md"
test -f /tmp/test-evals/agents/prompts/common.minimal.md && echo "PASS: common.minimal.md"
test -f /tmp/test-evals/agents/prompts/common.md && echo "PASS: common.md"
test -f /tmp/test-evals/agents/skills/understand/SKILL.md && echo "PASS: understand skill"
test -f /tmp/test-evals/scripts/understand/generate_context.py && echo "PASS: generate_context.py"

# Test the understand pipeline
python3 scripts/understand/generate_context.py /tmp/test-evals
test -f /tmp/test-evals/.understand/context.md && echo "PASS: context.md generated"

# Cleanup
rm -rf /tmp/test-evals
```

## Code Conventions

- **Python**: Follow PEP 8. Use type hints. No external dependencies.
- **Shell**: Use `set -euo pipefail`. Quote all variables.
- **Markdown**: Use `-` for unordered tables, `|` for ordered. Code blocks must specify language.
- **Templates**: Keep placeholder text in `{curly braces}` so it's easy to find-and-replace.

## Project Structure

```
repo-init/
├── SKILL.md                  # Skill definition (for AI agents)
├── README.md                 # User-facing documentation
├── scripts/
│   ├── init_ai_coding.py     # Main scaffolding script
│   ├── install.sh            # One-liner installer
│   ├── chromium_docs.py      # Document search tool
│   └── understand/           # Analysis pipeline scripts
├── agents-understand/        # Template source (copied during init)
│   ├── scripts/understand/   # Python analysis scripts
│   └── skills/               # Understand + dashboard skills
├── references/               # Extended documentation
├── evals/                    # Eval test cases
└── .github/workflows/        # CI configuration
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
