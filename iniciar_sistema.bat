@echo off
setlocal
echo ========================================
echo  SaaS Engenharia - Ambiente Local
echo ========================================

:: Garante que o script funciona de qualquer diretorio
set "ROOT=%~dp0"

echo.
echo [*] Iniciando Backend (FastAPI)...
cd /d "%ROOT%apps\api"

:: Cria o venv apenas se nao existir (evita reinstalacao a cada boot)
if not exist "venv\Scripts\activate.bat" (
    echo     [venv] Criando ambiente virtual...
    python -m venv venv
    echo     [pip]  Instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Host explicito 127.0.0.1 para evitar conflito IPv4/IPv6 no Windows 11
start cmd /k "title Backend FastAPI && call venv\Scripts\activate.bat && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo [*] Iniciando Frontend (Vite)...
cd /d "%ROOT%apps\web"

:: Instala dependencias apenas se node_modules nao existir
if not exist "node_modules" (
    echo     [npm] Instalando dependencias...
    npm install
)

start cmd /k "title Frontend Vite && npm run dev"

cd /d "%ROOT%"

echo.
echo ========================================
echo  [OK] Servidores iniciando...
echo.
echo  Frontend : http://localhost:5173
echo  Backend  : http://127.0.0.1:8000
echo  API Docs : http://127.0.0.1:8000/docs
echo ========================================
echo.
pause
