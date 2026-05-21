@echo off
echo ========================================
echo  SaaS Engenharia - Ambiente Local
echo ========================================

echo.
echo [*] Iniciando Backend (FastAPI)...
cd apps\api
start cmd /k "python -m venv venv 2>nul & venv\Scripts\activate & pip install -r requirements.txt & uvicorn main:app --reload --port 8000"
cd ..\..

echo [*] Iniciando Frontend (Vite)...
cd apps\web
start cmd /k "npm install & npm run dev"
cd ..\..

echo.
echo [OK] Ambos os servidores estao iniciando em janelas separadas.
echo      Frontend: http://localhost:5173
echo      Backend:  http://localhost:8000
pause