# RX_PM Reporting

## Run everything at once

The runner uses local PostgreSQL only. Current default aliases:

- `AG_Dev` -> local database `AG_Dev`
- `Telios_LMS_Dev` -> local database `LMS_Survey_Dev`

### Windows PowerShell
```powershell
cd D:\git-projects\rx_pm
.\run_all.ps1 
```

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
