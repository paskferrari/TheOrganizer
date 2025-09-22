#!/bin/bash
# Script di build per Unix/Linux/macOS
# Installa le dipendenze e crea l'eseguibile

echo "File Organizer - Build Script per Unix/Linux/macOS"
echo "=================================================="
echo

# Controlla se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "ERRORE: Python 3 non trovato. Installa Python 3.10+ dal tuo package manager."
    exit 1
fi

# Controlla se pip è disponibile
if ! command -v pip3 &> /dev/null; then
    echo "ERRORE: pip3 non trovato. Installa pip3 dal tuo package manager."
    exit 1
fi

echo "1. Installazione dipendenze..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERRORE: Installazione dipendenze fallita"
    exit 1
fi

echo
echo "2. Esecuzione build..."
python3 build.py
if [ $? -ne 0 ]; then
    echo "ERRORE: Build fallita"
    exit 1
fi

echo
echo "Build completata! Controlla la directory 'dist' per l'eseguibile."
echo