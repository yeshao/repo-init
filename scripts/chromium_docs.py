#!/usr/bin/env python3
"""
chromium_docs.py — Document search tool for Agentic RAG.

This tool helps AI agents find relevant documentation in the repository
by searching through markdown files with weighted scoring.

Usage:
    # Build the index (first time, ~30s for large repos):
    python3 chromium_docs.py --build-index [--root /path/to/repo]

    # Search:
    python3 chromium_docs.py "mojo ipc"
    python3 chromium_docs.py "threading and tasks"

    # Search with category filter:
    python3 chromium_docs.py "network" --category network
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INDEX_DIR = Path.home() / ".cache" / "ai-coding-docs"
INDEX_FILES = {
    "doc": INDEX_DIR / "doc_index.json",
    "keyword": INDEX_DIR / "keyword_index.json",
    "category": INDEX_DIR / "category_index.json",
}

# File patterns to index
DOC_PATTERNS = [
    "docs/**/*.md",
    "*/README.md",
    "*/docs/*.md",
    "agents/**/*.md",
]

# Categories (extend as needed)
CATEGORIES = {
    "ui": ["ui", "view", "widget", "layout", "render", "css", "html"],
    "network": ["network", "http", "request", "response", "url", "fetch", "api"],
    "threading": ["thread", "task", "async", "callback", "promise", "future"],
    "security": ["security", "permission", "sandbox", "cors", "csrf", "auth"],
    "testing": ["test", "mock", "fixture", "assert", "coverage"],
    "build": ["build", "compile", "link", "dependency", "package", "cargo", "cmake", "bazel"],
    "performance": ["performance", "perf", "trace", "profile", "benchmark", "optimize"],
    "storage": ["storage", "database", "cache", "file", "disk", "persist"],
    "ipc": ["ipc", "mojo", "message", "port", "channel", "rpc"],
    "metrics": ["metric", "analytics", "histogram", "telemetry", "uma", "ukm"],
    "architecture": ["architecture", "design", "pattern", "structure", "overview"],
    "mobile": ["mobile", "android", "ios", "swift", "kotlin"],
    "desktop": ["desktop", "windows", "mac", "linux", "gtk", "cocoa"],
}

# Search weights
WEIGHTS = {
    "title": 4.0,
    "path": 2.5,
    "keyword": 2.0,
    "content": 1.0,
    "content_exact": 1.5,
    "recent_bonus": 0.5,
}


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def find_doc_files(root: Path) -> list[Path]:
    """Find all markdown files matching the configured patterns."""
    files = []
    for pattern in DOC_PATTERNS:
        files.extend(root.glob(pattern))
    # Deduplicate and filter
    seen = set()
    result = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen and f.is_file():
            seen.add(resolved)
            result.append(f)
    return result


def categorize(path: Path, content: str) -> list[str]:
    """Determine the category of a document based on path and content."""
    text = (str(path) + " " + content[:500]).lower()
    cats = []
    for cat, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            cats.append(cat)
    return cats if cats else ["general"]


def extract_keywords(content: str) -> list[str]:
    """Extract meaningful keywords from content."""
    # Find CamelCase words (likely code identifiers)
    camel = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', content)
    # Find ALL_CAPS identifiers
    caps = re.findall(r'\b[A-Z]{2,}\b', content)
    # Find Chromium/project-specific terms
    technical = re.findall(r'\b[a-z]+(?:_[a-z]+){2,}\b', content)
    # Combine and deduplicate
    keywords = list(set(w.lower() for w in camel + caps + technical))
    return keywords[:20]


def parse_document(path: Path, root: Path) -> dict:
    """Parse a markdown file and extract metadata."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    # Extract title (first H1 or H2)
    title = ""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break
        elif line.startswith("## ") and not title:
            title = line[3:].strip()

    # Extract summary (first ~300 chars of meaningful text)
    text_lines = [
        l.strip() for l in content.split("\n")
        if l.strip() and not l.startswith("#")
    ]
    summary = " ".join(text_lines[:5])[:300]

    # Relative path as string
    try:
        rel_path = str(path.relative_to(root))
    except ValueError:
        rel_path = str(path)

    stat = path.stat()
    return {
        "path": rel_path,
        "title": title or path.name,
        "summary": summary,
        "content": content[:5000],  # First 5000 chars for search
        "keywords": extract_keywords(content),
        "categories": categorize(path, content),
        "mtime": stat.st_mtime,
        "size": stat.st_size,
    }


def build_index(root: Path) -> dict:
    """Build the full document index."""
    print(f"Scanning {root} for documentation files...", file=sys.stderr)

    files = find_doc_files(root)
    print(f"Found {len(files)} files to index.", file=sys.stderr)

    doc_index = {}
    keyword_index = {}
    category_index = {}
    now = datetime.now().timestamp()

    for i, path in enumerate(files):
        if (i + 1) % 100 == 0:
            print(f"  Indexing {i+1}/{len(files)}...", file=sys.stderr)

        doc = parse_document(path, root)
        if not doc:
            continue

        doc_key = doc["path"]
        doc_index[doc_key] = doc

        # Build keyword index
        for kw in doc.get("keywords", []):
            keyword_index.setdefault(kw, []).append(doc_key)

        # Build category index
        for cat in doc.get("categories", []):
            category_index.setdefault(cat, []).append(doc_key)

    return {
        "doc": doc_index,
        "keyword": keyword_index,
        "category": category_index,
    }


def save_index(index: dict) -> None:
    """Persist the index to disk."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for key, path in INDEX_FILES.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(index[key], f, ensure_ascii=False, indent=2)
    print(f"Index saved to {INDEX_DIR}", file=sys.stderr)


def load_index():
    """Load the index from disk."""
    if not all(p.exists() for p in INDEX_FILES.values()):
        return None
    index = {}
    for key, path in INDEX_FILES.items():
        with open(path, "r", encoding="utf-8") as f:
            index[key] = json.load(f)
    return index


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def score_document(doc: dict, query_terms: list[str], now: float) -> float:
    """Score a document against the query terms."""
    score = 0.0
    title_lower = doc.get("title", "").lower()
    path_lower = doc.get("path", "").lower()
    content_lower = doc.get("content", "").lower()

    for term in query_terms:
        term_lower = term.lower()

        # Title match (highest weight)
        if term_lower in title_lower:
            score += WEIGHTS["title"]

        # Path match
        if term_lower in path_lower:
            score += WEIGHTS["path"]

        # Keyword match
        if term_lower in [k.lower() for k in doc.get("keywords", [])]:
            score += WEIGHTS["keyword"]

        # Content match
        if term_lower in content_lower:
            # Check for exact phrase match
            if len(query_terms) > 1:
                phrase = " ".join(query_terms).lower()
                if phrase in content_lower:
                    score += WEIGHTS["content_exact"] * len(query_terms)
                else:
                    score += WEIGHTS["content"]
            else:
                score += WEIGHTS["content"]

    # Recency bonus (documents modified in the last 90 days)
    mtime = doc.get("mtime", 0)
    if now - mtime < 90 * 86400:
        score += WEIGHTS["recent_bonus"]

    return score


def search(query: str, index: dict, category=None, top_k: int = 5):
    """Search the index for the query."""
    query_terms = query.lower().split()
    now = datetime.now().timestamp()

    # Get candidate set
    if category and category in index.get("category", {}):
        candidates = index["category"][category]
    else:
        # Use keyword index to narrow candidates
        candidate_sets = []
        for term in query_terms:
            if term in index.get("keyword", {}):
                candidate_sets.append(set(index["keyword"][term]))

        if candidate_sets:
            # Union of all keyword matches
            candidates = list(set().union(*candidate_sets))
            # Also include all docs for broader matching
            if len(candidates) < 20:
                candidates = list(index["doc"].keys())
        else:
            candidates = list(index["doc"].keys())

    # Score candidates
    scored = []
    for doc_key in candidates:
        doc = index["doc"].get(doc_key)
        if not doc:
            continue
        score = score_document(doc, query_terms, now)
        if score > 0:
            scored.append((score, doc))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top_k results
    results = []
    for score, doc in scored[:top_k]:
        results.append({
            "score": round(score, 2),
            "path": doc["path"],
            "title": doc["title"],
            "summary": doc["summary"][:200],
            "categories": doc.get("categories", []),
        })
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Document search for Agentic RAG")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--build-index", action="store_true", help="Build the document index")
    parser.add_argument("--root", default=".", help="Repository root directory")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    # Handle build-index
    if args.build_index:
        root = Path(args.root).resolve()
        index = build_index(root)
        save_index(index)
        print(f"Indexed {len(index['doc'])} documents.")
        return

    # Handle search
    query = args.query
    if not query:
        parser.print_help()
        sys.exit(1)

    index = load_index()
    if not index:
        print(
            "Error: No index found. Run `python chromium_docs.py --build-index` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    results = search(query, index, args.category, args.top_k)

    if not results:
        print(f"No results for: {query}")
        return

    print(f"Results for: {query}\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['score']:.1f}] {r['title']}")
        print(f"     Path: {r['path']}")
        print(f"     {r['summary'][:120]}")
        print()


if __name__ == "__main__":
    main()
