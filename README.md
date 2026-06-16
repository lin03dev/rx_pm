# RX_PM Reporting

## App layout

- `backend/` - FastAPI API for listing databases/reports and generating report files.
- `frontend/` - React UI for selecting and generating reports.

### Start the backend

From the repo root:

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\pip.exe install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Or from inside `backend/`:

```powershell
cd D:\git-projects\rx_pm\backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start the frontend

```powershell
cd D:\git-projects\rx_pm\frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## Batch report generation (CLI)

The scripts below generate Excel reports offline. They do **not** start the web dashboard.

Uses local PostgreSQL dev aliases by default:

- `AG_Dev` -> local database `AG_Dev`
- `LMS_Dev` -> local database `LMS_Survey_Dev`
- `Telios_Dev` -> local database `Telios_Dev`

### Windows PowerShell
```powershell
cd D:\git-projects\rx_pm
.\backend\run_all.ps1 
```

The Windows runner creates `.\venv` automatically from Python 3.10. It first
tries the Windows Python launcher (`py -3.10`), then falls back to the currently
active `python` or `python3` if that interpreter is Python 3.10.

### Git Bash / WSL
```bash
cd ~/workspace/git-projects/rx_pm
source venv/bin/activate
./backend/run_all.sh
```

## If you already have a Python 3.10 virtual environment
Activate it first and then run the Windows script:

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\Activate.ps1
.\backend\run_all.ps1
```
