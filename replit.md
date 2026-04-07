# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.
Also contains **pyjx2** — a Python CLI/TUI/API tool for Jira/Xray automation.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## pyjx2 — Python Jira/Xray Automation Tool

Located at `pyjx2/`. A standalone Python package with clean architecture.

### Architecture
```
pyjx2/pyjx2/
├── domain/               # Entities + repository interfaces (pure Python)
│   ├── entities/         # Test, TestSet, TestExecution, TestPlan
│   └── repositories/     # Abstract repository contracts (ABC)
├── application/          # Use case services
│   └── services/         # SetupService, SyncService
├── infrastructure/       # Concrete implementations
│   ├── config/           # Settings loader + JSON Schema validator
│   ├── jira/             # Jira REST API client
│   └── xray/             # Xray Cloud REST + GraphQL client + repository impls
├── api/                  # High-level public API facade (PyJX2)
├── cli/                  # Typer CLI commands (setup, sync, tui)
└── tui/                  # Textual TUI application
```

### Key Commands
- `pyjx2 --help` — show all commands
- `pyjx2 setup --project PROJ --test-plan PROJ-100 --execution-summary "..." --test-set-summary "..."` — setup flow
- `pyjx2 sync --execution PROJ-200 --folder ./evidence --status PASS` — sync flow
- `pyjx2 tui` — launch interactive terminal UI

### Configuration
Auto-discovers `pyjx2.toml` or `pyjx2.json` in the current directory.
Environment variables: `PYJX2_JIRA_URL`, `PYJX2_JIRA_USERNAME`, `PYJX2_JIRA_API_TOKEN`, `PYJX2_XRAY_CLIENT_ID`, `PYJX2_XRAY_CLIENT_SECRET`.
Example files: `pyjx2/pyjx2.toml.example`, `pyjx2/pyjx2.json.example`.

### Dependencies
Python 3.10+, httpx, typer, rich, textual, toml, jsonschema.
Install: `cd pyjx2 && pip install -e .`

## Key Node.js Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
