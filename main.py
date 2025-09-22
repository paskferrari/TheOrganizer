#!/usr/bin/env python3
"""
File Organizer - Organizzatore File Aziendali
Entry point principale che supporta sia CLI che GUI.

Utilizzo:
- Da terminale: python main.py [argomenti CLI]
- Doppio click: avvia la GUI
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path per gli import
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def is_gui_mode():
    """
    Determina se avviare in modalità GUI.
    
    Returns:
        bool: True se deve avviare la GUI, False per CLI
    """
    # Se non ci sono argomenti da riga di comando, avvia la GUI
    if len(sys.argv) == 1:
        return True
    
    # Se il primo argomento è 'gui', avvia la GUI
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'gui':
        return True
    
    # Altrimenti usa la CLI
    return False


def main():
    """Funzione principale che decide se avviare CLI o GUI."""
    try:
        if is_gui_mode():
            # Avvia la GUI
            try:
                from gui import main as gui_main
                return gui_main()
            except ImportError as e:
                print(f"Errore nell'importazione della GUI: {e}")
                print("Assicurati che PyQt6 sia installato: pip install PyQt6")
                return 1
            except Exception as e:
                print(f"Errore nell'avvio della GUI: {e}")
                return 1
        else:
            # Avvia la CLI
            try:
                from cli import main as cli_main
                return cli_main()
            except ImportError as e:
                print(f"Errore nell'importazione della CLI: {e}")
                return 1
            except Exception as e:
                print(f"Errore nell'avvio della CLI: {e}")
                return 1
                
    except KeyboardInterrupt:
        print("\nOperazione interrotta dall'utente.")
        return 130
    except Exception as e:
        print(f"Errore critico: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())