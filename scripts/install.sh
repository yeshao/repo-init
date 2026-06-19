#!/usr/bin/env bash
#
# install.sh — Install repo-init as an OpenCode skill
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/yeshao/repo-init/main/scripts/install.sh | bash
#   git clone https://github.com/yeshao/repo-init.git && cd repo-init && bash scripts/install.sh
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/yeshao/repo-init.git"
SKILL_NAME="repo-init"

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin) ;;
    Linux)  ;;
    *)      echo "⚠  Unknown OS: $OS — proceeding anyway";;
esac

# ---------------------------------------------------------------------------
# Determine install source
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# If running from a cloned repo, use it directly; otherwise clone
if [ -f "$PROJECT_ROOT/scripts/init_ai_coding.py" ]; then
    SOURCE_DIR="$PROJECT_ROOT"
    echo "📦 Installing from local clone: $SOURCE_DIR"
else
    # Temp clone
    TMP_DIR="$(mktemp -d)"
    echo "📦 Cloning $REPO_URL..."
    git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo-init"
    SOURCE_DIR="$TMP_DIR/repo-init"
fi

# ---------------------------------------------------------------------------
# Detect OpenCode / agent-compatible skill directories
# ---------------------------------------------------------------------------
INSTALL_TARGETS=()

# OpenCode
OPENCODE_GLOBAL="$HOME/.config/opencode/skills"
OPENCODE_LOCAL=".opencode/skills"

# Agent-compatible (generic)
AGENTS_GLOBAL="$HOME/.agents/skills"
AGENTS_LOCAL=".agents/skills"

# Offer choices
echo ""
echo "Where would you like to install the repo-init skill?"
echo ""

OPTIONS=()
INDEX=1

# Check which directories exist or are creatable
if [ -d "$OPENCODE_GLOBAL" ] || [ -d "$HOME/.config/opencode" ]; then
    OPTIONS+=("$OPENCODE_GLOBAL/$SKILL_NAME" "OpenCode (global)")
    echo "  $INDEX) OpenCode global:  $OPENCODE_GLOBAL/$SKILL_NAME"
    INDEX=$((INDEX + 1))
fi

if [ -d ".opencode" ] || [ -n "${OPENCODE_INSTALL:-}" ]; then
    OPTIONS+=("$OPENCODE_LOCAL/$SKILL_NAME" "OpenCode (project-local)")
    echo "  $INDEX) OpenCode project: ./$OPENCODE_LOCAL/$SKILL_NAME"
    INDEX=$((INDEX + 1))
fi

if [ -d "$AGENTS_GLOBAL" ]; then
    OPTIONS+=("$AGENTS_GLOBAL/$SKILL_NAME" "Agents (global)")
    echo "  $INDEX) Agents global:    $AGENTS_GLOBAL/$SKILL_NAME"
    INDEX=$((INDEX + 1))
fi

if [ -d ".agents" ] || [ -n "${AGENTS_INSTALL:-}" ]; then
    OPTIONS+=("$AGENTS_LOCAL/$SKILL_NAME" "Agents (project-local)")
    echo "  $INDEX) Agents project:   ./$AGENTS_LOCAL/$SKILL_NAME"
    INDEX=$((INDEX + 1))
fi

# Always offer global paths even if parent doesn't exist yet
if [ ${#OPTIONS[@]} -eq 0 ]; then
    OPTIONS=(
        "$OPENCODE_GLOBAL/$SKILL_NAME"    "OpenCode (global, recommended)"
        "$AGENTS_GLOBAL/$SKILL_NAME"      "Agents (global)"
        "$OPENCODE_LOCAL/$SKILL_NAME"     "OpenCode (project-local)"
        "$AGENTS_LOCAL/$SKILL_NAME"       "Agents (project-local)"
    )
    for i in "${!OPTIONS[@]}"; do
        if [ $((i % 2)) -eq 0 ]; then
            NUM=$((i / 2 + 1))
            echo "  $NUM) ${OPTIONS[$((i + 1))]}: ${OPTIONS[$i]}"
        fi
    done
fi

echo ""

# Auto-detect: if only OpenCode paths exist, use global
if [ ${#OPTIONS[@]} -eq 2 ]; then
    CHOICE=1
    echo "→ Auto-selecting: ${OPTIONS[1]}"
else
    read -rp "Enter choice (1-${#OPTIONS[@]}): " CHOICE
fi

# Resolve choice to path
TARGET_PATH="${OPTIONS[$(( (CHOICE - 1) * 2 ))]}"
TARGET_LABEL="${OPTIONS[$(( (CHOICE - 1) * 2 + 1 ))]}"

echo ""
echo "→ Installing to: $TARGET_PATH ($TARGET_LABEL)"

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
# Copy the skill (SKILL.md + scripts/ + agents-understand/ + references/ + evals/)
mkdir -p "$TARGET_PATH"

# Core files
cp "$SOURCE_DIR/SKILL.md" "$TARGET_PATH/SKILL.md"

# Scripts
if [ -d "$SOURCE_DIR/scripts" ]; then
    cp -r "$SOURCE_DIR/scripts" "$TARGET_PATH/scripts"
fi

# Agents-understand (understand skill + dashboard skill + analysis scripts)
if [ -d "$SOURCE_DIR/agents-understand" ]; then
    mkdir -p "$TARGET_PATH/skills"
    cp -r "$SOURCE_DIR/agents-understand/skills/understand" "$TARGET_PATH/skills/understand"
    cp -r "$SOURCE_DIR/agents-understand/skills/understand-dashboard" "$TARGET_PATH/skills/understand-dashboard"
    mkdir -p "$TARGET_PATH/scripts/understand"
    cp "$SOURCE_DIR/agents-understand/scripts/understand/"*.py "$TARGET_PATH/scripts/understand/"
fi

# References
if [ -d "$SOURCE_DIR/references" ]; then
    cp -r "$SOURCE_DIR/references" "$TARGET_PATH/references"
fi

# Evals
if [ -d "$SOURCE_DIR/evals" ]; then
    cp -r "$SOURCE_DIR/evals" "$TARGET_PATH/evals"
fi

# ---------------------------------------------------------------------------
# Post-install
# ---------------------------------------------------------------------------
echo ""
echo "✅ repo-init installed successfully!"
echo ""
echo "Quick start:"
echo "  1. Initialize a repository:"
echo "     python3 $TARGET_PATH/scripts/init_ai_coding.py --dir /path/to/my-project --project-name \"My Project\""
echo ""
echo "  2. Preview first (safe):"
echo "     python3 $TARGET_PATH/scripts/init_ai_coding.py --dir /path/to/my-project --dry-run"
echo ""
echo "  3. Analyze a codebase:"
echo "     python3 $TARGET_PATH/scripts/understand/generate_context.py /path/to/my-project"
echo ""
echo "Documentation: $TARGET_PATH/references/"
echo "Evals:          $TARGET_PATH/evals/"
