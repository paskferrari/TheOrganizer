#!/usr/bin/env python3
"""
Test script per verificare il feedback migliorato dell'organizzatore file.
"""

import os
import sys
from pathlib import Path
from datetime import date

# Aggiungi il percorso del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import FileOrganizerCore

def test_no_company_configured():
    """Test con nessuna azienda configurata."""
    print("=== Test: Nessuna azienda configurata ===")
    
    organizer = FileOrganizerCore(threshold=0.8, dry_run=True)
    
    # Non aggiungiamo nessuna azienda
    print(f"Aziende configurate: {len(organizer.matcher.company_aliases)}")
    
    # Tenta di organizzare
    test_dir = Path("test_files")
    result = organizer.organize_files(str(test_dir), str(test_dir))
    
    print(f"File trovati: {result.total_files}")
    print(f"File processati: {result.processed_files}")
    print(f"Match trovati: {len(result.matches)}")
    print()

def test_no_matching_files():
    """Test con azienda configurata ma nessun file corrispondente."""
    print("=== Test: Azienda configurata, nessun file corrispondente ===")
    
    organizer = FileOrganizerCore(threshold=0.8, dry_run=True)
    
    # Aggiungi un'azienda che non corrisponde ai file di test
    organizer.add_company("Azienda Inesistente", ["Inesistente Corp"])
    print(f"Aziende configurate: {list(organizer.matcher.company_aliases.keys())}")
    
    # Tenta di organizzare
    test_dir = Path("test_files")
    result = organizer.organize_files(str(test_dir), str(test_dir))
    
    print(f"File trovati: {result.total_files}")
    print(f"File processati: {result.processed_files}")
    print(f"Match trovati: {len(result.matches)}")
    print()

def test_successful_organization():
    """Test con organizzazione riuscita."""
    print("=== Test: Organizzazione riuscita ===")
    
    organizer = FileOrganizerCore(threshold=0.8, dry_run=True)
    
    # Aggiungi aziende che corrispondono ai file di test
    organizer.add_company("ACME Corp", ["ACME", "Acme Corporation"])
    organizer.add_company("Microsoft", ["Microsoft Corp", "MS"])
    print(f"Aziende configurate: {list(organizer.matcher.company_aliases.keys())}")
    
    # Tenta di organizzare
    test_dir = Path("test_files")
    result = organizer.organize_files(str(test_dir), str(test_dir))
    
    print(f"File trovati: {result.total_files}")
    print(f"File processati: {result.processed_files}")
    print(f"Match trovati: {len(result.matches)}")
    
    if result.matches:
        print("Match trovati:")
        for match in result.matches:
            print(f"  - {match.file_path} -> {match.company_name} (score: {match.score:.2f})")
    print()

def main():
    """Esegue tutti i test."""
    print("Test del feedback migliorato per l'organizzatore file\n")
    
    # Verifica che i file di test esistano
    test_dir = Path("test_files")
    if not test_dir.exists():
        print("ERRORE: Cartella test_files non trovata!")
        return
    
    test_files = list(test_dir.glob("*"))
    print(f"File di test disponibili: {len(test_files)}")
    for f in test_files:
        print(f"  - {f.name}")
    print()
    
    # Esegui i test
    test_no_company_configured()
    test_no_matching_files()
    test_successful_organization()
    
    print("=== Riepilogo ===")
    print("I test mostrano i diversi scenari che possono causare")
    print("il problema dei file non organizzati:")
    print("1. Nessuna azienda configurata")
    print("2. Azienda configurata ma nessun file corrispondente")
    print("3. Organizzazione riuscita con match trovati")

if __name__ == "__main__":
    main()