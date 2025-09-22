"""
Script di build per creare eseguibili con PyInstaller.
Supporta Windows, macOS e Linux.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def get_platform_info():
    """Restituisce informazioni sulla piattaforma corrente."""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == "windows":
        ext = ".exe"
        separator = ";"
    else:
        ext = ""
        separator = ":"
    
    return system, arch, ext, separator


def clean_build_dirs():
    """Pulisce le directory di build precedenti."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Rimozione directory: {dir_name}")
            shutil.rmtree(dir_name)
    
    # Rimuovi anche i file .spec
    for spec_file in Path(".").glob("*.spec"):
        print(f"Rimozione file spec: {spec_file}")
        spec_file.unlink()


def create_pyinstaller_command():
    """Crea il comando PyInstaller per la build."""
    system, arch, ext, separator = get_platform_info()
    
    # Comando base
    cmd = [
        "pyinstaller",
        "--onefile",  # Crea un singolo eseguibile
        "--windowed" if system == "windows" else "--console",  # GUI su Windows, console su altri
        "--name", f"FileOrganizer{ext}",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
    ]
    
    # Aggiungi i dati necessari
    data_files = [
        ("assets", "assets"),  # Include la cartella assets
    ]
    
    for src, dst in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{separator}{dst}"])
    
    # Moduli nascosti che potrebbero essere necessari
    hidden_imports = [
        "PyQt6.QtCore",
        "PyQt6.QtGui", 
        "PyQt6.QtWidgets",
        "rapidfuzz",
        "yaml",
        "csv",
        "datetime",
        "pathlib",
        "threading",
    ]
    
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])
    
    # Esclusioni per ridurre la dimensione
    excludes = [
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PIL",
        "cv2",
    ]
    
    for module in excludes:
        cmd.extend(["--exclude-module", module])
    
    # Opzioni specifiche per piattaforma
    if system == "windows":
        if os.path.exists("assets/icon.ico"):
            cmd.extend(["--icon", "assets/icon.ico"])
        if os.path.exists("version_info.txt"):
            cmd.extend(["--version-file", "version_info.txt"])
    
    elif system == "darwin":  # macOS
        if os.path.exists("assets/icon.icns"):
            cmd.extend(["--icon", "assets/icon.icns"])
    
    # File principale
    cmd.append("main.py")
    
    return cmd


def create_version_info():
    """Crea il file version_info per Windows."""
    if platform.system().lower() != "windows":
        return
    
    version_info = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'File Organizer'),
        StringStruct(u'FileDescription', u'Organizzatore File Aziendali'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'FileOrganizer'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
        StringStruct(u'OriginalFilename', u'FileOrganizer.exe'),
        StringStruct(u'ProductName', u'File Organizer'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_info)
    
    print("File version_info.txt creato per Windows")


def create_icon_files():
    """Crea file icona di base se non esistono."""
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    # Crea un'icona SVG semplice se non esiste
    icon_svg = assets_dir / "icon.svg"
    if not icon_svg.exists():
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" rx="8" fill="#4CAF50"/>
  <path d="M16 20h32v4H16zm0 8h32v4H16zm0 8h24v4H16zm0 8h28v4H16z" fill="white"/>
  <circle cx="48" cy="40" r="8" fill="#FF9800"/>
  <path d="M44 36l4 4 8-8" stroke="white" stroke-width="2" fill="none"/>
</svg>"""
        
        with open(icon_svg, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        print(f"Icona SVG creata: {icon_svg}")


def run_build():
    """Esegue la build dell'applicazione."""
    print("=== File Organizer - Script di Build ===")
    print(f"Piattaforma: {platform.system()} {platform.machine()}")
    print()
    
    # Verifica che PyInstaller sia installato
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERRORE: PyInstaller non trovato. Installalo con: pip install pyinstaller")
        return 1
    
    # Pulisci le directory precedenti
    print("1. Pulizia directory di build...")
    clean_build_dirs()
    
    # Crea file necessari
    print("2. Creazione file di supporto...")
    create_icon_files()
    create_version_info()
    
    # Crea il comando PyInstaller
    print("3. Preparazione comando PyInstaller...")
    cmd = create_pyinstaller_command()
    
    print("Comando PyInstaller:")
    print(" ".join(cmd))
    print()
    
    # Esegui PyInstaller
    print("4. Esecuzione PyInstaller...")
    try:
        result = subprocess.run(cmd, check=True)
        print("Build completata con successo!")
        
        # Mostra informazioni sull'eseguibile creato
        system, arch, ext, _ = get_platform_info()
        exe_path = Path("dist") / f"FileOrganizer{ext}"
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nEseguibile creato: {exe_path}")
            print(f"Dimensione: {size_mb:.1f} MB")
            
            # Test rapido dell'eseguibile
            print("\n5. Test dell'eseguibile...")
            try:
                test_result = subprocess.run([str(exe_path), "--help"], 
                                           capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    print("✓ Test CLI riuscito")
                else:
                    print("⚠ Test CLI fallito")
            except subprocess.TimeoutExpired:
                print("⚠ Test CLI timeout")
            except Exception as e:
                print(f"⚠ Errore nel test: {e}")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"ERRORE nella build: {e}")
        return 1


def create_installer_script():
    """Crea uno script per l'installazione."""
    system, arch, ext, _ = get_platform_info()
    
    if system == "windows":
        # Script batch per Windows
        script_content = f"""@echo off
echo File Organizer - Installer
echo.

set "INSTALL_DIR=%PROGRAMFILES%\\FileOrganizer"
set "DESKTOP_LINK=%USERPROFILE%\\Desktop\\File Organizer.lnk"
set "STARTMENU_LINK=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\File Organizer.lnk"

echo Installazione in: %INSTALL_DIR%
echo.

REM Crea la directory di installazione
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copia l'eseguibile
copy "FileOrganizer{ext}" "%INSTALL_DIR%\\" >nul
if errorlevel 1 (
    echo ERRORE: Impossibile copiare l'eseguibile
    pause
    exit /b 1
)

REM Crea collegamenti (richiede PowerShell)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_LINK%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\FileOrganizer{ext}'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU_LINK%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\FileOrganizer{ext}'; $Shortcut.Save()"

echo.
echo Installazione completata!
echo - Eseguibile: %INSTALL_DIR%\\FileOrganizer{ext}
echo - Collegamento Desktop: %DESKTOP_LINK%
echo - Collegamento Start Menu: %STARTMENU_LINK%
echo.
pause
"""
        
        with open("dist/install.bat", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print("Script di installazione Windows creato: dist/install.bat")
    
    else:
        # Script shell per Unix/Linux/macOS
        script_content = f"""#!/bin/bash
echo "File Organizer - Installer"
echo

INSTALL_DIR="/usr/local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/file-organizer.desktop"

echo "Installazione in: $INSTALL_DIR"
echo

# Copia l'eseguibile (richiede sudo)
sudo cp FileOrganizer{ext} "$INSTALL_DIR/"
if [ $? -ne 0 ]; then
    echo "ERRORE: Impossibile copiare l'eseguibile (serve sudo)"
    exit 1
fi

# Rendi eseguibile
sudo chmod +x "$INSTALL_DIR/FileOrganizer{ext}"

# Crea file desktop per Linux
if [ "$OSTYPE" = "linux-gnu"* ]; then
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=File Organizer
Comment=Organizzatore File Aziendali
Exec=$INSTALL_DIR/FileOrganizer{ext}
Icon=folder
Terminal=false
Type=Application
Categories=Utility;FileManager;
EOF
    echo "File desktop creato: $DESKTOP_FILE"
fi

echo
echo "Installazione completata!"
echo "- Eseguibile: $INSTALL_DIR/FileOrganizer{ext}"
echo "- Comando: FileOrganizer{ext}"
echo
"""
        
        with open("dist/install.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # Rendi eseguibile
        os.chmod("dist/install.sh", 0o755)
        
        print("Script di installazione Unix creato: dist/install.sh")


def main():
    """Funzione principale dello script di build."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            print("Pulizia directory di build...")
            clean_build_dirs()
            return 0
        elif sys.argv[1] == "installer":
            print("Creazione script di installazione...")
            create_installer_script()
            return 0
    
    # Esegui la build
    result = run_build()
    
    if result == 0:
        # Crea anche lo script di installazione
        create_installer_script()
        
        print("\n=== Build Completata ===")
        print("File creati nella directory 'dist/':")
        
        for file_path in Path("dist").glob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  - {file_path.name} ({size_mb:.1f} MB)")
        
        print("\nPer installare l'applicazione:")
        system, _, _, _ = get_platform_info()
        if system == "windows":
            print("  Esegui: dist\\install.bat")
        else:
            print("  Esegui: ./dist/install.sh")
    
    return result


if __name__ == "__main__":
    sys.exit(main())