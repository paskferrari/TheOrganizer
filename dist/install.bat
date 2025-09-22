@echo off
echo File Organizer - Installer
echo.

set "INSTALL_DIR=%PROGRAMFILES%\FileOrganizer"
set "DESKTOP_LINK=%USERPROFILE%\Desktop\File Organizer.lnk"
set "STARTMENU_LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\File Organizer.lnk"

echo Installazione in: %INSTALL_DIR%
echo.

REM Crea la directory di installazione
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copia l'eseguibile
copy "FileOrganizer.exe" "%INSTALL_DIR%\" >nul
if errorlevel 1 (
    echo ERRORE: Impossibile copiare l'eseguibile
    pause
    exit /b 1
)

REM Crea collegamenti (richiede PowerShell)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_LINK%'); $Shortcut.TargetPath = '%INSTALL_DIR%\FileOrganizer.exe'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_LINK%'); $Shortcut.TargetPath = '%INSTALL_DIR%\FileOrganizer.exe'; $Shortcut.Save()"

echo.
echo Installazione completata!
echo - Eseguibile: %INSTALL_DIR%\FileOrganizer.exe
echo - Collegamento Desktop: %DESKTOP_LINK%
echo - Collegamento Start Menu: %STARTMENU_LINK%
echo.
pause
