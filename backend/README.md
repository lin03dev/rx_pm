# RX_PM Backend

FastAPI wrapper around the existing reporting engine.

## Run

From the repo root:

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\pip.exe install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Or from this `backend/` folder:

```powershell
cd D:\git-projects\rx_pm\backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API base URL: `http://127.0.0.1:8000`

Useful endpoints:

- `GET /api/health`
- `GET /api/reports` — list configured reports
- `GET /api/databases` — list database connections
- `GET /api/dashboard/insights` — KPIs for a database
- `POST /api/reports/generate` — generate a report file
- `POST /api/reports/preview` — preview report rows in the UI

Database connections can be managed via `/api/connections` (see `config/user_connections.yaml`).

Schema reference for AG, LMS, and Telios lives in `config/schema_registry.yaml`. This file is the single source of truth for:

- **Table/column allowlists** per database system (`systems`)
- **Report catalogue** — module, class, filters, category (`report_definitions` + `report_categories`)
- **Report-to-database routing** (derived from `category` in `report_definitions`; `cross_db_reports` for enrichments)
- **Report output definitions** (`report_definitions`) — columns, schema refs, Excel layout, conditional formatting

Report output templates are **generated from** `report_definitions`, not maintained separately. Generate blank layout workbooks with:

```powershell
.\venv\Scripts\python.exe backend\scripts\generate_report_templates.py
```

Validate schema refs and column definitions:

```powershell
.\venv\Scripts\python.exe backend\scripts\preflight_check.py
```

CLI runners:

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\python.exe backend\run.py --list-reports
.\venv\Scripts\python.exe backend\run.py --report user-activity --database AG_Dev
.\backend\run_all.ps1   # full offline batch pipeline
```

`backend/main.py` is a legacy CLI for template generation and Excel uploads; the web dashboard uses `app/main.py`.
