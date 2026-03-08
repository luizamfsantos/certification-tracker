# AGENTS.md

## Commit Discipline (Required)

Every repository change must be followed by:
1. Stage the change(s).
2. Commit the change(s).

No change should be left uncommitted after it is completed.

## Required Workflow For Every Change

1. Inspect changes:
```powershell
git status --short
```

2. Stage intended files:
```powershell
git add <file-or-directory>
```

3. Commit using one of the approved templates (`feat`, `fix`, `refactor`):
```powershell
git commit -m "<type>(<scope>): <short summary>"
```

4. Verify clean state:
```powershell
git status --short
```

## Commit Message Policy

- Use lowercase type: `feat`, `fix`, `refactor`
- Keep subject short, imperative, and specific
- Recommended format:
  - `<type>(<scope>): <summary>`

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

Use when changing internal structure without changing behavior.

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

## Notes

- If multiple unrelated changes exist, split into separate commits.
- Avoid mixing `feat`, `fix`, and `refactor` in a single commit unless unavoidable.
