---
name: understand
description: |
  Analyze a codebase to build a structured knowledge graph of files, functions,
  classes, dependencies, and architecture layers. Use when the user wants to
  understand a project's structure, generate architecture documentation, create
  guided onboarding tours, or analyze the impact of changes. Triggers on:
  "understand this codebase", "analyze this project", "map out the code",
  "how is this project structured", "generate architecture docs", "create a
  knowledge graph", "explain this project", "onboarding guide", "codebase tour".
---

# Understand

Analyze a codebase and produce a structured knowledge graph that maps files, functions, classes, dependencies, and architecture layers.

## When to Use

- "Understand this codebase"
- "Analyze the project structure"
- "Generate architecture documentation"
- "Create an onboarding guide"
- "Map out the dependencies"
- "How is this project organized?"
- "What's the architecture of this codebase?"

## Quick Start

```bash
# Generate project context (build commands, doc routes, debug patterns)
python3 scripts/understand/generate_context.py .

# Build the full knowledge graph + tour
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json
```

The `generate_context.py` script is the **primary entry point**. It analyzes the codebase in pure Python (no LLM needed) and produces:

- `.understand/context.json` — structured data about the project
- `.understand/context.md` — human-readable summary with **suggested template customizations**

The context file tells you exactly what build commands, test commands, doc routes, and debug patterns to add to your AI Coding templates.

## Pipeline

The analysis runs in 4 phases:

### Phase 1 — Project Scan

Scan the codebase to produce a structured inventory:

```
python3 scripts/understand/scan_project.py <project-root> --output <output-path>
```

Produces: file list with language detection, file categories (code/config/docs/infra/data/script/markup), line counts, complexity estimates, and import maps.

**Supported languages:** TypeScript, JavaScript, Python, Go, Rust, Java, Kotlin, C#, Ruby, PHP, C, C++, Swift, Shell, PowerShell, Batch, HTML, CSS, SQL, GraphQL, Protobuf, YAML, JSON, TOML, Markdown.

### Phase 2 — Architecture Analysis

Identify architectural layers and assign every file to a layer:

```
python3 scripts/understand/analyze_architecture.py <project-root> --output <output-path>
```

Produces: 3-10 layers (e.g., API, Service, Data, UI, Infrastructure, Config, Documentation) with file assignments.

### Phase 3 — Knowledge Graph Build

Combine scan results, architecture layers, and semantic analysis into a unified knowledge graph:

```
python3 scripts/understand/build_graph.py <project-root> --output <output-path>
```

Produces: `knowledge-graph.json` with nodes (files, functions, classes, configs, documents, services, tables, endpoints, pipelines, schemas, resources) and edges (imports, contains, calls, configures, documents, deploys, etc.).

### Phase 4 — Tour Generation

Create a guided onboarding tour through the codebase:

```
python3 scripts/understand/build_tour.py <project-root> --output <output-path>
```

Produces: 5-15 step guided tour ordered by dependency, starting from README → entry point → core modules → infrastructure.

## Output Files

```
<project-root>/
└── .understand/
    ├── scan.json              # Phase 1: File inventory + import map
    ├── layers.json            # Phase 2: Architecture layers
    ├── knowledge-graph.json   # Phase 3: Full knowledge graph
    ├── domain-graph.json      # Phase 3b: Business domain graph (optional)
    └── tour.json              # Phase 4: Guided onboarding tour
```

## Knowledge Graph Schema

### Node Types (13 structural + 3 domain)

| Type | ID Convention | Description |
|------|--------------|-------------|
| `file` | `file:<path>` | Source file |
| `function` | `function:<path>:<name>` | Function or method |
| `class` | `class:<path>:<name>` | Class, interface, or type |
| `config` | `config:<path>` | Configuration file |
| `document` | `document:<path>` | Documentation file |
| `service` | `service:<path>` | Dockerfile, docker-compose, K8s manifest |
| `table` | `table:<path>:<name>` | Database table |
| `endpoint` | `endpoint:<path>:<name>` | API endpoint |
| `pipeline` | `pipeline:<path>` | CI/CD pipeline |
| `schema` | `schema:<path>` | GraphQL, Protobuf, Prisma schema |
| `resource` | `resource:<path>` | Terraform, CloudFormation resource |
| `domain` | `domain:<name>` | Business domain |
| `flow` | `flow:<name>` | Business flow/process |
| `step` | `step:<flow>:<name>` | Business step |

### Edge Types (26 structural + 3 domain)

| Category | Types |
|----------|-------|
| Structural | `imports`, `exports`, `contains`, `inherits`, `implements` |
| Behavioral | `calls`, `subscribes`, `publishes`, `middleware` |
| Data flow | `reads_from`, `writes_to`, `transforms`, `validates` |
| Dependencies | `depends_on`, `tested_by`, `configures` |
| Semantic | `related`, `similar_to` |
| Infrastructure | `deploys`, `serves`, `provisions`, `triggers`, `migrates`, `documents`, `routes`, `defines_schema` |
| Domain | `contains_flow`, `flow_step`, `cross_domain` |

## File Categories

| Category | Patterns |
|----------|----------|
| `code` | Source files (`.ts`, `.py`, `.go`, `.rs`, `.java`, etc.) |
| `config` | `package.json`, `tsconfig.json`, `.env`, `*.toml`, `*.yaml` |
| `docs` | `*.md`, `*.rst`, `*.txt` (except `LICENSE`) |
| `infra` | `Dockerfile`, `docker-compose.*`, `*.tf`, `.github/workflows/*`, K8s manifests |
| `data` | `*.sql`, `*.graphql`, `*.proto`, `*.prisma`, `*.csv` |
| `script` | `*.sh`, `*.bash`, `*.ps1`, `*.bat`, `*.cmd` |
| `markup` | `*.html`, `*.css`, `*.scss`, `*.sass`, `*.less` |

## Architecture Layer Patterns

Directory names are matched against known patterns:

| Directory | Layer |
|-----------|-------|
| `routes/`, `api/`, `controllers/`, `handlers/` | API |
| `services/`, `core/`, `domain/`, `lib/` | Service |
| `models/`, `db/`, `data/`, `repository/`, `entities/` | Data |
| `components/`, `views/`, `pages/`, `ui/` | UI |
| `middleware/`, `plugins/`, `guards/` | Middleware |
| `utils/`, `helpers/`, `common/`, `shared/` | Utility |
| `config/`, `constants/`, `settings/` | Config |
| `test/`, `tests/`, `__tests__/`, `spec/` | Test |
| `types/`, `interfaces/`, `schemas/`, `dtos/` | Types |
| `hooks/`, `store/`, `state/`, `reducers/` | State |
| `Dockerfile`, `docker-compose.*`, K8s, Terraform | Infrastructure |
| `docs/`, `README.md`, `CONTRIBUTING.md` | Documentation |
| `.github/workflows/`, `.gitlab-ci.yml` | CI/CD |

## Integration with AI Coding Agents

The knowledge graph can be used by AI coding agents to:

1. **Answer questions** about the codebase ("How does authentication work?")
2. **Find related files** when working on a feature
3. **Understand impact** before making changes
4. **Generate onboarding docs** for new team members
5. **Identify architectural violations** (e.g., UI layer importing from Data layer)

### Example Queries (using jq)

```bash
# Find all files in the API layer
jq '.layers[] | select(.id == "layer:api") | .nodeIds' .understand/knowledge-graph.json

# Find what a file imports
jq '.edges[] | select(.source == "file:src/index.ts" and .type == "imports") | .target' .understand/knowledge-graph.json

# Find all files that import a specific utility
jq '.edges[] | select(.target == "file:src/utils/format.ts") | .source' .understand/knowledge-graph.json

# Get the guided tour
jq '.[] | {order, title, nodeIds}' .understand/tour.json

# Find business domains
jq '.nodes[] | select(.type == "domain") | {id, name, summary}' .understand/domain-graph.json
```

## Customization

After generation, you can customize the analysis:

1. **Add `.understandignore`** to exclude files from analysis (same format as `.gitignore`)
2. **Edit `layers.json`** to adjust architecture layer assignments
3. **Edit `knowledge-graph.json`** to add domain-specific knowledge
4. **Edit `tour.json`** to customize the onboarding path

## Re-run and Incremental Analysis

Re-run anytime the codebase changes:

```bash
# Full re-analysis
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json

# Incremental (only re-analyzes changed files)
python3 scripts/understand/build_graph.py . --output .understand/knowledge-graph.json --incremental
```
