@echo off
title Portal Vente - servidor local
cd /d "%~dp0"

rem Arranca el servidor local solo si nadie esta escuchando en el puerto 8123
powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 8123 -State Listen -ErrorAction SilentlyContinue)) { Start-Process -FilePath 'python' -ArgumentList '-m','http.server','8123' -WorkingDirectory '%~dp0' -WindowStyle Minimized; Write-Host 'Servidor local iniciado en el puerto 8123' } else { Write-Host 'El servidor local ya esta corriendo' }"

rem Espera a que el servidor responda antes de abrir el portal
timeout /t 2 /nobreak >nul
start "" "http://localhost:8123/index.html"
