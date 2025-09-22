"""
Modulo per la classificazione dei tipi di file.
Gestisce la mappatura delle estensioni ai tipi di file per l'organizzazione.
"""

from typing import Dict, List, Set
from enum import Enum


class FileCategory(Enum):
    """Categorie di file supportate."""
    PDF = "PDF"
    WORD = "Word"
    EXCEL = "Excel"
    POWERPOINT = "PowerPoint"
    IMMAGINI = "Immagini"
    VIDEO = "Video"
    AUDIO = "Audio"
    ARCHIVI = "Archivi"
    CODICE = "Codice"
    ALTRO = "Altro"


class FileTypeMapper:
    """Classe per mappare le estensioni ai tipi di file."""
    
    def __init__(self):
        """Inizializza il mapper con le estensioni predefinite."""
        self._extension_map = {
            # PDF
            '.pdf': FileCategory.PDF,
            
            # Microsoft Word
            '.doc': FileCategory.WORD,
            '.docx': FileCategory.WORD,
            '.docm': FileCategory.WORD,
            '.dot': FileCategory.WORD,
            '.dotx': FileCategory.WORD,
            '.dotm': FileCategory.WORD,
            '.odt': FileCategory.WORD,
            '.rtf': FileCategory.WORD,
            
            # Microsoft Excel
            '.xls': FileCategory.EXCEL,
            '.xlsx': FileCategory.EXCEL,
            '.xlsm': FileCategory.EXCEL,
            '.xlsb': FileCategory.EXCEL,
            '.xlt': FileCategory.EXCEL,
            '.xltx': FileCategory.EXCEL,
            '.xltm': FileCategory.EXCEL,
            '.xlam': FileCategory.EXCEL,
            '.ods': FileCategory.EXCEL,
            '.csv': FileCategory.EXCEL,
            
            # Microsoft PowerPoint
            '.ppt': FileCategory.POWERPOINT,
            '.pptx': FileCategory.POWERPOINT,
            '.pptm': FileCategory.POWERPOINT,
            '.pot': FileCategory.POWERPOINT,
            '.potx': FileCategory.POWERPOINT,
            '.potm': FileCategory.POWERPOINT,
            '.pps': FileCategory.POWERPOINT,
            '.ppsx': FileCategory.POWERPOINT,
            '.ppsm': FileCategory.POWERPOINT,
            '.odp': FileCategory.POWERPOINT,
            
            # Immagini
            '.jpg': FileCategory.IMMAGINI,
            '.jpeg': FileCategory.IMMAGINI,
            '.png': FileCategory.IMMAGINI,
            '.gif': FileCategory.IMMAGINI,
            '.bmp': FileCategory.IMMAGINI,
            '.tiff': FileCategory.IMMAGINI,
            '.tif': FileCategory.IMMAGINI,
            '.svg': FileCategory.IMMAGINI,
            '.webp': FileCategory.IMMAGINI,
            '.ico': FileCategory.IMMAGINI,
            '.raw': FileCategory.IMMAGINI,
            '.cr2': FileCategory.IMMAGINI,
            '.nef': FileCategory.IMMAGINI,
            '.arw': FileCategory.IMMAGINI,
            '.dng': FileCategory.IMMAGINI,
            '.psd': FileCategory.IMMAGINI,
            '.ai': FileCategory.IMMAGINI,
            '.eps': FileCategory.IMMAGINI,
            
            # Video
            '.mp4': FileCategory.VIDEO,
            '.avi': FileCategory.VIDEO,
            '.mkv': FileCategory.VIDEO,
            '.mov': FileCategory.VIDEO,
            '.wmv': FileCategory.VIDEO,
            '.flv': FileCategory.VIDEO,
            '.webm': FileCategory.VIDEO,
            '.m4v': FileCategory.VIDEO,
            '.3gp': FileCategory.VIDEO,
            '.mpg': FileCategory.VIDEO,
            '.mpeg': FileCategory.VIDEO,
            '.ts': FileCategory.VIDEO,
            '.vob': FileCategory.VIDEO,
            
            # Audio
            '.mp3': FileCategory.AUDIO,
            '.wav': FileCategory.AUDIO,
            '.flac': FileCategory.AUDIO,
            '.aac': FileCategory.AUDIO,
            '.ogg': FileCategory.AUDIO,
            '.wma': FileCategory.AUDIO,
            '.m4a': FileCategory.AUDIO,
            '.opus': FileCategory.AUDIO,
            '.aiff': FileCategory.AUDIO,
            '.au': FileCategory.AUDIO,
            
            # Archivi
            '.zip': FileCategory.ARCHIVI,
            '.rar': FileCategory.ARCHIVI,
            '.7z': FileCategory.ARCHIVI,
            '.tar': FileCategory.ARCHIVI,
            '.gz': FileCategory.ARCHIVI,
            '.bz2': FileCategory.ARCHIVI,
            '.xz': FileCategory.ARCHIVI,
            '.tar.gz': FileCategory.ARCHIVI,
            '.tar.bz2': FileCategory.ARCHIVI,
            '.tar.xz': FileCategory.ARCHIVI,
            '.iso': FileCategory.ARCHIVI,
            '.dmg': FileCategory.ARCHIVI,
            
            # Codice e sviluppo
            '.py': FileCategory.CODICE,
            '.js': FileCategory.CODICE,
            '.html': FileCategory.CODICE,
            '.htm': FileCategory.CODICE,
            '.css': FileCategory.CODICE,
            '.php': FileCategory.CODICE,
            '.java': FileCategory.CODICE,
            '.cpp': FileCategory.CODICE,
            '.c': FileCategory.CODICE,
            '.h': FileCategory.CODICE,
            '.cs': FileCategory.CODICE,
            '.vb': FileCategory.CODICE,
            '.rb': FileCategory.CODICE,
            '.go': FileCategory.CODICE,
            '.rs': FileCategory.CODICE,
            '.swift': FileCategory.CODICE,
            '.kt': FileCategory.CODICE,
            '.scala': FileCategory.CODICE,
            '.r': FileCategory.CODICE,
            '.sql': FileCategory.CODICE,
            '.xml': FileCategory.CODICE,
            '.json': FileCategory.CODICE,
            '.yaml': FileCategory.CODICE,
            '.yml': FileCategory.CODICE,
            '.toml': FileCategory.CODICE,
            '.ini': FileCategory.CODICE,
            '.cfg': FileCategory.CODICE,
            '.conf': FileCategory.CODICE,
            '.sh': FileCategory.CODICE,
            '.bat': FileCategory.CODICE,
            '.ps1': FileCategory.CODICE,
            '.md': FileCategory.CODICE,
            '.txt': FileCategory.CODICE,
        }
        
        # Set di estensioni per categoria (per ricerca rapida)
        self._category_extensions = {}
        for category in FileCategory:
            self._category_extensions[category] = set()
        
        for ext, category in self._extension_map.items():
            self._category_extensions[category].add(ext)
    
    def get_file_category(self, filename: str) -> FileCategory:
        """
        Determina la categoria di un file basandosi sulla sua estensione.
        
        Args:
            filename: Nome del file (con estensione)
            
        Returns:
            Categoria del file
        """
        # Estrai l'estensione
        extension = self._extract_extension(filename)
        
        # Cerca nella mappa
        return self._extension_map.get(extension, FileCategory.ALTRO)
    
    def _extract_extension(self, filename: str) -> str:
        """
        Estrae l'estensione da un nome file.
        
        Args:
            filename: Nome del file
            
        Returns:
            Estensione in lowercase (con il punto)
        """
        # Gestisci estensioni composte come .tar.gz
        filename_lower = filename.lower()
        
        # Controlla estensioni composte comuni
        composite_extensions = ['.tar.gz', '.tar.bz2', '.tar.xz']
        for comp_ext in composite_extensions:
            if filename_lower.endswith(comp_ext):
                return comp_ext
        
        # Estensione normale
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        
        return ''
    
    def get_extensions_for_category(self, category: FileCategory) -> Set[str]:
        """
        Ottiene tutte le estensioni per una categoria.
        
        Args:
            category: Categoria di file
            
        Returns:
            Set di estensioni per la categoria
        """
        return self._category_extensions.get(category, set()).copy()
    
    def add_extension_mapping(self, extension: str, category: FileCategory):
        """
        Aggiunge una nuova mappatura estensione -> categoria.
        
        Args:
            extension: Estensione (con il punto, es. '.xyz')
            category: Categoria di file
        """
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        self._extension_map[extension] = category
        self._category_extensions[category].add(extension)
    
    def remove_extension_mapping(self, extension: str):
        """
        Rimuove una mappatura estensione.
        
        Args:
            extension: Estensione da rimuovere
        """
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        if extension in self._extension_map:
            category = self._extension_map[extension]
            del self._extension_map[extension]
            self._category_extensions[category].discard(extension)
    
    def get_all_extensions(self) -> Set[str]:
        """
        Ottiene tutte le estensioni supportate.
        
        Returns:
            Set di tutte le estensioni
        """
        return set(self._extension_map.keys())
    
    def get_category_display_name(self, category: FileCategory) -> str:
        """
        Ottiene il nome visualizzabile di una categoria.
        
        Args:
            category: Categoria di file
            
        Returns:
            Nome da visualizzare
        """
        return category.value
    
    def filter_files_by_extensions(self, filenames: List[str], 
                                 include_extensions: Set[str] = None,
                                 exclude_extensions: Set[str] = None) -> List[str]:
        """
        Filtra una lista di file basandosi sulle estensioni.
        
        Args:
            filenames: Lista di nomi file
            include_extensions: Estensioni da includere (None = tutte)
            exclude_extensions: Estensioni da escludere (None = nessuna)
            
        Returns:
            Lista filtrata di nomi file
        """
        filtered = []
        
        # Normalizza le estensioni
        if include_extensions:
            include_extensions = {ext.lower() if ext.startswith('.') else '.' + ext.lower() 
                                for ext in include_extensions}
        
        if exclude_extensions:
            exclude_extensions = {ext.lower() if ext.startswith('.') else '.' + ext.lower() 
                                for ext in exclude_extensions}
        
        for filename in filenames:
            extension = self._extract_extension(filename)
            
            # Controlla esclusioni
            if exclude_extensions and extension in exclude_extensions:
                continue
            
            # Controlla inclusioni
            if include_extensions and extension not in include_extensions:
                continue
            
            filtered.append(filename)
        
        return filtered


# Istanza globale del mapper
file_type_mapper = FileTypeMapper()


def get_file_category(filename: str) -> FileCategory:
    """
    Funzione di convenienza per ottenere la categoria di un file.
    
    Args:
        filename: Nome del file
        
    Returns:
        Categoria del file
    """
    return file_type_mapper.get_file_category(filename)


def get_category_folder_name(category: FileCategory) -> str:
    """
    Ottiene il nome della cartella per una categoria.
    
    Args:
        category: Categoria di file
        
    Returns:
        Nome della cartella
    """
    return file_type_mapper.get_category_display_name(category)