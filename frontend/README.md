# RX_PM Frontend

React dashboard for RX_PM reporting.

## Layout

- **Project tabs**: AG, LMS, Telios, Language, Utility
- **Report list** inside each project
- **Sub-tabs**: Data, Generate, History
- **Database bar**: select a DB to load insights and report data

## Run

```powershell
cd D:\git-projects\rx_pm\frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. Start the backend first (see root `README.md`).
