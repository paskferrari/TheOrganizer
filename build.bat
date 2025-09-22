@echo off
REM Script di build per Windows
REM Installa le dipendenze e crea l'eseguibile

echo File Organizer - Build Script per Windows
echo ========================================
echo.

REM Controlla se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato. Installa Python 3.10+ da python.org
    pause
    exit /b 1
)

REM Controlla se pip è disponibile
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: pip non trovato. Reinstalla Python con pip incluso.
    pause
    exit /b 1
)

echo 1. Installazione dipendenze...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRORE: Installazione dipendenze fallita
    pause
    exit /b 1
)

echo.
echo 2. Esecuzione build...
python build.py
if errorlevel 1 (
    echo ERRORE: Build fallita
    pause
    exit /b 1
)

echo.
echo Build completata! Controlla la directory 'dist' per l'eseguibile.
echo.
pause