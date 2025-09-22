"""
Modulo per le operazioni di I/O, logging e undo.
Gestisce lo spostamento dei file, il logging delle operazioni e la funzionalità di undo.
"""

import os
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class OperationType(Enum):
    """Tipi di operazioni sui file."""
    MOVE = "move"
    COPY = "copy"
    CREATE_DIR = "create_dir"


@dataclass
class FileOperation:
    """Rappresenta un'operazione su un file."""
    operation_type: OperationType
    original_path: str
    new_path: str
    timestamp: datetime
    success: bool = True
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Converte l'operazione in un dizionario per il CSV."""
        return {
            'operation_type': self.operation_type.value,
            'original_path': self.original_path,
            'new_path': self.new_path,
            'timestamp': self.timestamp.isoformat(),
            'success': str(self.success),
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'FileOperation':
        """Crea un'operazione da un dizionario CSV."""
        return cls(
            operation_type=OperationType(data['operation_type']),
            original_path=data['original_path'],
            new_path=data['new_path'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            success=data['success'].lower() == 'true',
            error_message=data.get('error_message', '')
        )


class FileOperationLogger:
    """Classe per il logging delle operazioni sui file."""
    
    CSV_HEADERS = [
        'operation_type', 'original_path', 'new_path', 
        'timestamp', 'success', 'error_message'
    ]
    
    def __init__(self, log_file_path: str):
        """
        Inizializza il logger.
        
        Args:
            log_file_path: Percorso del file di log CSV
        """
        self.log_file_path = Path(log_file_path)
        self.operations: List[FileOperation] = []
        
        # Crea la directory del log se non esiste
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_operation(self, operation: FileOperation):
        """
        Registra un'operazione nel log.
        
        Args:
            operation: Operazione da registrare
        """
        self.operations.append(operation)
        self._write_to_csv(operation)
    
    def _write_to_csv(self, operation: FileOperation):
        """
        Scrive un'operazione nel file CSV.
        
        Args:
            operation: Operazione da scrivere
        """
        file_exists = self.log_file_path.exists()
        
        try:
            with open(self.log_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.CSV_HEADERS)
                
                # Scrivi l'header se il file è nuovo
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(operation.to_dict())
        except Exception as e:
            print(f"Errore nella scrittura del log: {e}")
    
    def load_operations_from_csv(self, csv_file_path: str) -> List[FileOperation]:
        """
        Carica le operazioni da un file CSV.
        
        Args:
            csv_file_path: Percorso del file CSV
            
        Returns:
            Lista delle operazioni caricate
        """
        operations = []
        csv_path = Path(csv_file_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"File di log non trovato: {csv_file_path}")
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        operation = FileOperation.from_dict(row)
                        operations.append(operation)
                    except Exception as e:
                        print(f"Errore nel parsing della riga: {row}, errore: {e}")
        
        except Exception as e:
            raise Exception(f"Errore nella lettura del file CSV: {e}")
        
        return operations
    
    def get_operations(self) -> List[FileOperation]:
        """
        Ottiene tutte le operazioni registrate.
        
        Returns:
            Lista delle operazioni
        """
        return self.operations.copy()


class FileOrganizer:
    """Classe principale per l'organizzazione dei file."""
    
    def __init__(self, dry_run: bool = False):
        """
        Inizializza l'organizzatore.
        
        Args:
            dry_run: Se True, simula le operazioni senza eseguirle
        """
        self.dry_run = dry_run
        self.logger: Optional[FileOperationLogger] = None
    
    def set_logger(self, logger: FileOperationLogger):
        """
        Imposta il logger per le operazioni.
        
        Args:
            logger: Logger da utilizzare
        """
        self.logger = logger
    
    def create_directory_structure(self, base_path: str, company_name: str, 
                                 year: str, category: str) -> str:
        """
        Crea la struttura di directory per l'organizzazione.
        
        Args:
            base_path: Percorso base
            company_name: Nome dell'azienda
            year: Anno
            category: Categoria del file
            
        Returns:
            Percorso della directory creata
        """
        # Sanitizza i nomi per il filesystem
        safe_company = self._sanitize_filename(company_name)
        safe_category = self._sanitize_filename(category)
        
        # Crea il percorso: base_path/Azienda/Categoria/Anno
        dir_path = Path(base_path) / safe_company / safe_category / year
        
        if not self.dry_run:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Log dell'operazione di creazione directory
                if self.logger:
                    operation = FileOperation(
                        operation_type=OperationType.CREATE_DIR,
                        original_path="",
                        new_path=str(dir_path),
                        timestamp=datetime.now(),
                        success=True
                    )
                    self.logger.log_operation(operation)
                    
            except Exception as e:
                if self.logger:
                    operation = FileOperation(
                        operation_type=OperationType.CREATE_DIR,
                        original_path="",
                        new_path=str(dir_path),
                        timestamp=datetime.now(),
                        success=False,
                        error_message=str(e)
                    )
                    self.logger.log_operation(operation)
                raise
        
        return str(dir_path)
    
    def move_file(self, source_path: str, destination_dir: str, 
                  new_filename: str = None) -> Tuple[bool, str, str]:
        """
        Sposta un file nella directory di destinazione.
        
        Args:
            source_path: Percorso del file sorgente
            destination_dir: Directory di destinazione
            new_filename: Nuovo nome del file (opzionale)
            
        Returns:
            Tupla (successo, percorso_finale, messaggio_errore)
        """
        source = Path(source_path)
        dest_dir = Path(destination_dir)
        
        if not source.exists():
            return False, "", f"File sorgente non trovato: {source_path}"
        
        # Determina il nome del file finale
        if new_filename:
            filename = new_filename
        else:
            filename = source.name
        
        # Gestisci collisioni di nomi
        final_path = self._resolve_name_collision(dest_dir / filename)
        
        try:
            if not self.dry_run:
                # Assicurati che la directory di destinazione esista
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Sposta il file
                shutil.move(str(source), str(final_path))
            
            # Log dell'operazione
            if self.logger:
                operation = FileOperation(
                    operation_type=OperationType.MOVE,
                    original_path=str(source),
                    new_path=str(final_path),
                    timestamp=datetime.now(),
                    success=True
                )
                self.logger.log_operation(operation)
            
            return True, str(final_path), ""
            
        except Exception as e:
            error_msg = f"Errore nello spostamento del file: {e}"
            
            # Log dell'errore
            if self.logger:
                operation = FileOperation(
                    operation_type=OperationType.MOVE,
                    original_path=str(source),
                    new_path=str(final_path),
                    timestamp=datetime.now(),
                    success=False,
                    error_message=error_msg
                )
                self.logger.log_operation(operation)
            
            return False, "", error_msg
    
    def _resolve_name_collision(self, file_path: Path) -> Path:
        """
        Risolve le collisioni di nomi aggiungendo suffissi numerici.
        
        Args:
            file_path: Percorso del file
            
        Returns:
            Percorso senza collisioni
        """
        if not file_path.exists() or self.dry_run:
            return file_path
        
        base_name = file_path.stem
        extension = file_path.suffix
        parent_dir = file_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent_dir / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Protezione contro loop infiniti
            if counter > 9999:
                raise Exception("Troppi file con lo stesso nome")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizza un nome file per il filesystem.
        
        Args:
            filename: Nome da sanitizzare
            
        Returns:
            Nome sanitizzato
        """
        # Caratteri non validi per i nomi file
        invalid_chars = '<>:"/\\|?*'
        
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Rimuovi spazi multipli e spazi iniziali/finali
        sanitized = ' '.join(sanitized.split())
        
        # Limita la lunghezza (Windows ha un limite di 255 caratteri)
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized
    
    def generate_organized_filename(self, original_filename: str, 
                                  date_str: str = None) -> str:
        """
        Genera un nome file organizzato con data.
        
        Args:
            original_filename: Nome file originale
            date_str: Stringa data in formato YYYY-MM-DD
            
        Returns:
            Nome file organizzato
        """
        path = Path(original_filename)
        base_name = path.stem
        extension = path.suffix
        
        if date_str:
            # Formato: YYYY-MM-DD_nome_originale.ext
            new_name = f"{date_str}_{base_name}{extension}"
        else:
            new_name = original_filename
        
        return self._sanitize_filename(new_name)


class UndoManager:
    """Classe per gestire l'undo delle operazioni."""
    
    def __init__(self, dry_run: bool = False):
        """
        Inizializza l'undo manager.
        
        Args:
            dry_run: Se True, simula le operazioni senza eseguirle
        """
        self.dry_run = dry_run
    
    def undo_operations(self, csv_file_path: str) -> Tuple[int, int, List[str]]:
        """
        Annulla le operazioni registrate in un file CSV.
        
        Args:
            csv_file_path: Percorso del file CSV con le operazioni
            
        Returns:
            Tupla (operazioni_annullate, errori, lista_errori)
        """
        logger = FileOperationLogger("")
        operations = logger.load_operations_from_csv(csv_file_path)
        
        # Filtra solo le operazioni riuscite e invertile
        successful_operations = [op for op in operations if op.success]
        successful_operations.reverse()  # Inverti l'ordine per l'undo
        
        undone_count = 0
        error_count = 0
        errors = []
        
        for operation in successful_operations:
            try:
                if operation.operation_type == OperationType.MOVE:
                    success = self._undo_move_operation(operation)
                elif operation.operation_type == OperationType.CREATE_DIR:
                    success = self._undo_create_dir_operation(operation)
                else:
                    success = False
                    errors.append(f"Tipo operazione non supportato: {operation.operation_type}")
                
                if success:
                    undone_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Errore nell'undo di {operation.original_path}: {e}")
        
        return undone_count, error_count, errors
    
    def _undo_move_operation(self, operation: FileOperation) -> bool:
        """
        Annulla un'operazione di spostamento.
        
        Args:
            operation: Operazione da annullare
            
        Returns:
            True se l'operazione è stata annullata con successo
        """
        new_path = Path(operation.new_path)
        original_path = Path(operation.original_path)
        
        if not new_path.exists():
            print(f"File non trovato per l'undo: {new_path}")
            return False
        
        if original_path.exists():
            print(f"File di destinazione già esiste: {original_path}")
            return False
        
        try:
            if not self.dry_run:
                # Assicurati che la directory di destinazione esista
                original_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Sposta il file indietro
                shutil.move(str(new_path), str(original_path))
            
            print(f"Undo: {new_path} -> {original_path}")
            return True
            
        except Exception as e:
            print(f"Errore nell'undo del file {new_path}: {e}")
            return False
    
    def _undo_create_dir_operation(self, operation: FileOperation) -> bool:
        """
        Annulla un'operazione di creazione directory.
        
        Args:
            operation: Operazione da annullare
            
        Returns:
            True se l'operazione è stata annullata con successo
        """
        dir_path = Path(operation.new_path)
        
        if not dir_path.exists():
            return True  # Directory già rimossa
        
        try:
            if not self.dry_run:
                # Rimuovi la directory solo se è vuota
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"Directory rimossa: {dir_path}")
                else:
                    print(f"Directory non vuota, non rimossa: {dir_path}")
            
            return True
            
        except Exception as e:
            print(f"Errore nella rimozione della directory {dir_path}: {e}")
            return False