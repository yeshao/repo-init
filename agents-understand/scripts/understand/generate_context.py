#!/usr/bin/env python3
"""
generate_context.py — Analyze a repo and generate a context file for AI-assisted
template customization.

This script does ALL analysis in pure Python (no LLM calls). It produces:
  1. .understand/context.json  — structured data about the project
  2. .understand/context.md    — human-readable summary for LLM consumption

The context file contains everything an LLM needs to customize the AI Coding
templates: build commands, test commands, detected frameworks, doc structure,
language-specific patterns, and suggested knowledge base routes.

Usage:
    python3 generate_context.py <project-root> [--output-dir <dir>]
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
# Build system detection
# ---------------------------------------------------------------------------

BUILD_SYSTEMS = {
    # Manifest file → (build_cmd, test_cmd, lint_cmd, build_dir)
    "Cargo.toml": {
        "build": "cargo build --release",
        "test": "cargo test",
        "lint": "cargo clippy",
        "check": "cargo check",
        "build_dir": "target/",
        "test_filter": "cargo test <name>",
        "language": "rust",
    },
    "package.json": {
        "build": "npm run build",
        "test": "npm test",
        "lint": "npm run lint",
        "check": "npm run check",
        "build_dir": "dist/",
        "test_filter": "npm test -- --testNamePattern=<name>",
        "language": "javascript",
    },
    "go.mod": {
        "build": "go build ./...",
        "test": "go test ./...",
        "lint": "go vet ./...",
        "check": "go build ./...",
        "build_dir": "bin/",
        "test_filter": "go test -run <name> ./...",
        "language": "go",
    },
    "pyproject.toml": {
        "build": "pip install -e .",
        "test": "pytest",
        "lint": "ruff check .",
        "check": "mypy .",
        "build_dir": "dist/",
        "test_filter": "pytest -k <name>",
        "language": "python",
    },
    "setup.py": {
        "build": "pip install -e .",
        "test": "pytest",
        "lint": "flake8",
        "check": "python -m py_compile",
        "build_dir": "build/",
        "test_filter": "pytest -k <name>",
        "language": "python",
    },
    "setup.cfg": {
        "build": "pip install -e .",
        "test": "pytest",
        "lint": "flake8",
        "check": "python -m py_compile",
        "build_dir": "build/",
        "test_filter": "pytest -k <name>",
        "language": "python",
    },
    "requirements.txt": {
        "build": "pip install -r requirements.txt",
        "test": "pytest",
        "lint": "flake8",
        "check": "python -m py_compile",
        "build_dir": "N/A",
        "test_filter": "pytest -k <name>",
        "language": "python",
    },
    "Pipfile": {
        "build": "pipenv install",
        "test": "pipenv run pytest",
        "lint": "pipenv run flake8",
        "check": "pipenv run python -m py_compile",
        "build_dir": "N/A",
        "test_filter": "pipenv run pytest -k <name>",
        "language": "python",
    },
    "Gemfile": {
        "build": "bundle install",
        "test": "bundle exec rspec",
        "lint": "bundle exec rubocop",
        "check": "bundle exec ruby -c",
        "build_dir": "pkg/",
        "test_filter": "bundle exec rspec <path>",
        "language": "ruby",
    },
    "pom.xml": {
        "build": "mvn compile",
        "test": "mvn test",
        "lint": "mvn checkstyle:check",
        "check": "mvn compile",
        "build_dir": "target/",
        "test_filter": "mvn test -Dtest=<name>",
        "language": "java",
    },
    "build.gradle": {
        "build": "gradle build",
        "test": "gradle test",
        "lint": "gradle check",
        "check": "gradle compileJava",
        "build_dir": "build/",
        "test_filter": "gradle test --tests <name>",
        "language": "java",
    },
    "build.gradle.kts": {
        "build": "gradle build",
        "test": "gradle test",
        "lint": "gradle check",
        "check": "gradle compileKotlin",
        "build_dir": "build/",
        "test_filter": "gradle test --tests <name>",
        "language": "kotlin",
    },
    "composer.json": {
        "build": "composer install",
        "test": "composer test",
        "lint": "composer lint",
        "check": "composer validate",
        "build_dir": "vendor/",
        "test_filter": "composer test -- --filter <name>",
        "language": "php",
    },
    ".csproj": {
        "build": "dotnet build",
        "test": "dotnet test",
        "lint": "dotnet format --verify-no-changes",
        "check": "dotnet build",
        "build_dir": "bin/",
        "test_filter": "dotnet test --filter <name>",
        "language": "csharp",
    },
    "Makefile": {
        "build": "make",
        "test": "make test",
        "lint": "make lint",
        "check": "make check",
        "build_dir": "build/",
        "test_filter": "make test TEST=<name>",
        "language": "c",
    },
    "CMakeLists.txt": {
        "build": "cmake --build build/",
        "test": "ctest --test-dir build/",
        "lint": "cppcheck src/",
        "check": "cmake --build build/",
        "build_dir": "build/",
        "test_filter": "ctest --test-dir build/ -R <name>",
        "language": "cpp",
    },
    "build.swift": {
        "build": "swift build",
        "test": "swift test",
        "lint": "swiftlint",
        "check": "swift build",
        "build_dir": ".build/",
        "test_filter": "swift test --filter <name>",
        "language": "swift",
    },
}


def detect_build_system(root: Path) -> dict:
    """Detect the build system and return commands."""
    for manifest, config in BUILD_SYSTEMS.items():
        if manifest.startswith("."):
            # Check for any file with this extension
            matches = list(root.glob(f"*{manifest}"))
            if matches:
                return config
        elif (root / manifest).exists():
            return config

    # Check for package.json scripts for more specific commands
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            scripts = data.get("scripts", {})
            config = dict(BUILD_SYSTEMS["package.json"])
            if "build" in scripts:
                config["build"] = f"npm run build  # ({scripts['build']})"
            if "test" in scripts:
                config["test"] = f"npm test  # ({scripts['test']})"
            if "lint" in scripts:
                config["lint"] = f"npm run lint  # ({scripts['lint']})"
            if "check" in scripts:
                config["check"] = f"npm run check  # ({scripts['check']})"
            elif "typecheck" in scripts:
                config["check"] = f"npm run typecheck  # ({scripts['typecheck']})"
            return config
        except Exception:
            pass

    return {}


# ---------------------------------------------------------------------------
# Language-specific debugging routes
# ---------------------------------------------------------------------------

LANGUAGE_DEBUG_ROUTES = {
    "rust": {
        "common_errors": [
            ("trait not implemented", [
                "Check trait bounds on the type",
                "Verify the type implements all required traits",
                "Check feature flags for optional trait impls",
                "Look for blanket impls that might apply",
            ]),
            ("lifetime mismatch", [
                "Check ownership flow — who owns the data?",
                "Verify lifetime annotations match the actual data flow",
                "Consider Arc<T> for shared ownership across threads",
                "Consider cloning if the lifetime is too complex",
            ]),
            ("borrow checker error", [
                "Check for simultaneous mutable and immutable borrows",
                "Narrow the scope of mutable borrows",
                "Use .clone() if ownership transfer is needed",
                "Consider RefCell<T> for interior mutability",
            ]),
            ("type mismatch", [
                "Check the expected type vs actual type",
                "Look for missing type annotations",
                "Check if .into() or .try_into() is needed",
                "Verify generic type parameters",
            ]),
        ],
        "key_concepts": ["ownership", "borrowing", "lifetimes", "traits", "generics"],
    },
    "python": {
        "common_errors": [
            ("ImportError / ModuleNotFoundError", [
                "Check if the package is installed: pip install <package>",
                "Verify virtual environment is activated",
                "Check PYTHONPATH includes the project root",
                "For local imports, verify __init__.py exists in package dirs",
            ]),
            ("TypeError", [
                "Check function signatures match the call site",
                "Verify None isn't being used where a value is expected",
                "Check type annotations for correctness",
            ]),
            ("AttributeError", [
                "Verify the object has the attribute you're accessing",
                "Check if the object is actually the type you expect",
                "Look for typos in attribute names",
            ]),
        ],
        "key_concepts": ["duck typing", "decorators", "generators", "context managers", "GIL"],
    },
    "javascript": {
        "common_errors": [
            ("Cannot read property of undefined", [
                "Add null checks before accessing properties",
                "Use optional chaining: obj?.property",
                "Check if the variable is properly initialized",
            ]),
            ("Module not found", [
                "Check if the package is installed: npm install <package>",
                "Verify the import path is correct",
                "Check tsconfig.json paths for path aliases",
            ]),
            ("is not a function", [
                "Verify the export name matches the import",
                "Check if you're importing a named export as default",
                "Ensure the module actually exports the function",
            ]),
        ],
        "key_concepts": ["closures", "promises", "event loop", "prototypes", "modules"],
    },
    "typescript": {
        "common_errors": [
            ("Type 'X' is not assignable to type 'Y'", [
                "Check the type definition at both sides of the assignment",
                "Use type guards to narrow types",
                "Check if you need a type assertion: value as Type",
                "Verify generic type parameters",
            ]),
            ("Property 'X' does not exist on type 'Y'", [
                "Check the type definition for the correct property name",
                "Use optional chaining if the property might not exist",
                "Extend the interface if the property should exist",
            ]),
            ("Cannot find module", [
                "Check tsconfig.json paths for path aliases",
                "Install types: npm install -D @types/<package>",
                "Add a declaration: declare module '<package>'",
            ]),
        ],
        "key_concepts": ["type narrowing", "generics", "discriminated unions", "utility types", "decorators"],
    },
    "go": {
        "common_errors": [
            ("nil pointer dereference", [
                "Check if the variable was initialized",
                "Verify error handling — errors return nil values",
                "Use the comma-ok pattern for map lookups and type assertions",
            ]),
            ("undefined: X", [
                "Check if the package is imported",
                "Verify the symbol is exported (capitalized)",
                "Run go mod tidy to update dependencies",
            ]),
            ("cannot use X as type Y", [
                "Check interface satisfaction",
                "Verify pointer vs value receiver methods",
                "Use type conversion if types are compatible",
            ]),
        ],
        "key_concepts": ["goroutines", "channels", "interfaces", "embedding", "error handling"],
    },
    "java": {
        "common_errors": [
            ("NullPointerException", [
                "Check for null before accessing object methods",
                "Use Optional<T> for values that might be null",
                "Verify object initialization in constructors",
            ]),
            ("cannot find symbol", [
                "Check imports for the class",
                "Verify the class is on the classpath",
                "Check for typos in the class name",
            ]),
        ],
        "key_concepts": ["generics", "streams", "annotations", "interfaces", "classloaders"],
    },
    "ruby": {
        "common_errors": [
            ("NoMethodError (undefined method)", [
                "Check if the object is nil",
                "Verify the method exists on the object's class",
                "Check for typos in method names",
            ]),
            ("LoadError (cannot load such file)", [
                "Check if the gem is installed: bundle install",
                "Verify the require path is correct",
                "Check $LOAD_PATH includes the lib directory",
            ]),
        ],
        "key_concepts": ["blocks", "procs", "lambdas", "metaprogramming", "mixins"],
    },
    "php": {
        "common_errors": [
            ("Class 'X' not found", [
                "Check autoload configuration in composer.json",
                "Run composer dump-autoload",
                "Verify the namespace matches the file path",
            ]),
            ("Undefined variable", [
                "Check variable initialization",
                "Verify variable scope",
                "Check for typos in variable names",
            ]),
        ],
        "key_concepts": ["namespaces", "traits", "closures", "generators", "autoloading"],
    },
    "c": {
        "common_errors": [
            ("segmentation fault", [
                "Check for null pointer dereferences",
                "Verify array bounds are not exceeded",
                "Check for use-after-free",
                "Run with valgrind: valgrind ./program",
            ]),
            ("undefined reference", [
                "Check if all source files are compiled",
                "Verify library linking order",
                "Check for missing -l flags in the build command",
            ]),
        ],
        "key_concepts": ["pointers", "memory management", "structs", "preprocessor", "linking"],
    },
    "cpp": {
        "common_errors": [
            ("undefined symbol", [
                "Check if all .cpp files are compiled and linked",
                "Verify template definitions are in headers",
                "Check for name mangling issues with extern \"C\"",
            ]),
            ("segmentation fault", [
                "Check for dangling pointers/references",
                "Verify object lifetimes",
                "Use smart pointers (unique_ptr, shared_ptr)",
                "Run with address sanitizer: -fsanitize=address",
            ]),
        ],
        "key_concepts": ["RAII", "templates", "smart pointers", "move semantics", "STL"],
    },
}


# ---------------------------------------------------------------------------
# Doc structure analysis
# ---------------------------------------------------------------------------

def analyze_docs_structure(root: Path) -> dict:
    """Analyze the docs/ directory structure for knowledge base routing."""
    docs_dirs = []
    doc_files = []

    for pattern in ["docs/", "doc/", "documentation/", "wiki/", "guides/"]:
        d = root / pattern.rstrip("/")
        if d.is_dir():
            docs_dirs.append(pattern.rstrip("/"))

    for pattern in ["*.md", "*.rst"]:
        for f in root.rglob(pattern):
            try:
                rel = str(f.relative_to(root))
            except ValueError:
                continue
            if ".git" in rel or "node_modules" in rel:
                continue
            doc_files.append(rel)

    # Categorize doc files
    categorized = {}
    for f in doc_files:
        fl = f.lower()
        if "readme" in fl:
            categorized.setdefault("overview", []).append(f)
        elif "arch" in fl or "design" in fl or "structure" in fl:
            categorized.setdefault("architecture", []).append(f)
        elif "api" in fl or "reference" in fl:
            categorized.setdefault("api_reference", []).append(f)
        elif "contrib" in fl or "develop" in fl or "setup" in fl:
            categorized.setdefault("development", []).append(f)
        elif "deploy" in fl or "infra" in fl or "docker" in fl or "k8s" in fl:
            categorized.setdefault("deployment", []).append(f)
        elif "test" in fl:
            categorized.setdefault("testing", []).append(f)
        elif "security" in fl or "auth" in fl:
            categorized.setdefault("security", []).append(f)
        elif "chang" in fl or "release" in fl or "migration" in fl:
            categorized.setdefault("changelog", []).append(f)
        elif "trouble" in fl or "debug" in fl or "faq" in fl:
            categorized.setdefault("troubleshooting", []).append(f)
        else:
            categorized.setdefault("other", []).append(f)

    return {
        "docs_directories": docs_dirs,
        "doc_files": doc_files[:50],  # Cap to avoid huge output
        "categorized": categorized,
        "total_doc_files": len(doc_files),
    }


# ---------------------------------------------------------------------------
# Framework-specific knowledge base routes
# ---------------------------------------------------------------------------

FRAMEWORK_ROUTES = {
    "React": {
        "detected_by": ["react"],
        "routes": [
            ("Involves component state or hooks", "Read docs/react-patterns.md or equivalent"),
            ("Involves routing", "Check for react-router configuration in src/"),
        ],
    },
    "Vue": {
        "detected_by": ["vue", "@vue"],
        "routes": [
            ("Involves component composition", "Read docs/vue-patterns.md or equivalent"),
            ("Involves Vuex/Pinia state", "Check store/ directory"),
        ],
    },
    "Angular": {
        "detected_by": ["@angular"],
        "routes": [
            ("Involves dependency injection", "Check Angular module configuration"),
            ("Involves RxJS observables", "Read docs/angular-rxjs.md or equivalent"),
        ],
    },
    "Next.js": {
        "detected_by": ["next"],
        "routes": [
            ("Involves server-side rendering", "Check pages/ or app/ directory for SSR patterns"),
            ("Involves API routes", "Check pages/api/ or app/api/ directory"),
        ],
    },
    "Django": {
        "detected_by": ["django"],
        "routes": [
            ("Involves database models", "Read models.py files and docs/database.md"),
            ("Involves URL routing", "Check urls.py for route definitions"),
            ("Involves middleware", "Check MIDDLEWARE setting in settings.py"),
        ],
    },
    "Flask": {
        "detected_by": ["flask"],
        "routes": [
            ("Involves route handlers", "Check app.py or routes/ directory"),
            ("Involves blueprints", "Check blueprints/ directory"),
        ],
    },
    "FastAPI": {
        "detected_by": ["fastapi"],
        "routes": [
            ("Involves API endpoints", "Check routers/ directory"),
            ("Involves Pydantic models", "Check models/ or schemas/ directory"),
        ],
    },
    "Express": {
        "detected_by": ["express"],
        "routes": [
            ("Involves route handlers", "Check routes/ directory"),
            ("Involves middleware", "Check middleware/ directory"),
        ],
    },
    "Rails": {
        "detected_by": ["rails", "railties"],
        "routes": [
            ("Involves database models", "Check app/models/ and db/migrate/"),
            ("Involves controllers", "Check app/controllers/"),
            ("Involves routing", "Check config/routes.rb"),
        ],
    },
    "Spring Boot": {
        "detected_by": ["spring-boot"],
        "routes": [
            ("Involves REST controllers", "Check @RestController annotated classes"),
            ("Involves JPA entities", "Check @Entity annotated classes"),
        ],
    },
    "Docker": {
        "detected_by": ["Dockerfile"],
        "routes": [
            ("Involves container builds", "Check Dockerfile and .dockerignore"),
            ("Involves multi-service orchestration", "Check docker-compose.yml"),
        ],
    },
    "Terraform": {
        "detected_by": [".tf"],
        "routes": [
            ("Involves infrastructure changes", "Check *.tf files and docs/infra.md"),
        ],
    },
}


def detect_framework_routes(root: Path, frameworks: list[str]) -> list[dict]:
    """Generate knowledge base routes based on detected frameworks."""
    routes = []
    for fw in frameworks:
        fw_lower = fw.lower()
        for fw_name, fw_config in FRAMEWORK_ROUTES.items():
            for detector in fw_config["detected_by"]:
                if detector.lower() in fw_lower:
                    for trigger, action in fw_config["routes"]:
                        routes.append({
                            "framework": fw_name,
                            "trigger": trigger,
                            "action": action,
                        })
                    break
    return routes


# ---------------------------------------------------------------------------
# Entry point detection
# ---------------------------------------------------------------------------

ENTRY_POINT_PATTERNS = [
    "src/index.ts", "src/index.js", "src/main.ts", "src/main.js",
    "src/app.ts", "src/app.js", "src/server.ts", "src/server.js",
    "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py",
    "main.go", "cmd/main.go",
    "src/main.rs", "src/lib.rs",
    "src/main/java", "Application.java", "Main.java",
    "Program.cs", "Startup.cs",
    "config.ru", "app.rb",
    "index.php", "public/index.php",
    "app.swift", "main.swift",
    "src/Application.kt", "src/Main.kt",
]


def detect_entry_points(root: Path) -> list[str]:
    """Detect likely entry point files."""
    found = []
    for pattern in ENTRY_POINT_PATTERNS:
        p = root / pattern
        if p.exists():
            found.append(pattern)
    return found


# ---------------------------------------------------------------------------
# Test framework detection
# ---------------------------------------------------------------------------

TEST_FRAMEWORKS = {
    "jest": {"test_cmd": "npx jest", "pattern": "*.test.{ts,js,tsx,jsx}"},
    "vitest": {"test_cmd": "npx vitest", "pattern": "*.test.{ts,tsx}"},
    "mocha": {"test_cmd": "npx mocha", "pattern": "*.test.{ts,js}"},
    "pytest": {"test_cmd": "pytest", "pattern": "test_*.py"},
    "unittest": {"test_cmd": "python -m unittest", "pattern": "test_*.py"},
    "cargo test": {"test_cmd": "cargo test", "pattern": "tests/**/*.rs"},
    "go test": {"test_cmd": "go test ./...", "pattern": "*_test.go"},
    "rspec": {"test_cmd": "bundle exec rspec", "pattern": "*_spec.rb"},
    "junit": {"test_cmd": "mvn test / gradle test", "pattern": "*Test.java"},
    "minitest": {"test_cmd": "bundle exec rake test", "pattern": "test_*.rb"},
    "phpunit": {"test_cmd": "vendor/bin/phpunit", "pattern": "*Test.php"},
    "dotnet test": {"test_cmd": "dotnet test", "pattern": "*Tests.cs"},
    "swift test": {"test_cmd": "swift test", "pattern": "*Tests.swift"},
}


def detect_test_framework(root: Path, frameworks: list[str]) -> Optional[str]:
    """Detect the test framework."""
    fw_lower = " ".join(f.lower() for f in frameworks)
    for tf_name, tf_config in TEST_FRAMEWORKS.items():
        if tf_name.lower() in fw_lower:
            return tf_name
    # Check for test directories
    for test_dir in ["tests/", "test/", "__tests__/", "spec/"]:
        if (root / test_dir.rstrip("/")).exists():
            return f"tests in {test_dir}"
    return None


# ---------------------------------------------------------------------------
# Main context generation
# ---------------------------------------------------------------------------

def generate_context(root: Path, output_dir: Path) -> dict:
    """Generate the full context for AI-assisted template customization."""
    root = root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run the scan first
    sys.path.insert(0, str(Path(__file__).parent))
    from scan_project import scan_project
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        scan_path = f.name
    scan_data = scan_project(root, Path(scan_path))

    # Detect build system
    build = detect_build_system(root)

    # Analyze docs
    docs = analyze_docs_structure(root)

    # Detect entry points
    entry_points = detect_entry_points(root)

    # Detect test framework
    test_framework = detect_test_framework(root, scan_data.get("project", {}).get("frameworks", []))

    # Get language-specific debug routes
    languages = scan_data.get("project", {}).get("languages", [])
    debug_routes = {}
    lang_concepts = {}
    for lang in languages:
        lang_key = lang.lower()
        if lang_key in LANGUAGE_DEBUG_ROUTES:
            debug_routes[lang_key] = LANGUAGE_DEBUG_ROUTES[lang_key]["common_errors"]
            lang_concepts[lang_key] = LANGUAGE_DEBUG_ROUTES[lang_key]["key_concepts"]

    # Get framework-specific routes
    fw_routes = detect_framework_routes(root, scan_data.get("project", {}).get("frameworks", []))

    # Build the context
    context = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "project": {
            "name": scan_data.get("project", {}).get("name", root.name),
            "description": scan_data.get("project", {}).get("description", ""),
            "languages": languages,
            "frameworks": scan_data.get("project", {}).get("frameworks", []),
            "complexity": scan_data.get("estimatedComplexity", "unknown"),
            "total_files": scan_data.get("totalFiles", 0),
        },
        "build_system": build,
        "entry_points": entry_points,
        "test_framework": test_framework,
        "docs_structure": docs,
        "debug_routes": debug_routes,
        "language_concepts": lang_concepts,
        "framework_routes": fw_routes,
        "file_categories": scan_data.get("stats", {}).get("byCategory", {}),
        "import_map_stats": {
            "files_with_imports": len(scan_data.get("importMap", {})),
            "total_import_edges": sum(len(v) for v in scan_data.get("importMap", {}).values()),
        },
    }

    # Write JSON context
    context_json = output_dir / "context.json"
    context_json.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write Markdown context (for LLM consumption)
    context_md = _generate_markdown_context(context, root)
    context_md_path = output_dir / "context.md"
    context_md_path.write_text(context_md, encoding="utf-8")

    print(f"Context generated:", file=sys.stderr)
    print(f"  JSON: {context_json}", file=sys.stderr)
    print(f"  Markdown: {context_md_path}", file=sys.stderr)

    return context


def _generate_markdown_context(context: dict, root: Path) -> str:
    """Generate a human-readable Markdown context file for LLM consumption."""
    lines = []
    p = context["project"]
    b = context["build_system"]

    lines.append(f"# Project Analysis: {p['name']}")
    lines.append("")
    lines.append(f"**Description:** {p['description']}")
    lines.append(f"**Complexity:** {p['complexity']} ({p['total_files']} files)")
    lines.append(f"**Languages:** {', '.join(p['languages']) or 'Unknown'}")
    lines.append(f"**Frameworks:** {', '.join(p['frameworks']) or 'None detected'}")
    lines.append("")

    # Build system
    lines.append("## Build System")
    lines.append("")
    if b:
        lines.append(f"| Command | Invocation |")
        lines.append(f"|---------|------------|")
        for cmd in ["build", "test", "lint", "check"]:
            if cmd in b:
                lines.append(f"| {cmd.capitalize()} | `{b[cmd]}` |")
        if "build_dir" in b:
            lines.append(f"| Build output | `{b['build_dir']}` |")
        if "test_filter" in b:
            lines.append(f"| Run single test | `{b['test_filter']}` |")
    else:
        lines.append("*No build system detected. Manual configuration required.*")
    lines.append("")

    # Entry points
    lines.append("## Entry Points")
    lines.append("")
    if context["entry_points"]:
        for ep in context["entry_points"]:
            lines.append(f"- `{ep}`")
    else:
        lines.append("*No standard entry points detected.*")
    lines.append("")

    # Test framework
    lines.append("## Testing")
    lines.append("")
    if context["test_framework"]:
        lines.append(f"**Framework:** {context['test_framework']}")
    else:
        lines.append("*No test framework detected.*")
    lines.append("")

    # Docs structure
    docs = context["docs_structure"]
    lines.append("## Documentation Structure")
    lines.append("")
    if docs["total_doc_files"] > 0:
        lines.append(f"**Total doc files:** {docs['total_doc_files']}")
        if docs["docs_directories"]:
            lines.append(f"**Doc directories:** {', '.join(docs['docs_directories'])}")
        lines.append("")
        for category, files in sorted(docs.get("categorized", {}).items()):
            lines.append(f"### {category.replace('_', ' ').title()}")
            for f in files[:10]:
                lines.append(f"- `{f}`")
            if len(files) > 10:
                lines.append(f"- ... and {len(files) - 10} more")
            lines.append("")
    else:
        lines.append("*No documentation files detected.*")
    lines.append("")

    # File categories
    lines.append("## File Categories")
    lines.append("")
    cats = context.get("file_categories", {})
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        lines.append(f"- **{cat}:** {count} files")
    lines.append("")

    # Import map stats
    imp = context.get("import_map_stats", {})
    lines.append("## Dependency Analysis")
    lines.append("")
    lines.append(f"- Files with imports: {imp.get('files_with_imports', 0)}")
    lines.append(f"- Total import edges: {imp.get('total_import_edges', 0)}")
    lines.append("")

    # Language-specific concepts
    if context.get("language_concepts"):
        lines.append("## Language-Specific Concepts")
        lines.append("")
        for lang, concepts in context["language_concepts"].items():
            lines.append(f"**{lang.title()}:** {', '.join(concepts)}")
        lines.append("")

    # Debug routes
    if context.get("debug_routes"):
        lines.append("## Common Errors & Debugging")
        lines.append("")
        for lang, errors in context["debug_routes"].items():
            lines.append(f"### {lang.title()}")
            for error_msg, steps in errors:
                lines.append(f"**{error_msg}:**")
                for i, step in enumerate(steps, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

    # Framework routes
    if context.get("framework_routes"):
        lines.append("## Framework-Specific Routes")
        lines.append("")
        for route in context["framework_routes"]:
            lines.append(f"- **{route['framework']}:** {route['trigger']} → {route['action']}")
        lines.append("")

    # Suggested customizations
    lines.append("## Suggested Template Customizations")
    lines.append("")
    lines.append("Based on the analysis above, the following customizations are recommended:")
    lines.append("")

    if b:
        lines.append("### common.minimal.md")
        lines.append(f"```")
        lines.append(f"## Build")
        lines.append(f"- Build command: `{b.get('build', 'N/A')}`")
        lines.append(f"- Check command: `{b.get('check', b.get('build', 'N/A'))}`")
        lines.append(f"- Build output: `{b.get('build_dir', 'N/A')}`")
        lines.append(f"")
        lines.append(f"## Test")
        lines.append(f"- Test command: `{b.get('test', 'N/A')}`")
        if "test_filter" in b:
            lines.append(f"- Single test: `{b.get('test_filter', 'N/A')}`")
        lines.append(f"```")
        lines.append("")

    if b:
        lines.append("### templates/default.md")
        lines.append(f"```")
        lines.append(f"## Build Targets")
        lines.append(f"- **Main target:** `{b.get('build', 'N/A')}`")
        lines.append(f"- **Test target:** `{b.get('test', 'N/A')}`")
        if "lint" in b:
            lines.append(f"- **Lint target:** `{b.get('lint', 'N/A')}`")
        lines.append(f"```")
        lines.append("")

    if docs["categorized"] or context.get("debug_routes") or context.get("framework_routes"):
        lines.append("### knowledge_base.md")
        lines.append("Add the following routing rules:")
        lines.append("```")
        for category, files in sorted(docs.get("categorized", {}).items()):
            if files:
                lines.append(f"| Involves {category.replace('_', ' ')} | Read `{files[0]}` |")
        for lang, errors in context.get("debug_routes", {}).items():
            for error_msg, _ in errors[:2]:
                lines.append(f"| {error_msg} | See {lang} debugging guide |")
        for route in context.get("framework_routes", [])[:5]:
            lines.append(f"| {route['trigger']} | {route['action']} |")
        lines.append("```")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate project context for AI template customization")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: <root>/.understand)")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else root / ".understand"
    generate_context(root, output_dir)


if __name__ == "__main__":
    main()
