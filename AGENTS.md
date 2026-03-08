# AGENTS.md

## Repo Purpose And Success Criteria

This repository is a local Python app for tracking certification learning progress.

Primary flow:
1. Import certification tracks/learning paths/modules.
2. Log study time and module status updates.
3. View aggregate and filtered dashboard metrics.

A change is done when:
- Requested behavior is implemented.
- Relevant tests are added or updated and pass.
- Lint/format/type checks pass when configured for touched code.
- Docs are updated when behavior, commands, or structure changes.
- Change is staged and committed.

## Commit Discipline (Required)

Every completed change must be followed by:
1. Stage the change.
2. Commit the change.

Do not leave completed work uncommitted.

## Required Workflow For Every Change

1. Inspect changes:
```powershell
git status --short
```

2. Stage intended files:
```powershell
git add <file-or-directory>
```

3. Commit using one approved type:
```powershell
git commit -m "<type>(<scope>): <short summary>"
```

4. Verify clean state:
```powershell
git status --short
```

## Commit Message Policy

- Allowed types: `feat`, `fix`, `refactor`
- Format: `<type>(<scope>): <summary>`
- Subject should be short, imperative, and specific

Examples:
- `feat(dashboard): add weekly time bar chart by user`
- `fix(importer): handle missing module url gracefully`
- `refactor(metrics): split aggregation queries by domain`

## Approved Commit Templates

### `feat`

Use when adding new functionality.

Template:
```text
feat(<scope>): <new capability>

Why:
- <reason for feature>

What:
- <main implementation item>
- <additional implementation item>

Validation:
- <test or verification performed>
```

### `fix`

Use when correcting incorrect behavior.

Template:
```text
fix(<scope>): <bug fix summary>

Root cause:
- <what was wrong>

Fix:
- <how it was fixed>

Validation:
- <test or verification performed>
```

### `refactor`

Use when changing internal structure without behavior change.

Template:
```text
refactor(<scope>): <structural improvement>

Intent:
- <why refactor was needed>

Changes:
- <main restructuring item>
- <secondary restructuring item>

Validation:
- <test or verification performed>
```

## Quickstart Commands

Preferred toolchain: `uv` + `pytest`.

```powershell
uv venv
.venv\Scripts\Activate.ps1
uv sync
uv run streamlit run app/main.py
uv run pytest
```

If the project scaffold is not yet created, implement missing structure first, then run commands.

## Python And Environment Expectations

- Python: `3.12+`
- OS focus: Windows + PowerShell
- Package/dependency manager: `uv` only
- Do not mix dependency workflows (`pip install`, Poetry, Pipenv) unless explicitly requested.

## Project Layout Map

Expected structure:
- `app/`: Streamlit UI, components, and services
- `data/raw/`: raw provider exports
- `data/curated/`: committed CSV source-of-truth files
- `scripts/`: import/bootstrap utilities
- `tests/`: unit/integration tests and fixtures
- `PLANNING.md`: implementation plan and scope
- `AGENTS.md`: agent operating rules

## App Run Modes

- Dev dashboard:
```powershell
uv run streamlit run app/main.py
```

- Prod-ish local run:
```powershell
uv run streamlit run app/main.py --server.headless true --server.port 8501
```

- Script usage:
```powershell
uv run python scripts/<script_name>.py
```

## Testing Instructions And Philosophy

Commands:
- Run all tests:
```powershell
uv run pytest
```
- Run one file:
```powershell
uv run pytest tests/test_metrics_service.py
```
- Run one scenario:
```powershell
uv run pytest tests/test_metrics_service.py -k weekly -vv
```

Philosophy:
- Prefer deterministic unit tests with fixtures.
- Avoid live network access in tests.
- Add tests for new behavior and bug fixes in the same change.

## Linting And Formatting

Use automated tools, not manual style edits.

Commands:
```powershell
uv run ruff format .
uv run ruff check . --fix
```

## Type Checking

If type checking is configured, run:
```powershell
uv run mypy app scripts
```

Expect typed boundaries for service-layer functions and public APIs.

## Dependency Management Policy

- Source of truth: `pyproject.toml`
- Lockfile: `uv.lock` (commit lockfile changes)
- Add runtime dependency:
```powershell
uv add <package>
```
- Add dev dependency:
```powershell
uv add --dev <package>
```
- Avoid new dependencies unless clearly necessary.

## Configuration And Environment Variables

Configuration priority:
1. Environment variables
2. Local `.env` file (if used)
3. Code defaults

Recommended variables:
- `CERT_TRACKER_ENV` (`dev` by default)
- `CERT_TRACKER_DATA_DIR` (`data/curated` by default)
- `CERT_TRACKER_LOG_LEVEL` (`INFO` by default)

Safe local example:
```powershell
$env:CERT_TRACKER_ENV="dev"
$env:CERT_TRACKER_DATA_DIR="data/curated"
$env:CERT_TRACKER_LOG_LEVEL="DEBUG"
```

## Secrets And Credentials

- Never commit secrets, tokens, or credentials.
- Keep local secrets in ignored files such as `.env.local`.
- Redact secrets from logs, screenshots, issue text, and commit messages.

## Data And File Safety Rules

- Treat `data/curated/*.csv` as source-of-truth files.
- Prefer updates through app forms or scripts over ad-hoc manual edits.
- Preserve CSV headers and schema compatibility.
- Do not regenerate or rewrite large datasets unless requested.
- Do not touch unrelated files in the working tree.

## Code Style And Conventions

- Naming: `snake_case` for functions/variables, `PascalCase` for classes.
- Keep functions small and focused.
- Add concise docstrings for public functions.
- Raise explicit exceptions with useful messages.
- Use logging in services; avoid `print` in non-debug code.
- Add comments only when logic is non-obvious.

## Architecture Boundaries

- `app/pages` and UI components handle presentation and input.
- `app/services` owns business logic, DuckDB queries, and aggregation.
- `app/models` owns schemas/enums/constants.
- `scripts` orchestrate imports/bootstrap and reuse service logic.
- Keep direction clean: UI -> services -> models/data.
- Avoid circular imports and cross-layer shortcuts.

## Change Checklist (Agent-Oriented)

Before commit, ensure:
1. Scope is minimal and aligned to the request.
2. Tests are added or updated for changed behavior.
3. Format/lint/type checks are run when available.
4. Related docs are updated (`README.md`, `PLANNING.md`, or both).
5. Changes are staged and committed with `feat`, `fix`, or `refactor`.

## When Unsure

1. Follow existing repository patterns first.
2. Search for similar code before introducing new patterns.
3. Prefer the smallest safe change.
4. Ask for user confirmation only when ambiguity would cause incorrect behavior.

## Scope Limits

- Keep diffs small and focused.
- Do not run broad refactors unless requested.
- Do not add dependencies without clear need.
- Do not add auth, deployment, CI, or auto-scraping unless explicitly requested.

## Examples Of Good Tasks

- `feat`: add dashboard weekly bar chart filtered by user and track.
- `fix`: correct progress rollup to use latest status per user/module.
- `refactor`: split metrics aggregation into separate service methods.
- `test`: add unit coverage for completion score calculations and weekly totals.

## Notes

- If multiple unrelated changes exist, split into separate commits.
- Avoid mixing `feat`, `fix`, and `refactor` in one commit unless unavoidable.
