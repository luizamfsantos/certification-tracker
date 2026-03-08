# Certification Tracker Dashboard - Planning

## 1. Scope

Build a local Python dashboard to track certification study progress for a small group of users.

In scope:
- Multiple certification tracks (example: `AZ-104`)
- Multiple users
- Module catalog imported from cloud provider catalog APIs (initially Microsoft Learn Catalog API: `https://learn.microsoft.com/api/catalog/`)
- Time tracking (vertical bar chart):
  - Aggregate
  - Daily
  - Weekly 
  - Per user
  - Across all users
  - Per module
  - Per certification track
- Progress tracking per module with status (Pie chart, horizontal bar chart):
  - `not_seen`
  - `seen`
  - `mastered`
- Progress visualizations:
  - Pie chart
  - Horizontal bar chart
- CSV files as source data, queried with DuckDB
- Modular repository organization
- Tests included

Out of scope for now:
- Authentication/authorization
- Goals and deadlines
- Automatic scheduled sync jobs
- CI pipeline
- Deployment

## 2. Core Product Decisions

- App is local-first and file-based.
- Data entry is done in the dashboard UI via clicks/selects (not manual CSV edits as primary workflow).
- CSV files are committed to git as the shared source of truth.
- Small team usage (2 users, low write frequency) allows a simple write model.
- Track/module ingestion is manual/on-demand.
- Chart library decision: Plotly.
- Week boundary decision for weekly aggregation: Monday (`date_trunc('week', ...)`).
- CSV row ID strategy decision: UUID (`uuid4`).

## 3. Proposed Tech Stack

- Language: Python 3.12+
- Dashboard/UI: Streamlit
- Query engine: DuckDB
- Data interchange/storage: CSV files
- Plotting: Plotly
- Testing: pytest

## 3.1 Environment And Infrastructure

No cloud infrastructure is required for MVP. This is local-first infrastructure only.
All execution checklists are consolidated in Section 10 (`Unified Execution Checklist`).

## 4. Repository Structure

```text
certification-tracker/
  PLANNING.md
  Dockerfile
  README.md
  pyproject.toml
  data/
    raw/
      microsoft_learn/
    curated/
      users.csv
      certification_tracks.csv
      learning_paths.csv
      modules.csv
      module_progress.csv
      time_entries.csv
  app/
    main.py
    pages/
      01_dashboard.py
      02_data_entry.py
      03_catalog_import.py
    components/
      filters.py
      charts.py
      tables.py
    services/
      duckdb_service.py
      metrics_service.py
      progress_service.py
      ingestion_service.py
    models/
      schemas.py
      enums.py
    config.py
  scripts/
    import_microsoft_learn.py
    bootstrap_data.py
  tests/
    test_metrics_service.py
    test_progress_service.py
    test_ingestion_service.py
    fixtures/
      sample_users.csv
      sample_modules.csv
      sample_time_entries.csv
      sample_module_progress.csv
```

## 4.1 Dockerfile (Local Reproducibility)

Even without deployment, include a `Dockerfile` so the app can run in a consistent environment.

Dockerfile baseline:
- Base image: Python 3.12 slim
- Set working directory to `/app`
- Copy `pyproject.toml` and lock file first for dependency layer caching
- Install dependencies
- Copy project files
- Expose Streamlit port `8501`
- Default command to run dashboard app

Example runtime command:

```powershell
docker build -t certification-tracker .
docker run --rm -p 8501:8501 certification-tracker
```

## 5. Data Model (CSV + DuckDB)

### 5.1 `users.csv`
- `user_id` (PK)
- `display_name`
- `active` (bool)

### 5.2 `certification_tracks.csv`
- `track_id` (PK) (example: `az-104`)
- `provider` (example: `microsoft`)
- `track_name`
- `exam_code` (example: `AZ-104`)

### 5.3 `learning_paths.csv`
- `path_id` (PK)
- `track_id` (FK -> certification_tracks.track_id)
- `path_name`
- `provider_url`

### 5.4 `modules.csv`
- `module_id` (PK)
- `path_id` (FK -> learning_paths.path_id)
- `track_id` (FK -> certification_tracks.track_id)
- `module_name`
- `provider_url`
- `module_order` (int)

### 5.5 `module_progress.csv`
- `entry_id` (PK)
- `user_id` (FK -> users.user_id)
- `module_id` (FK -> modules.module_id)
- `status` (`not_seen|seen|mastered`)
- `updated_at` (ISO timestamp)

Notes:
- Keep latest status per `(user_id, module_id)` using max `updated_at`.

### 5.6 `time_entries.csv`
- `entry_id` (PK)
- `user_id` (FK -> users.user_id)
- `track_id` (FK -> certification_tracks.track_id)
- `module_id` (nullable FK -> modules.module_id)
- `minutes_spent` (int, > 0)
- `entry_date` (YYYY-MM-DD)
- `created_at` (ISO timestamp)

Notes:
- Multiple entries per day/user/module are allowed and aggregated in queries.

## 6. Dashboard Requirements

Global filters:
- Date range
- User (single or all)
- Track (single or all)

### 6.1 Time Tracking Section
- KPI cards:
  - Total study time (minutes/hours)
  - Daily total (selected day or latest day)
  - Weekly total (current week)
- Charts:
  - Weekly time bar chart
  - Daily trend line (optional in MVP if quick to add)
- Breakdowns:
  - Per user
  - Per module
  - Per track
  - All users combined

### 6.2 Progress Tracking Section
- Module status distribution:
  - Pie chart of `not_seen/seen/mastered`
- Completion by entity:
  - Horizontal bar chart (by track, learning path, or user based on filter mode)
- Progress score mapping:
  - `not_seen = 0.0`
  - `seen = 0.5`
  - `mastered = 1.0`
- Completion percentage:
  - `sum(status_score) / total_modules * 100`

## 7. Data Entry UX (Clicks and Selects)

### 7.1 Time Entry Form
- Inputs:
  - User (select)
  - Track (select)
  - Module (select, optional)
  - Date (date picker)
  - Minutes spent (number input)
- Action:
  - Save button appends row to `time_entries.csv`

### 7.2 Module Progress Update Form
- Inputs:
  - User (select)
  - Track (select)
  - Learning path (select)
  - Module (select)
  - Status (radio/select: `not_seen`, `seen`, `mastered`)
- Action:
  - Save button appends row to `module_progress.csv`
  - Dashboard resolves latest status per module/user

## 8. Manual Catalog Import Workflow (API-Based)

Initial focus: Microsoft Learn tracks (example: `AZ-104`) using:
- `https://learn.microsoft.com/api/catalog/`
    (documentation: https://learn.microsoft.com/en-us/training/support/catalog-api-developer-reference)

Workflow:
1. User selects the target track/exam (for example `AZ-104`).
2. Import script calls the Microsoft Learn Catalog API.
3. Script filters and maps API entities into learning paths and modules.
4. Script writes normalized rows into:
   - `certification_tracks.csv`
   - `learning_paths.csv`
   - `modules.csv`
5. User reviews and commits CSV changes.

Implementation note:
- Keep importer idempotent by upserting on stable IDs (provider + catalog item ID/URL slug).
- Keep provider-specific API mapping isolated so we can add other cloud providers later.

## 9. Modular Implementation Plan

### Phase 1 - Foundations
- Create project scaffolding and Python package layout.
- Add schema definitions and CSV bootstrap script.
- Add DuckDB access layer for loading/querying CSVs.

### Phase 2 - Dashboard MVP
- Implement dashboard with filters.
- Add time tracking KPIs + weekly bar + table breakdowns.
- Add progress pie + horizontal bar.

### Phase 3 - Data Entry
- Add form page for time entries.
- Add form page for module status updates.
- Add validations (required fields, positive minutes, valid status).

### Phase 4 - Catalog Import
- Add Microsoft Learn Catalog API importer for selected tracks/exam codes.
- Add deduplication/idempotency checks.

### Phase 5 - Test Coverage
- Unit tests for:
  - Status score and completion calculations
  - Time aggregation (daily/weekly/total)
  - Import normalization and deduplication
- Smoke test: app loads with fixture CSVs.

## 10. Unified Execution Checklist

### 10.1 Environment And Infrastructure

- [x] Install required tooling (Git, Python 3.12+, `uv`, optional Docker Desktop).
- [x] Configure repository trust:
  - `git config --global --add safe.directory C:/Users/lsant/Documents/repositories/certification-tracker`
- [x] Create local environment and install dependencies:
  - `uv venv`
  - `.venv\Scripts\Activate.ps1`
  - `uv sync`
- [x] Create initial project files:
  - `pyproject.toml`
  - `uv.lock`
  - `.python-version`
- [x] Scaffold folders from Section 4 (`app/`, `data/`, `scripts/`, `tests/`).
- [x] Bootstrap CSV source files with headers:
  - `users.csv`
  - `certification_tracks.csv`
  - `learning_paths.csv`
  - `modules.csv`
  - `module_progress.csv`
  - `time_entries.csv`
- [x] Add baseline app shell and config:
  - `app/main.py`
  - `app/services/duckdb_service.py`
  - `.env.example`
- [x] Add quality tooling baseline:
  - `pytest`
  - `ruff`
  - `mypy`
- [x] Add `Dockerfile` and `.dockerignore`.
- [x] Validate with `uv run pytest`.
- [x] Validate importability with `uv run python -c "from app.main import main; print('app-import-ok')"`.
- [x] Validate Streamlit startup (`uv run streamlit run app/main.py`; command is long-running).
- [ ] Validate Docker image build (`docker build -t certification-tracker .`).

### 10.2 Product And Architecture Decisions

- [x] Chart library selected: Plotly.
- [x] Weekly boundary selected: Monday (`date_trunc('week', ...)`).
- [x] CSV row IDs selected: UUID (`uuid4`).
- [x] Catalog ingestion source selected: Microsoft Learn Catalog API (`https://learn.microsoft.com/api/catalog/`).

### 10.3 Delivered Implementation

- [x] Finish Phase 1 foundations:
  - [x] Add `app/models/schemas.py`
  - [x] Add `app/models/enums.py`
  - [x] Add `app/services/metrics_service.py`
  - [x] Add `app/services/progress_service.py`
  - [x] Add seed fixture data for 2 users and 1 track (`AZ-104`)
- [x] Build Phase 2 dashboard MVP:
  - [x] Add global filters (date, user, track)
  - [x] Add time section (total/daily/weekly + weekly bar + breakdown tables)
  - [x] Add progress section (pie + horizontal bar)
- [x] Build Phase 3 data entry:
  - [x] Add time entry form (append to `time_entries.csv`)
  - [x] Add status update form (append to `module_progress.csv`)
  - [x] Add input validation rules
- [x] Add tests for new logic:
  - [x] Aggregations (daily/weekly/total)
  - [x] Latest-status resolution per `(user_id, module_id)`
  - [x] Progress percentage scoring
- [x] Apply package-first import fix:
  - [x] Configure build system/package discovery in `pyproject.toml`
  - [x] Run `uv sync` to install project package
  - [x] Remove temporary `sys.path` workarounds

### 10.4 Next Steps (Current)

- [x] Implement Microsoft Learn Catalog API importer in `scripts/import_microsoft_learn.py`:
  - [x] Add pagination support
  - [x] Add retry/error handling
- [x] Map API entities into normalized records:
  - [x] `certification_tracks.csv`
  - [x] `learning_paths.csv`
  - [x] `modules.csv`
- [x] Implement idempotent upsert/dedup strategy for catalog imports.
- [x] Add import controls in `app/pages/03_catalog_import.py` (track/exam input + run import).
- [x] Add fixture-based tests for API mapping and deduplication behavior.
- [x] Run validation suite after importer work:
  - [x] `uv run pytest`
  - [x] `uv run ruff check .`
  - [x] `uv run mypy app scripts`

## 11. Testing Strategy (No CI for now)

Run tests locally before commits:

```powershell
uv run pytest
```

Minimum expected tests:
- Metrics aggregation correctness with fixed fixture data
- Progress rollup correctness for mixed statuses
- CSV read/write integrity for append operations
- Import mapping behavior for representative Microsoft Learn Catalog API responses/snapshots

## 12. Risks and Mitigations

- CSV merge conflicts:
  - Mitigation: append-only writes, small file granularity, frequent commits
- External API schema/field changes on Learn catalog:
  - Mitigation: keep API mapping isolated and covered by fixture-based tests
- Data consistency:
  - Mitigation: centralized validation in service layer + schema checks in tests

## 13. Definition of Done (MVP)

MVP is done when:
- Two users can log time and module status using UI controls only.
- Dashboard shows:
  - Aggregate/daily/weekly time
  - Weekly bar chart
  - Per-user/per-module/per-track breakdowns
  - Progress pie and horizontal bar charts
- AZ-104 catalog can be imported manually from Microsoft Learn into CSVs.
- Local test suite passes.
