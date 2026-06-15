# RX_PM Reporting

## App layout

- `backend/` - FastAPI API for listing databases/reports and generating report files.
- `frontend/` - React UI for selecting and generating reports.

### Start the backend

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\pip.exe install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start the frontend

```powershell
cd D:\git-projects\rx_pm\frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## Run everything at once

The runner uses local PostgreSQL only. Current default aliases:

- `AG_Dev` -> local database `AG_Dev`
- `Telios_LMS_Dev` -> local database `LMS_Survey_Dev`

### Windows PowerShell
```powershell
cd D:\git-projects\rx_pm
.\run_all.ps1 
```

The Windows runner creates `.\venv` automatically from Python 3.10. It first
tries the Windows Python launcher (`py -3.10`), then falls back to the currently
active `python` or `python3` if that interpreter is Python 3.10.

### Git Bash / WSL
```bash
cd ~/workspace/git-projects/rx_pm
source venv/bin/activate
./run_all.sh
```

## If you already have a Python 3.10 virtual environment
Activate it first and then run the Windows script:

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\Activate.ps1
.\run_all.ps1
```
