# RX_PM Backend

FastAPI wrapper around the existing reporting engine.

## Run

```powershell
cd D:\git-projects\rx_pm
.\venv\Scripts\pip.exe install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API base URL: `http://127.0.0.1:8000`

Useful endpoints:

- `GET /api/health`
- `GET /api/reports`
- `GET /api/databases`
- `POST /api/reports/generate`
