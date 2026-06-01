#!/usr/bin/env python3
"""
scan_project.py — Scan a codebase to produce a structured inventory.

Usage:
    python3 scan_project.py <project-root> --output <output-path>

Produces a JSON file with:
    - files: list of {path, language, fileCategory, sizeLines}
    - totalFiles, filteredByIgnore, estimatedComplexity
    - stats: {byCategory, byLanguage}
    - importMap: {file: [imported_files]}
    - name, description, frameworks, languages (from manifests)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Language detection by extension
# ---------------------------------------------------------------------------

LANGUAGE_MAP = {
    ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
    ".mjs": "javascript", ".cjs": "javascript",
    ".py": "python", ".pyw": "python", ".pyi": "python",
    ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".cs": "csharp", ".rb": "rb", ".php": "php",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    ".swift": "swift",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".psm1": "powershell", ".psd1": "powershell",
    ".bat": "batch", ".cmd": "batch",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss", ".sass": "sass",
    ".less": "less",
    ".sql": "sql", ".graphql": "graphql", ".gql": "graphql",
    ".proto": "protobuf", ".prisma": "prisma",
    ".csv": "csv", ".tsv": "tsv",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".jsonc": "json",
    ".toml": "toml", ".xml": "xml", ".xsl": "xml", ".xsd": "xml",
    ".plist": "plist", ".cfg": "cfg", ".ini": "ini", ".env": "env",
    ".properties": "properties", ".gradle": "gradle",
    ".md": "markdown", ".mdx": "mdx", ".rst": "rst", ".txt": "text",
    ".tf": "terraform", ".tfvars": "terraform",
    ".dockerfile": "dockerfile",
}

# Filename-based language detection
FILENAME_LANGUAGE = {
    "Dockerfile": "dockerfile", "Makefile": "makefile", "Jenkinsfile": "jenkinsfile",
    "Procfile": "procfile", "Vagrantfile": "ruby",
    "Gemfile": "ruby", "Rakefile": "ruby",
    "Cargo.toml": "rust", "go.mod": "go", "go.sum": "go",
    "package.json": "json", "tsconfig.json": "json",
    "pyproject.toml": "toml", "setup.py": "python", "setup.cfg": "ini",
    "Pipfile": "toml", "requirements.txt": "text",
    "pom.xml": "xml", "build.gradle": "gradle", "build.gradle.kts": "gradle",
    "composer.json": "json",
    ".dockerignore": "dockerfile", ".gitignore": "text",
}

# ---------------------------------------------------------------------------
# File category detection
# ---------------------------------------------------------------------------

INFRA_PATTERNS = [
    "Dockerfile", "Dockerfile.", "docker-compose.", "compose.yml", "compose.yaml",
    "Makefile", "Jenkinsfile", "Procfile", "Vagrantfile", ".gitlab-ci.yml",
    ".dockerignore",
]
INFRA_PATHS = [".github/workflows/", ".circleci/", "k8s/", "kubernetes/"]
INFRA_EXTENSIONS = {".tf", ".tfvars"}

DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}

CONFIG_EXTENSIONS = {
    ".yaml", ".yml", ".json", ".jsonc", ".toml", ".xml", ".xsl", ".xsd",
    ".plist", ".cfg", ".ini", ".env", ".properties", ".csproj", ".sln",
    ".mod", ".sum", ".gradle",
}

DATA_EXTENSIONS = {".sql", ".graphql", ".gql", ".proto", ".prisma", ".csv", ".tsv"}

SCRIPT_EXTENSIONS = {".sh", ".bash", ".zsh", ".ps1", ".psm1", ".psd1", ".bat", ".cmd"}

MARKUP_EXTENSIONS = {".html", ".htm", ".css", ".scss", ".sass", ".less"}

# Files that are code despite being in docs-like locations
CODE_EXCEPTIONS = {"LICENSE"}


def detect_language(path: Path) -> Optional[str]:
    """Detect the programming language of a file."""
    name = path.name
    if name in FILENAME_LANGUAGE:
        return FILENAME_LANGUAGE[name]
    # Check Dockerfile.* pattern
    if name.startswith("Dockerfile."):
        return "dockerfile"
    ext = path.suffix.lower()
    if ext in {".yml", ".yaml"}:
        if ".github/workflows/" in str(path) or ".circleci/" in str(path):
            return "yaml"
    return LANGUAGE_MAP.get(ext, ext.lstrip(".") if ext else "unknown")


def detect_category(path: Path) -> Optional[str]:
    """Detect the file category based on path and extension."""
    name = path.name
    str_path = str(path)

    # Code exceptions first
    if name in CODE_EXCEPTIONS:
        return "code"

    # Infrastructure patterns (most specific)
    for pattern in INFRA_PATTERNS:
        if name == pattern or (pattern.endswith(".") and name.startswith(pattern)):
            return "infra"
    for infra_path in INFRA_PATHS:
        if infra_path in str_path:
            return "infra"
    if path.suffix.lower() in INFRA_EXTENSIONS:
        return "infra"

    # Documentation
    if path.suffix.lower() in DOC_EXTENSIONS and name not in CODE_EXCEPTIONS:
        return "docs"

    # Config
    if path.suffix.lower() in CONFIG_EXTENSIONS:
        return "config"

    # Data
    if path.suffix.lower() in DATA_EXTENSIONS:
        return "data"

    # Script
    if path.suffix.lower() in SCRIPT_EXTENSIONS:
        return "script"

    # Markup
    if path.suffix.lower() in MARKUP_EXTENSIONS:
        return "markup"

    # Everything else is code
    return "code"


# ---------------------------------------------------------------------------
# Framework detection from manifests
# ---------------------------------------------------------------------------

JS_FRAMEWORKS = [
    "react", "vue", "svelte", "@angular/core", "express", "fastify", "koa",
    "next", "nuxt", "vite", "vitest", "jest", "mocha", "tailwindcss",
    "prisma", "typeorm", "sequelize", "mongoose", "redux", "zustand", "mobx",
    "webpack", "rollup", "esbuild", "babel", "eslint", "prettier",
    "typescript", "ts-node", "nodemon",
]

PYTHON_FRAMEWORKS = [
    "django", "djangorestframework", "fastapi", "flask", "sqlalchemy",
    "alembic", "celery", "pydantic", "uvicorn", "gunicorn", "aiohttp",
    "tornado", "starlette", "pytest", "hypothesis", "channels",
]

RUBY_FRAMEWORKS = [
    "rails", "railties", "sinatra", "grape", "rspec", "sidekiq",
    "activerecord", "actionpack", "devise", "pundit",
]

GO_FRAMEWORKS = [
    "github.com/gin-gonic/gin", "github.com/labstack/echo",
    "github.com/gofiber/fiber", "github.com/go-chi/chi", "gorm.io/gorm",
]

RUST_FRAMEWORKS = [
    "actix-web", "axum", "rocket", "diesel", "tokio", "serde", "warp",
]

JVM_FRAMEWORKS = [
    "spring-boot", "spring-web", "spring-data", "quarkus", "micronaut",
    "hibernate", "jakarta", "junit", "ktor",
]


def detect_frameworks(root: Path) -> list[str]:
    """Detect frameworks from manifest files."""
    frameworks = set()

    # package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for dep in deps:
                dep_lower = dep.lower()
                for fw in JS_FRAMEWORKS:
                    if fw in dep_lower:
                        frameworks.add(fw.title() if fw[0].islower() else fw)
        except (json.JSONDecodeError, KeyError):
            pass

    # Python manifests
    for manifest in ["pyproject.toml", "setup.py", "Pipfile", "requirements.txt"]:
        manifest_path = root / manifest
        if manifest_path.exists():
            try:
                content = manifest_path.read_text(encoding="utf-8", errors="ignore").lower()
                for fw in PYTHON_FRAMEWORKS:
                    if fw in content:
                        frameworks.add(fw.title())
            except Exception:
                pass

    # Cargo.toml
    cargo = root / "Cargo.toml"
    if cargo.exists():
        try:
            content = cargo.read_text(encoding="utf-8", errors="ignore").lower()
            for fw in RUST_FRAMEWORKS:
                if fw in content:
                    frameworks.add(fw.title())
        except Exception:
            pass

    # go.mod
    gomod = root / "go.mod"
    if gomod.exists():
        try:
            content = gomod.read_text(encoding="utf-8", errors="ignore").lower()
            for fw in GO_FRAMEWORKS:
                if fw.lower() in content:
                    frameworks.add(fw.split("/")[-1].title())
        except Exception:
            pass

    # Gemfile
    gemfile = root / "Gemfile"
    if gemfile.exists():
        try:
            content = gemfile.read_text(encoding="utf-8", errors="ignore").lower()
            for fw in RUBY_FRAMEWORKS:
                if fw in content:
                    frameworks.add(fw.title())
        except Exception:
            pass

    # JVM manifests
    for manifest in ["pom.xml", "build.gradle", "build.gradle.kts"]:
        manifest_path = root / manifest
        if manifest_path.exists():
            try:
                content = manifest_path.read_text(encoding="utf-8", errors="ignore").lower()
                for fw in JVM_FRAMEWORKS:
                    if fw in content:
                        frameworks.add(fw.title())
            except Exception:
                pass

    # Infrastructure detection
    if (root / "Dockerfile").exists() or list(root.glob("Dockerfile.*")):
        frameworks.add("Docker")
    if list(root.glob("docker-compose.*")) or (root / "compose.yml").exists() or (root / "compose.yaml").exists():
        frameworks.add("Docker Compose")
    if list(root.glob("*.tf")):
        frameworks.add("Terraform")
    if (root / ".github" / "workflows").exists():
        frameworks.add("GitHub Actions")
    if (root / ".gitlab-ci.yml").exists():
        frameworks.add("GitLab CI")
    if (root / "Jenkinsfile").exists():
        frameworks.add("Jenkins")

    return sorted(frameworks)


# ---------------------------------------------------------------------------
# Project metadata extraction
# ---------------------------------------------------------------------------

def extract_project_info(root: Path) -> dict:
    """Extract project name, description from manifests."""
    name = root.name
    description = ""

    # package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            name = pkg.get("name", name)
            description = pkg.get("description", description)
        except (json.JSONDecodeError, KeyError):
            pass

    # pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and not description:
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'^name\s*=\s*["\']([^"\']+)', content, re.MULTILINE)
            if m:
                name = m.group(1)
            m = re.search(r'^description\s*=\s*["\']([^"\']+)', content, re.MULTILINE)
            if m:
                description = m.group(1)
        except Exception:
            pass

    # Cargo.toml
    cargo = root / "Cargo.toml"
    if cargo.exists() and not description:
        try:
            content = cargo.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'^name\s*=\s*["\']([^"\']+)', content, re.MULTILINE)
            if m:
                name = m.group(1)
            m = re.search(r'^description\s*=\s*["\']([^"\']+)', content, re.MULTILINE)
            if m:
                description = m.group(1)
        except Exception:
            pass

    # README
    readme_content = ""
    for readme_name in ["README.md", "README.rst", "README"]:
        readme_path = root / readme_name
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")[:500]
                if not description:
                    # Try to extract first meaningful line as description
                    for line in readme_content.split("\n"):
                        line = line.strip().lstrip("#").strip()
                        if line and len(line) > 10:
                            description = line[:200]
                            break
            except Exception:
                pass
            break

    return {
        "name": name,
        "description": description or "No description available",
        "readmeHead": readme_content[:300],
    }


# ---------------------------------------------------------------------------
# File enumeration
# ---------------------------------------------------------------------------

def get_ignore_patterns(root: Path) -> list[str]:
    """Read .understandignore and .gitignore for patterns to exclude."""
    patterns = [
        ".git/", "node_modules/", "__pycache__/", ".venv/", "venv/",
        ".tox/", ".mypy_cache/", ".pytest_cache/", ".ruff_cache/",
        "dist/", "build/", "*.pyc", "*.pyo", "*.so", "*.dylib", "*.dll",
        ".DS_Store", "Thumbs.db", ".understand/",
    ]
    for ignore_file in [".understandignore", ".gitignore"]:
        ignore_path = root / ignore_file
        if ignore_path.exists():
            try:
                for line in ignore_path.read_text(encoding="utf-8", errors="ignore").split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
            except Exception:
                pass
    return patterns


def should_ignore(path: Path, patterns: list[str], root: Path) -> bool:
    """Check if a path should be ignored based on patterns."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    str_path = str(rel).replace(os.sep, "/")
    str_path_prefix = str_path + "/"

    for pattern in patterns:
        if not pattern:
            continue
        # Directory patterns
        if pattern.endswith("/"):
            if str_path_prefix.startswith(pattern) or str_path == pattern.rstrip("/"):
                return True
        # Glob patterns
        import fnmatch
        if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
        # Path contains pattern
        if pattern in str_path_prefix:
            return True
    return False


def enumerate_files(root: Path) -> list[Path]:
    """Enumerate all files in the project, respecting ignore patterns."""
    patterns = get_ignore_patterns(root)
    files = []

    # Try git ls-files first
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(root),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line:
                    p = root / line
                    if p.is_file() and not should_ignore(p, patterns, root):
                        files.append(p)
            if files:
                return sorted(files)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: recursive walk
    for p in root.rglob("*"):
        if p.is_file() and not should_ignore(p, patterns, root):
            files.append(p)
    return sorted(files)


# ---------------------------------------------------------------------------
# Import extraction (simplified)
# ---------------------------------------------------------------------------

def extract_imports(path: Path, root: Path, all_files: set[str]) -> list[str]:
    """Extract project-internal imports from a file."""
    imports = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        ext = path.suffix.lower()
        rel_str = str(path.relative_to(root)).replace(os.sep, "/")

        if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            # ES imports: import ... from '...' or require('...')
            for m in re.finditer(r"""(?:import|require)\s*\(?['"]([^'"]+)['"]\)?""", content):
                imp = m.group(1)
                resolved = resolve_import(imp, path, root, all_files)
                if resolved:
                    imports.append(resolved)

        elif ext == ".py":
            # Python imports: from x import y / import x
            for m in re.finditer(r'^\s*(?:from|import)\s+([\w.]+)', content, re.MULTILINE):
                mod = m.group(1)
                resolved = resolve_python_import(mod, path, root, all_files)
                if resolved:
                    imports.append(resolved)

        elif ext == ".go":
            # Go imports
            for m in re.finditer(r'import\s*\(\s*([^)]+)\s*\)', content, re.DOTALL):
                for line in m.group(1).split("\n"):
                    line = line.strip().strip('"')
                    if line and not line.startswith("//"):
                        resolved = resolve_go_import(line, path, root, all_files)
                        if resolved:
                            imports.append(resolved)

        elif ext == ".rs":
            # Rust: use crate:: / use super:: / use self::
            for m in re.finditer(r'use\s+(crate|super|self)::([\w:]+)', content):
                mod_path = m.group(2).replace("::", "/")
                for candidate in [
                    root / f"{mod_path}.rs",
                    root / mod_path / "mod.rs",
                ]:
                    if candidate.exists():
                        try:
                            rel = str(candidate.relative_to(root)).replace(os.sep, "/")
                            imports.append(rel)
                        except ValueError:
                            pass

        elif ext in (".java", ".kt", ".kts"):
            # Java/Kotlin: import statements
            pkg = ""
            if ext == ".java":
                pm = re.search(r'^\s*package\s+([\w.]+)', content, re.MULTILINE)
                if pm:
                    pkg = pm.group(1)
            for m in re.finditer(r'^\s*import\s+([\w.]+)', content, re.MULTILINE):
                imp = m.group(1)
                parts = imp.split(".")
                # Try to find the file
                for i in range(len(parts), 0, -1):
                    candidate_path = "/".join(parts[:i]) + ".java"
                    if candidate_path in all_files:
                        imports.append(candidate_path)
                        break

        elif ext == ".cs":
            for m in re.finditer(r'^\s*using\s+([\w.]+)', content, re.MULTILINE):
                pass  # C# namespace imports are harder to resolve statically

        elif ext == ".rb":
            for m in re.finditer(r"""(?:require|require_relative)\s*\(?['"]([^'"]+)['"]\)?""", content):
                imp = m.group(1)
                if imp.startswith("."):
                    resolved = resolve_relative(imp, path, root, all_files)
                    if resolved:
                        imports.append(resolved)

        elif ext == ".php":
            for m in re.finditer(r"""(?:require|include)(?:_once)?\s*\(?['"]([^'"]+)['"]\)?;""", content):
                imp = m.group(1)
                resolved = resolve_relative(imp, path, root, all_files)
                if resolved:
                    imports.append(resolved)

        elif ext in (".c", ".h", ".cpp", ".hpp", ".cc", ".cxx"):
            for m in re.finditer(r'#include\s+["<]([^">]+)[">]', content):
                imp = m.group(1)
                resolved = resolve_c_include(imp, path, root, all_files)
                if resolved:
                    imports.append(resolved)

    except Exception:
        pass

    return list(set(imports))


def resolve_import(imp: str, source: Path, root: Path, all_files: set[str]) -> Optional[str]:
    """Resolve a JS/TS import path to a project file."""
    if imp.startswith("."):
        return resolve_relative(imp, source, root, all_files)
    # Check if it's a local workspace package
    for f in all_files:
        if f.endswith(imp + ".ts") or f.endswith(imp + ".js") or f.endswith(imp + "/index.ts") or f.endswith(imp + "/index.js"):
            return f
    return None


def resolve_relative(imp: str, source: Path, root: Path, all_files: set[str]) -> Optional[str]:
    """Resolve a relative import path."""
    base = source.parent
    # Normalize the path
    parts = imp.replace("\\", "/").split("/")
    resolved = list(base.relative_to(root).parts) if base != root else []
    for part in parts:
        if part == "..":
            if resolved:
                resolved.pop()
        elif part != ".":
            resolved.append(part)

    resolved_path = "/".join(resolved)

    # Try exact match
    if resolved_path in all_files:
        return resolved_path
    # Try with extensions
    for ext in [".ts", ".tsx", ".js", ".jsx", ".json", ".py", ".go", ".rs", ".rb", ".php", ".java", ".kt", ".cs", ".c", ".cpp", ".h", ".hpp"]:
        if resolved_path + ext in all_files:
            return resolved_path + ext
    # Try index files
    for ext in [".ts", ".tsx", ".js", ".jsx"]:
        if resolved_path + "/index" + ext in all_files:
            return resolved_path + "/index" + ext

    return None


def resolve_python_import(mod: str, source: Path, root: Path, all_files: set[str]) -> Optional[str]:
    """Resolve a Python module path to a file."""
    parts = mod.split(".")
    mod_path = "/".join(parts)

    # Try as package
    for candidate in [
        mod_path + ".py",
        mod_path + "/__init__.py",
    ]:
        if candidate in all_files:
            return candidate

    # Try relative to source
    if source.name == "__init__.py":
        base = source.parent
    else:
        base = source.parent
    rel_candidate = base / mod_path
    try:
        rel_str = str(rel_candidate.relative_to(root)).replace(os.sep, "/")
        if rel_str + ".py" in all_files:
            return rel_str + ".py"
        if rel_str + "/__init__.py" in all_files:
            return rel_str + "/__init__.py"
    except ValueError:
        pass

    return None


def resolve_go_import(imp: str, source: Path, root: Path, all_files: set[str]) -> Optional[str]:
    """Resolve a Go import to a local file."""
    # Only resolve local imports (not external packages)
    gomod = root / "go.mod"
    if gomod.exists():
        try:
            content = gomod.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
            if m:
                module_prefix = m.group(1)
                if imp.startswith(module_prefix):
                    local_path = imp[len(module_prefix):].strip("/")
                    for f in all_files:
                        if f.startswith(local_path) and f.endswith(".go"):
                            return f
        except Exception:
            pass
    return None


def resolve_c_include(imp: str, source: Path, root: Path, all_files: set[str]) -> Optional[str]:
    """Resolve a C/C++ #include to a local file."""
    if imp in all_files:
        return imp
    # Try relative to source
    candidate = source.parent / imp
    try:
        rel = str(candidate.relative_to(root)).replace(os.sep, "/")
        if rel in all_files:
            return rel
    except ValueError:
        pass
    # Try include/ and src/
    for prefix in ["include/", "src/"]:
        if prefix + imp in all_files:
            return prefix + imp
    return None


# ---------------------------------------------------------------------------
# Complexity estimation
# ---------------------------------------------------------------------------

def estimate_complexity(total_files: int, total_lines: int) -> Optional[str]:
    """Estimate project complexity."""
    if total_files < 20 and total_lines < 1000:
        return "simple"
    elif total_files < 100 and total_lines < 10000:
        return "moderate"
    else:
        return "complex"


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def scan_project(root: Path, output: Path) -> dict:
    """Run the full project scan."""
    print(f"Scanning {root}...", file=sys.stderr)

    files = enumerate_files(root)
    print(f"Found {len(files)} files.", file=sys.stderr)

    # Build file list
    file_entries = []
    all_file_paths = set()
    total_lines = 0
    by_category = {}
    by_language = {}

    for f in files:
        try:
            rel = str(f.relative_to(root)).replace(os.sep, "/")
        except ValueError:
            continue
        all_file_paths.add(rel)

        lang = detect_language(f)
        category = detect_category(f)

        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").count("\n") + 1
        except Exception:
            lines = 0

        total_lines += lines
        by_category[category] = by_category.get(category, 0) + 1
        by_language[lang] = by_language.get(lang, 0) + 1

        file_entries.append({
            "path": rel,
            "language": lang,
            "fileCategory": category,
            "sizeLines": lines,
        })

    # Extract imports
    print("Extracting imports...", file=sys.stderr)
    import_map = {}
    for entry in file_entries:
        if entry["fileCategory"] == "code":
            f = root / entry["path"]
            imports = extract_imports(f, root, all_file_paths)
            if imports:
                import_map[entry["path"]] = imports

    # Project info
    info = extract_project_info(root)
    frameworks = detect_frameworks(root)
    languages = sorted(by_language.keys())

    result = {
        "version": "1.0.0",
        "project": {
            "name": info["name"],
            "description": info["description"],
            "languages": languages,
            "frameworks": frameworks,
            "analyzedAt": datetime.now().isoformat(),
        },
        "files": file_entries,
        "totalFiles": len(file_entries),
        "filteredByIgnore": 0,
        "estimatedComplexity": estimate_complexity(len(file_entries), total_lines),
        "stats": {
            "byCategory": by_category,
            "byLanguage": by_language,
            "totalLines": total_lines,
        },
        "importMap": import_map,
    }

    # Write output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scan complete. Output: {output}", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description="Scan a codebase for analysis")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    scan_project(root, Path(args.output))


if __name__ == "__main__":
    main()
