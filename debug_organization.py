#!/usr/bin/env python3
"""
Script di debug per testare l'organizzazione dei file
"""

import os
import sys
from pathlib import Path
from core import FileOrganizerCore

def test_organization():
    """Test dell'organizzazione dei file"""
    
    # Percorsi
    test_dir = Path("test_files")
    output_dir = Path("test_output")
    
    # Crea l'organizzatore
    organizer = FileOrganizerCore(threshold=70.0, dry_run=False)
    
    # Aggiungi alcune aziende
    organizer.add_company("ACME Corp", ["ACME", "Acme Corporation"])
    organizer.add_company("Microsoft", ["Microsoft Corp", "MS"])
    
    print(f"Directory di test: {test_dir.absolute()}")
    print(f"Directory di output: {output_dir.absolute()}")
    
    # Verifica che i file di test esistano
    if not test_dir.exists():
        print(f"ERRORE: Directory di test {test_dir} non trovata!")
        return
    
    files = list(test_dir.glob("*"))
    print(f"File trovati nella directory di test: {len(files)}")
    for file in files:
        print(f"  - {file.name}")
    
    if not files:
        print("ERRORE: Nessun file trovato nella directory di test!")
        return
    
    # Esegui l'organizzazione
    print("\n--- Avvio organizzazione ---")
    
    def progress_callback(phase, current, total):
        print(f"{phase}: {current}/{total}")
    
    try:
        result = organizer.organize_files(
            str(test_dir.absolute()),
            str(output_dir.absolute()),
            progress_callback=progress_callback
        )
        
        print(f"\n--- Risultati ---")
        print(f"File totali: {result.total_files}")
        print(f"File processati: {result.processed_files}")
        print(f"Spostamenti riusciti: {result.successful_moves}")
        print(f"Spostamenti falliti: {result.failed_moves}")
        print(f"File saltati: {result.skipped_files}")
        print(f"Errori: {len(result.errors)}")
        
        if result.errors:
            print("\nErrori:")
            for error in result.errors:
                print(f"  - {error}")
        
        print(f"\nMatch trovati: {len(result.matches)}")
        for match in result.matches:
            print(f"  - {match.file_path}")
            print(f"    Azienda: {match.company_name}")
            print(f"    Score: {match.match_score}")
            print(f"    Testo matchato: {match.matched_text}")
            print(f"    Categoria: {match.category}")
            print(f"    Percorso suggerito: {match.suggested_path}")
            print()
        
        # Verifica la struttura di output
        if output_dir.exists():
            print("--- Struttura di output ---")
            for root, dirs, files in os.walk(output_dir):
                level = root.replace(str(output_dir), '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")
        
    except Exception as e:
        print(f"ERRORE durante l'organizzazione: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_organization()