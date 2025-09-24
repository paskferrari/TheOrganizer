"""
Modulo core per l'organizzazione dei file.
Contiene la logica principale per il matching fuzzy e l'organizzazione dei file.
"""

import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Callable
from dataclasses import dataclass
from rapidfuzz import fuzz, process

from normalize import CompanyNameNormalizer, normalize_company_name, generate_company_aliases
from file_types import FileCategory, get_file_category
from io_ops import FileOrganizer, FileOperationLogger
from company_config import CompanyConfig


@dataclass
class FileMatch:
    """Rappresenta un match tra un file e un'azienda."""
    file_path: str
    company_name: str
    match_score: float
    matched_text: str
    category: FileCategory
    suggested_path: str
    file_date: Optional[date] = None
    file_size: int = 0


@dataclass
class OrganizationResult:
    """Risultato dell'organizzazione dei file."""
    total_files: int
    processed_files: int
    successful_moves: int
    failed_moves: int
    skipped_files: int
    matches: List[FileMatch]
    errors: List[str]


class DateExtractor:
    """Classe per estrarre date dai nomi dei file."""
    
    def __init__(self):
        """Inizializza l'estrattore di date."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compila i pattern regex per le date."""
        self.date_patterns = [
            # YYYY-MM-DD
            (re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})'), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # DD-MM-YYYY, DD/MM/YYYY
            (re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'), lambda m: (int(m.group(3)), int(m.group(2)), int(m.group(1)))),
            # YYYY/MM/DD
            (re.compile(r'(\d{4})/(\d{1,2})/(\d{1,2})'), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # YYYYMMDD
            (re.compile(r'(\d{8})'), lambda m: (int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(1)[6:8]))),
            # DD-MM-YY, DD/MM/YY (assumendo anni 2000+)
            (re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})'), lambda m: (2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        ]
    
    def extract_date_from_filename(self, filename: str) -> Optional[date]:
        """
        Estrae una data dal nome del file.
        
        Args:
            filename: Nome del file
            
        Returns:
            Data estratta o None se non trovata
        """
        for pattern, parser in self.date_patterns:
            match = pattern.search(filename)
            if match:
                try:
                    year, month, day = parser(match)
                    # Validazione base
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return date(year, month, day)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_date_from_file_stats(self, file_path: str) -> Optional[date]:
        """
        Estrae la data dalle statistiche del file.
        
        Args:
            file_path: Percorso del file
            
        Returns:
            Data di modifica del file
        """
        try:
            stat = os.stat(file_path)
            return datetime.fromtimestamp(stat.st_mtime).date()
        except (OSError, ValueError):
            return None


class CompanyMatcher:
    """Classe per il matching fuzzy dei nomi aziendali."""
    
    def __init__(self, threshold: float = 92.0):
        """
        Inizializza il matcher.
        
        Args:
            threshold: Soglia minima per considerare un match valido (0-100)
        """
        self.threshold = threshold
        self.normalizer = CompanyNameNormalizer()
        self.company_aliases: Dict[str, List[str]] = {}
        self.config = CompanyConfig()
        
        # Carica automaticamente le aziende dalla configurazione
        self._load_companies_from_config()
    
    def _load_companies_from_config(self):
        """Carica le aziende dalla configurazione."""
        companies = self.config.get_companies()
        for company_name, company_data in companies.items():
            aliases = company_data.get('aliases', [])
            self.add_company(company_name, aliases)
    
    def add_company(self, company_name: str, aliases: List[str] = None):
        """
        Aggiunge un'azienda con i suoi alias.
        
        Args:
            company_name: Nome dell'azienda
            aliases: Lista di alias (opzionale)
        """
        if aliases is None:
            aliases = []
        
        # Normalizza il nome principale
        normalized_name = self.normalizer.normalize(company_name)
        
        # Genera alias automatici
        auto_aliases = self.normalizer.generate_aliases(company_name)
        
        # Normalizza gli alias forniti
        normalized_aliases = [self.normalizer.normalize(alias) for alias in aliases]
        
        # Combina tutti gli alias
        all_aliases = list(set(auto_aliases + normalized_aliases + [normalized_name]))
        
        self.company_aliases[company_name] = all_aliases
    
    def find_best_match(self, text: str) -> Tuple[Optional[str], float, str]:
        """
        Trova il miglior match per un testo.
        
        Args:
            text: Testo da matchare
            
        Returns:
            Tupla (nome_azienda, score, testo_matchato)
        """
        if not self.company_aliases:
            return None, 0.0, ""
        
        # Normalizza il testo di input
        normalized_text = self.normalizer.normalize(text)
        
        if not normalized_text:
            return None, 0.0, ""
        
        best_company = None
        best_score = 0.0
        best_matched_text = ""
        
        # Cerca in tutti gli alias di tutte le aziende
        for company_name, aliases in self.company_aliases.items():
            for alias in aliases:
                if not alias:
                    continue
                
                # Calcola diversi tipi di score
                scores = [
                    fuzz.ratio(normalized_text, alias),
                    fuzz.partial_ratio(normalized_text, alias),
                    fuzz.token_sort_ratio(normalized_text, alias),
                    fuzz.token_set_ratio(normalized_text, alias)
                ]
                
                # Usa il punteggio massimo
                score = max(scores)
                
                # Bonus per match esatti
                if normalized_text == alias:
                    score = 100.0
                elif alias in normalized_text or normalized_text in alias:
                    score = min(score + 10, 100.0)
                
                if score > best_score and score >= self.threshold:
                    # Verifica se il match è valido secondo le regole dell'azienda
                    if self.config.is_valid_match(company_name, alias, normalized_text):
                        best_score = score
                        best_company = company_name
                        best_matched_text = alias
        
        return best_company, best_score, best_matched_text
    
    def _is_valid_single_word_match(self, word: str) -> bool:
        """
        Verifica se una singola parola può essere usata per il matching.
        Evita match su parole troppo generiche o forme societarie standalone.
        
        Args:
            word: Parola da verificare
            
        Returns:
            True se la parola può essere usata per il matching
        """
        word_lower = word.lower().strip()
        
        # Evita forme societarie standalone
        company_forms = {'spa', 's.p.a', 's.p.a.', 'srl', 's.r.l', 's.r.l.', 
                        'sas', 's.a.s', 's.a.s.', 'snc', 's.n.c', 's.n.c.',
                        'ltd', 'inc', 'corp', 'llc', 'gmbh', 'ag', 'sa', 'bv', 'nv'}
        
        if word_lower in company_forms:
            return False
        
        # Evita parole troppo generiche (già definite nel normalizer)
        if word_lower in self.normalizer.GENERIC_WORDS:
            return False
        
        # Evita parole troppo corte (meno di 3 caratteri)
        if len(word_lower) < 3:
            return False
        
        return True
    
    def extract_company_names_from_filename(self, filename: str) -> List[Tuple[str, float, str]]:
        """
        Estrae possibili nomi aziendali da un nome file.
        
        Args:
            filename: Nome del file
            
        Returns:
            Lista di tuple (nome_azienda, score, testo_matchato)
        """
        matches = []
        
        # PRIORITÀ 1: Testa il nome file completo (per catturare frasi complete come "SKY LINE EUROPA")
        company, score, matched_text = self.find_best_match(filename)
        if company and score >= self.threshold:
            matches.append((company, score, matched_text))
            # Se troviamo un match completo con score alto, non cercare parti singole
            if score >= 95:
                return [(company, score, matched_text)]
        
        # PRIORITÀ 2: Testa combinazioni di parole adiacenti (per frasi spezzate da separatori)
        parts = self.normalizer.extract_company_names_from_filename(filename)
        if len(parts) > 1:
            # Testa combinazioni di 2-4 parole adiacenti
            for i in range(len(parts)):
                for j in range(i + 2, min(i + 5, len(parts) + 1)):  # Da 2 a 4 parole
                    combined_text = ' '.join(parts[i:j])
                    company, score, matched_text = self.find_best_match(combined_text)
                    if company and score >= self.threshold:
                        matches.append((company, score, matched_text))
        
        # PRIORITÀ 3: Solo se non abbiamo trovato match di qualità, testa parti singole
        if not matches or max(match[1] for match in matches) < self.threshold + 5:
            for part in parts:
                # Evita match su parole troppo generiche o forme societarie standalone
                if self._is_valid_single_word_match(part):
                    company, score, matched_text = self.find_best_match(part)
                    if company and score >= self.threshold:
                        matches.append((company, score, matched_text))
        
        # Rimuovi duplicati e ordina per score
        unique_matches = {}
        for company, score, matched_text in matches:
            if company not in unique_matches or score > unique_matches[company][0]:
                unique_matches[company] = (score, matched_text)
        
        result = [(company, score, matched_text) 
                 for company, (score, matched_text) in unique_matches.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result
    
    def extract_company_names_from_path(self, file_path: str) -> List[Tuple[str, float, str]]:
        """
        Estrae possibili nomi aziendali da un percorso file, dando priorità al nome del file.
        
        Args:
            file_path: Percorso completo del file
            
        Returns:
            Lista di tuple (nome_azienda, score, testo_matchato) ordinate per priorità
        """
        path = Path(file_path)
        filename = path.name
        
        # Prima priorità: nome del file
        filename_matches = self.extract_company_names_from_filename(filename)
        
        # Applica bonus per match nel nome del file
        boosted_filename_matches = []
        for company, score, matched_text in filename_matches:
            # Bonus del 15% per match nel nome del file (max 100%)
            boosted_score = min(score + 15, 100.0)
            boosted_filename_matches.append((company, boosted_score, matched_text))
        
        # Seconda priorità: parti del percorso (solo se non abbiamo match nel filename)
        path_matches = []
        if not boosted_filename_matches:
            # Estrai parti dal percorso completo (escludendo il nome del file)
            path_parts = []
            for part in path.parts[:-1]:  # Esclude il nome del file
                path_parts.extend(self.normalizer.extract_company_names_from_filename(part))
            
            # Testa ogni parte del percorso
            for part in path_parts:
                company, score, matched_text = self.find_best_match(part)
                if company and score >= self.threshold:
                    # Penalizza i match nel percorso del 10%
                    penalized_score = max(score - 10, 0)
                    if penalized_score >= self.threshold:
                        path_matches.append((company, penalized_score, matched_text))
        
        # Combina i risultati, dando priorità al nome del file
        all_matches = boosted_filename_matches + path_matches
        
        # Rimuovi duplicati mantenendo il punteggio più alto
        unique_matches = {}
        for company, score, matched_text in all_matches:
            if company not in unique_matches or score > unique_matches[company][0]:
                unique_matches[company] = (score, matched_text)
        
        result = [(company, score, matched_text) 
                 for company, (score, matched_text) in unique_matches.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result


class FileScanner:
    """Classe per la scansione dei file."""
    
    def __init__(self, include_extensions: Set[str] = None, 
                 exclude_extensions: Set[str] = None,
                 exclude_folders: Set[str] = None,
                 max_file_size_mb: float = None):
        """
        Inizializza lo scanner.
        
        Args:
            include_extensions: Estensioni da includere (None = tutte)
            exclude_extensions: Estensioni da escludere
            exclude_folders: Cartelle da escludere
            max_file_size_mb: Dimensione massima file in MB
        """
        self.include_extensions = include_extensions
        self.exclude_extensions = exclude_extensions or set()
        self.exclude_folders = exclude_folders or set()
        self.max_file_size_mb = max_file_size_mb
        
        # Normalizza le estensioni
        if self.include_extensions:
            self.include_extensions = {ext.lower() if ext.startswith('.') else '.' + ext.lower() 
                                     for ext in self.include_extensions}
        
        self.exclude_extensions = {ext.lower() if ext.startswith('.') else '.' + ext.lower() 
                                 for ext in self.exclude_extensions}
    
    def scan_directory(self, root_path: str, 
                      progress_callback: Callable[[int, int], None] = None) -> List[str]:
        """
        Scansiona una directory per trovare i file.
        
        Args:
            root_path: Percorso della directory root
            progress_callback: Callback per il progresso (file_corrente, totale_file)
            
        Returns:
            Lista dei percorsi dei file trovati
        """
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Directory non valida: {root_path}")
        
        files = []
        total_files = 0
        
        # Prima passata: conta i file
        if progress_callback:
            for _ in root.rglob('*'):
                if _.is_file():
                    total_files += 1
        
        # Seconda passata: filtra i file
        current_file = 0
        for file_path in root.rglob('*'):
            if not file_path.is_file():
                continue
            
            current_file += 1
            if progress_callback:
                progress_callback(current_file, total_files)
            
            # Controlla se la cartella è esclusa
            if self._is_folder_excluded(file_path):
                continue
            
            # Controlla l'estensione
            if not self._is_extension_allowed(file_path.name):
                continue
            
            # Controlla la dimensione del file
            if not self._is_size_allowed(file_path):
                continue
            
            files.append(str(file_path))
        
        return files
    
    def _is_folder_excluded(self, file_path: Path) -> bool:
        """Verifica se il file è in una cartella esclusa."""
        for part in file_path.parts:
            if part in self.exclude_folders:
                return True
        return False
    
    def _is_extension_allowed(self, filename: str) -> bool:
        """Verifica se l'estensione del file è permessa."""
        extension = self._get_extension(filename)
        
        # Controlla esclusioni
        if extension in self.exclude_extensions:
            return False
        
        # Controlla inclusioni
        if self.include_extensions and extension not in self.include_extensions:
            return False
        
        return True
    
    def _is_size_allowed(self, file_path: Path) -> bool:
        """Verifica se la dimensione del file è permessa."""
        if self.max_file_size_mb is None:
            return True
        
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            return size_mb <= self.max_file_size_mb
        except OSError:
            return True  # Se non riusciamo a leggere la dimensione, includiamo il file
    
    def _get_extension(self, filename: str) -> str:
        """Ottiene l'estensione di un file."""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''


class FileOrganizerCore:
    """Classe principale per l'organizzazione dei file."""
    
    def __init__(self, threshold: float = 92.0, dry_run: bool = False):
        """
        Inizializza l'organizzatore.
        
        Args:
            threshold: Soglia per il matching fuzzy
            dry_run: Se True, simula le operazioni senza eseguirle
        """
        self.threshold = threshold
        self.dry_run = dry_run
        
        self.matcher = CompanyMatcher(threshold)
        self.date_extractor = DateExtractor()
        self.file_organizer = FileOrganizer(dry_run)
        self.scanner = FileScanner()
        
        self.logger: Optional[FileOperationLogger] = None
    
    def set_logger(self, logger: FileOperationLogger):
        """Imposta il logger per le operazioni."""
        self.logger = logger
        self.file_organizer.set_logger(logger)
    
    def add_company(self, company_name: str, aliases: List[str] = None):
        """Aggiunge un'azienda per il matching."""
        self.matcher.add_company(company_name, aliases)
    
    def set_filters(self, include_extensions: Set[str] = None,
                   exclude_extensions: Set[str] = None,
                   exclude_folders: Set[str] = None,
                   max_file_size_mb: float = None):
        """Imposta i filtri per la scansione."""
        self.scanner = FileScanner(
            include_extensions=include_extensions,
            exclude_extensions=exclude_extensions,
            exclude_folders=exclude_folders,
            max_file_size_mb=max_file_size_mb
        )
    
    def organize_files(self, root_path: str, output_path: str,
                      since_date: date = None, until_date: date = None,
                      progress_callback: Callable[[str, int, int], None] = None) -> OrganizationResult:
        """
        Organizza i file nella directory specificata.
        
        Args:
            root_path: Percorso della directory da organizzare
            output_path: Percorso di output per l'organizzazione
            since_date: Data minima per i file (opzionale)
            until_date: Data massima per i file (opzionale)
            progress_callback: Callback per il progresso (fase, corrente, totale)
            
        Returns:
            Risultato dell'organizzazione
        """
        print(f"[DEBUG] Avvio organizzazione file:")
        print(f"[DEBUG] - Directory sorgente: {root_path}")
        print(f"[DEBUG] - Directory destinazione: {output_path}")
        print(f"[DEBUG] - Modalità dry run: {self.dry_run}")
        print(f"[DEBUG] - Soglia matching: {self.threshold}")
        if since_date:
            print(f"[DEBUG] - Data minima: {since_date}")
        if until_date:
            print(f"[DEBUG] - Data massima: {until_date}")
        
        result = OrganizationResult(
            total_files=0,
            processed_files=0,
            successful_moves=0,
            failed_moves=0,
            skipped_files=0,
            matches=[],
            errors=[]
        )
        
        try:
            # Fase 1: Scansione dei file
            print(f"[DEBUG] Fase 1: Scansione directory {root_path}")
            if progress_callback:
                progress_callback("Scansione file...", 0, 0)
            
            files = self.scanner.scan_directory(
                root_path, 
                lambda c, t: progress_callback("Scansione file...", c, t) if progress_callback else None
            )
            
            result.total_files = len(files)
            print(f"[DEBUG] Trovati {result.total_files} file da analizzare")
            
            if not files:
                print(f"[DEBUG] Nessun file trovato nella directory {root_path}")
                return result
            
            # Fase 2: Analisi e matching
            print(f"[DEBUG] Fase 2: Analisi e matching dei file")
            print(f"[DEBUG] Aziende configurate: {list(self.matcher.company_aliases.keys())}")
            if progress_callback:
                progress_callback("Analisi file...", 0, len(files))
            
            for i, file_path in enumerate(files):
                if progress_callback:
                    progress_callback("Analisi file...", i + 1, len(files))
                
                print(f"[DEBUG] Analizzando file: {file_path}")
                try:
                    match = self._analyze_file(file_path, since_date, until_date)
                    if match:
                        print(f"[DEBUG] Match trovato: {match.company_name} (score: {match.match_score:.1f})")
                        print(f"[DEBUG] Percorso suggerito: {match.suggested_path}")
                        result.matches.append(match)
                    else:
                        print(f"[DEBUG] Nessun match trovato per: {os.path.basename(file_path)}")
                        result.skipped_files += 1
                except Exception as e:
                    print(f"[DEBUG] Errore nell'analisi di {file_path}: {e}")
                    result.errors.append(f"Errore nell'analisi di {file_path}: {e}")
                    result.skipped_files += 1
            
            result.processed_files = len(result.matches)
            print(f"[DEBUG] File con match trovati: {result.processed_files}")
            
            # Fase 3: Organizzazione (solo se non è dry run o se esplicitamente richiesto)
            if not self.dry_run:
                print(f"[DEBUG] Fase 3: Spostamento file nella directory {output_path}")
                if progress_callback:
                    progress_callback("Organizzazione file...", 0, len(result.matches))
                
                for i, match in enumerate(result.matches):
                    if progress_callback:
                        progress_callback("Organizzazione file...", i + 1, len(result.matches))
                    
                    print(f"[DEBUG] Spostando file: {match.file_path}")
                    print(f"[DEBUG] Destinazione: {output_path}")
                    try:
                        success = self._move_file(match, output_path)
                        if success:
                            print(f"[DEBUG] File spostato con successo")
                            result.successful_moves += 1
                        else:
                            print(f"[DEBUG] Spostamento fallito")
                            result.failed_moves += 1
                    except Exception as e:
                        print(f"[DEBUG] Errore nello spostamento: {e}")
                        result.errors.append(f"Errore nello spostamento di {match.file_path}: {e}")
                        result.failed_moves += 1
            else:
                print(f"[DEBUG] Modalità dry run attiva - nessun file verrà spostato")
            
        except Exception as e:
            result.errors.append(f"Errore generale: {e}")
        
        return result
    
    def _analyze_file(self, file_path: str, since_date: date = None, 
                     until_date: date = None) -> Optional[FileMatch]:
        """
        Analizza un file per determinare l'azienda e la categoria.
        
        Args:
            file_path: Percorso del file
            since_date: Data minima
            until_date: Data massima
            
        Returns:
            FileMatch se trovato un match, None altrimenti
        """
        path = Path(file_path)
        filename = path.name
        
        # Estrai la data dal file
        file_date = self.date_extractor.extract_date_from_filename(filename)
        if not file_date:
            file_date = self.date_extractor.extract_date_from_file_stats(file_path)
        
        # Filtra per date se specificate
        if file_date:
            if since_date and file_date < since_date:
                return None
            if until_date and file_date > until_date:
                return None
        
        # Trova il match aziendale usando il nuovo metodo che dà priorità al nome del file
        matches = self.matcher.extract_company_names_from_path(file_path)
        if not matches:
            return None
        
        # Prendi il miglior match
        company_name, score, matched_text = matches[0]
        
        # Determina la categoria del file
        category = get_file_category(filename)
        
        # Genera il percorso suggerito
        year = str(file_date.year) if file_date else str(datetime.now().year)
        suggested_path = self._generate_suggested_path(
            company_name, category, year, filename, file_date
        )
        
        # Ottieni la dimensione del file
        try:
            file_size = path.stat().st_size
        except OSError:
            file_size = 0
        
        return FileMatch(
            file_path=file_path,
            company_name=company_name,
            match_score=score,
            matched_text=matched_text,
            category=category,
            suggested_path=suggested_path,
            file_date=file_date,
            file_size=file_size
        )
    
    def _generate_suggested_path(self, company_name: str, category: FileCategory,
                               year: str, filename: str, file_date: date = None) -> str:
        """
        Genera il percorso suggerito per un file.
        
        Args:
            company_name: Nome dell'azienda
            category: Categoria del file
            year: Anno
            filename: Nome del file
            file_date: Data del file (opzionale)
            
        Returns:
            Percorso suggerito relativo
        """
        # Sanitizza i nomi
        safe_company = self._sanitize_name(company_name)
        safe_category = category.value
        
        # Genera il nome del file con data se disponibile
        if file_date:
            date_str = file_date.strftime("%Y-%m-%d")
            new_filename = self.file_organizer.generate_organized_filename(filename, date_str)
        else:
            new_filename = filename
        
        # Costruisci il percorso: Azienda/Categoria/Anno/file
        return f"{safe_company}/{safe_category}/{year}/{new_filename}"
    
    def _move_file(self, match: FileMatch, output_path: str) -> bool:
        """
        Sposta un file nella posizione organizzata.
        
        Args:
            match: Match del file
            output_path: Percorso di output base
            
        Returns:
            True se lo spostamento è riuscito
        """
        # Crea la struttura di directory
        year = str(match.file_date.year) if match.file_date else str(datetime.now().year)
        print(f"[DEBUG] Creando struttura directory:")
        print(f"[DEBUG] - Base path: {output_path}")
        print(f"[DEBUG] - Azienda: {match.company_name}")
        print(f"[DEBUG] - Categoria: {match.category.value}")
        print(f"[DEBUG] - Anno: {year}")
        
        dest_dir = self.file_organizer.create_directory_structure(
            output_path, match.company_name, year, match.category.value
        )
        
        print(f"[DEBUG] Directory di destinazione creata: {dest_dir}")
        
        # Sposta il file
        print(f"[DEBUG] Spostando file da {match.file_path} a {dest_dir}")
        success, final_path, error = self.file_organizer.move_file(
            match.file_path, dest_dir
        )
        
        if success:
            print(f"[DEBUG] File spostato con successo in: {final_path}")
        else:
            print(f"[DEBUG] Errore nello spostamento: {error}")
        
        if not success and error:
            raise Exception(error)
        
        return success
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitizza un nome per l'uso come nome di cartella."""
        return self.file_organizer._sanitize_filename(name)