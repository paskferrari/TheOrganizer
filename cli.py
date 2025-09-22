"""
Interfaccia a riga di comando per il File Organizer.
Fornisce accesso completo alle funzionalità tramite CLI.
"""

import argparse
import sys
import os
from datetime import datetime, date
from pathlib import Path
from typing import List, Set

from core import FileOrganizerCore
from io_ops import FileOperationLogger, UndoManager
from config import get_config_manager
from normalize import generate_company_aliases


def parse_date(date_string: str) -> date:
    """
    Converte una stringa in data.
    
    Args:
        date_string: Stringa data in formato YYYY-MM-DD
        
    Returns:
        Oggetto date
        
    Raises:
        ValueError: Se il formato non è valido
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Formato data non valido: {date_string}. Usa YYYY-MM-DD")


def parse_extensions(extensions_string: str) -> Set[str]:
    """
    Converte una stringa di estensioni in un set.
    
    Args:
        extensions_string: Estensioni separate da virgola (es. "pdf,docx,xlsx")
        
    Returns:
        Set di estensioni normalizzate
    """
    if not extensions_string:
        return set()
    
    extensions = set()
    for ext in extensions_string.split(','):
        ext = ext.strip()
        if ext:
            if not ext.startswith('.'):
                ext = '.' + ext
            extensions.add(ext.lower())
    
    return extensions


def print_progress(phase: str, current: int, total: int):
    """
    Stampa il progresso dell'operazione.
    
    Args:
        phase: Fase corrente
        current: Numero corrente
        total: Totale
    """
    if total > 0:
        percentage = (current / total) * 100
        print(f"\r{phase} [{current}/{total}] {percentage:.1f}%", end='', flush=True)
    else:
        print(f"\r{phase} {current}", end='', flush=True)


def organize_command(args):
    """Esegue il comando di organizzazione."""
    config_manager = get_config_manager()
    
    # Validazione parametri
    root_path = Path(args.root_path)
    if not root_path.exists() or not root_path.is_dir():
        print(f"Errore: Directory non valida: {args.root_path}")
        return 1
    
    output_path = Path(args.output_path) if args.output_path else root_path
    
    # Parsing delle date
    since_date = None
    until_date = None
    
    if args.since:
        try:
            since_date = parse_date(args.since)
        except ValueError as e:
            print(f"Errore: {e}")
            return 1
    
    if args.until:
        try:
            until_date = parse_date(args.until)
        except ValueError as e:
            print(f"Errore: {e}")
            return 1
    
    # Validazione date
    if since_date and until_date and since_date > until_date:
        print("Errore: La data 'since' deve essere precedente alla data 'until'")
        return 1
    
    # Parsing estensioni
    include_extensions = parse_extensions(args.include_extensions) if args.include_extensions else None
    exclude_extensions = parse_extensions(args.exclude_extensions) if args.exclude_extensions else None
    
    # Inizializza l'organizzatore
    organizer = FileOrganizerCore(threshold=args.threshold, dry_run=args.dry_run)
    
    # Configura i filtri
    organizer.set_filters(
        include_extensions=include_extensions,
        exclude_extensions=exclude_extensions,
        exclude_folders=set(args.exclude_folders) if args.exclude_folders else None,
        max_file_size_mb=args.max_size_mb
    )
    
    # Aggiungi l'azienda
    aliases = []
    if args.aliases:
        aliases = [alias.strip() for alias in args.aliases.split(',') if alias.strip()]
    
    organizer.add_company(args.company, aliases)
    
    # Configura il logging se non è dry run
    if not args.dry_run:
        log_file = args.log_file or f"file_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        logger = FileOperationLogger(log_file)
        organizer.set_logger(logger)
        print(f"Log delle operazioni: {log_file}")
    
    # Esegui l'organizzazione
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Organizzazione file...")
    print(f"Directory sorgente: {root_path}")
    print(f"Directory destinazione: {output_path}")
    print(f"Azienda: {args.company}")
    if aliases:
        print(f"Alias: {', '.join(aliases)}")
    print(f"Soglia matching: {args.threshold}%")
    
    if since_date:
        print(f"Data inizio: {since_date}")
    if until_date:
        print(f"Data fine: {until_date}")
    
    print()
    
    try:
        result = organizer.organize_files(
            str(root_path),
            str(output_path),
            since_date=since_date,
            until_date=until_date,
            progress_callback=print_progress
        )
        
        print()  # Nuova riga dopo il progresso
        
        # Stampa i risultati
        print("\n" + "="*50)
        print("RISULTATI ORGANIZZAZIONE")
        print("="*50)
        print(f"File totali trovati: {result.total_files}")
        print(f"File processati: {result.processed_files}")
        print(f"File saltati: {result.skipped_files}")
        
        if not args.dry_run:
            print(f"File spostati con successo: {result.successful_moves}")
            print(f"Errori nello spostamento: {result.failed_moves}")
        
        # Mostra i match trovati
        if result.matches:
            print(f"\nMATCH TROVATI ({len(result.matches)}):")
            print("-" * 80)
            for match in result.matches:
                status = "✓" if not args.dry_run else "→"
                print(f"{status} {match.file_path}")
                print(f"   Azienda: {match.company_name} (score: {match.match_score:.1f}%)")
                print(f"   Categoria: {match.category.value}")
                print(f"   Destinazione: {match.suggested_path}")
                if match.file_date:
                    print(f"   Data: {match.file_date}")
                print()
        
        # Mostra gli errori
        if result.errors:
            print(f"\nERRORI ({len(result.errors)}):")
            print("-" * 50)
            for error in result.errors:
                print(f"✗ {error}")
        
        print("\nOperazione completata!")
        return 0
        
    except Exception as e:
        print(f"\nErrore durante l'organizzazione: {e}")
        return 1


def undo_command(args):
    """Esegue il comando di undo."""
    log_file = Path(args.log_file)
    
    if not log_file.exists():
        print(f"Errore: File di log non trovato: {args.log_file}")
        return 1
    
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Annullamento operazioni da: {args.log_file}")
    
    try:
        undo_manager = UndoManager(dry_run=args.dry_run)
        undone_count, error_count, errors = undo_manager.undo_operations(str(log_file))
        
        print(f"\nOperazioni annullate: {undone_count}")
        print(f"Errori: {error_count}")
        
        if errors:
            print("\nErrori durante l'undo:")
            for error in errors:
                print(f"✗ {error}")
        
        print("\nUndo completato!")
        return 0
        
    except Exception as e:
        print(f"Errore durante l'undo: {e}")
        return 1


def list_companies_command(args):
    """Elenca le aziende salvate."""
    config_manager = get_config_manager()
    companies = config_manager.get_all_company_names()
    
    if not companies:
        print("Nessuna azienda salvata.")
        return 0
    
    print("AZIENDE SALVATE:")
    print("-" * 40)
    
    for company_name in sorted(companies):
        profile = config_manager.get_company_profile(company_name)
        print(f"• {company_name}")
        if profile.aliases:
            print(f"  Alias: {', '.join(profile.aliases)}")
        print(f"  Ultimo utilizzo: {profile.last_used.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    return 0


def add_company_command(args):
    """Aggiunge una nuova azienda."""
    config_manager = get_config_manager()
    
    aliases = []
    if args.aliases:
        aliases = [alias.strip() for alias in args.aliases.split(',') if alias.strip()]
    
    # Genera alias automatici se richiesto
    if args.auto_aliases:
        auto_aliases = generate_company_aliases(args.name)
        aliases.extend(auto_aliases)
        aliases = list(set(aliases))  # Rimuovi duplicati
    
    config_manager.add_company_profile(args.name, aliases)
    
    print(f"Azienda '{args.name}' aggiunta con successo!")
    if aliases:
        print(f"Alias: {', '.join(aliases)}")
    
    return 0


def remove_company_command(args):
    """Rimuove un'azienda."""
    config_manager = get_config_manager()
    
    if args.name not in config_manager.get_all_company_names():
        print(f"Errore: Azienda '{args.name}' non trovata.")
        return 1
    
    config_manager.remove_company_profile(args.name)
    print(f"Azienda '{args.name}' rimossa con successo!")
    
    return 0


def create_parser():
    """Crea il parser degli argomenti."""
    parser = argparse.ArgumentParser(
        description="File Organizer - Organizza file aziendali con matching fuzzy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  %(prog)s organize /path/to/files "Acme Corp" --threshold 80 --dry-run
  %(prog)s organize /path/to/files "Acme Corp" --since 2023-01-01 --until 2023-12-31
  %(prog)s undo operations_20231201_143022.csv
  %(prog)s add-company "Acme Corporation" --aliases "Acme,Acme Corp" --auto-aliases
  %(prog)s list-companies
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandi disponibili')
    
    # Comando organize
    organize_parser = subparsers.add_parser('organize', help='Organizza i file')
    organize_parser.add_argument('root_path', help='Percorso della directory da organizzare')
    organize_parser.add_argument('company', help='Nome dell\'azienda')
    organize_parser.add_argument('--output-path', '-o', help='Percorso di output (default: stesso di input)')
    organize_parser.add_argument('--threshold', '-t', type=float, default=92.0,
                               help='Soglia per il matching fuzzy (0-100, default: 92)')
    organize_parser.add_argument('--aliases', '-a', help='Alias dell\'azienda separati da virgola')
    organize_parser.add_argument('--since', help='Data inizio in formato YYYY-MM-DD')
    organize_parser.add_argument('--until', help='Data fine in formato YYYY-MM-DD')
    organize_parser.add_argument('--include-extensions', help='Estensioni da includere (es: pdf,docx,xlsx)')
    organize_parser.add_argument('--exclude-extensions', help='Estensioni da escludere (es: tmp,log)')
    organize_parser.add_argument('--exclude-folders', nargs='*', 
                               help='Cartelle da escludere')
    organize_parser.add_argument('--max-size-mb', type=float, 
                               help='Dimensione massima file in MB')
    organize_parser.add_argument('--dry-run', '-n', action='store_true',
                               help='Simula le operazioni senza eseguirle')
    organize_parser.add_argument('--log-file', help='File di log per le operazioni')
    
    # Comando undo
    undo_parser = subparsers.add_parser('undo', help='Annulla le operazioni da un file di log')
    undo_parser.add_argument('log_file', help='File di log CSV delle operazioni')
    undo_parser.add_argument('--dry-run', '-n', action='store_true',
                           help='Simula l\'undo senza eseguirlo')
    
    # Comando list-companies
    list_parser = subparsers.add_parser('list-companies', help='Elenca le aziende salvate')
    
    # Comando add-company
    add_parser = subparsers.add_parser('add-company', help='Aggiunge una nuova azienda')
    add_parser.add_argument('name', help='Nome dell\'azienda')
    add_parser.add_argument('--aliases', '-a', help='Alias separati da virgola')
    add_parser.add_argument('--auto-aliases', action='store_true',
                          help='Genera automaticamente gli alias')
    
    # Comando remove-company
    remove_parser = subparsers.add_parser('remove-company', help='Rimuove un\'azienda')
    remove_parser.add_argument('name', help='Nome dell\'azienda da rimuovere')
    
    return parser


def main():
    """Funzione principale della CLI."""
    parser = create_parser()
    
    # Se non ci sono argomenti, mostra l'help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    args = parser.parse_args()
    
    # Esegui il comando appropriato
    if args.command == 'organize':
        return organize_command(args)
    elif args.command == 'undo':
        return undo_command(args)
    elif args.command == 'list-companies':
        return list_companies_command(args)
    elif args.command == 'add-company':
        return add_company_command(args)
    elif args.command == 'remove-company':
        return remove_company_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())