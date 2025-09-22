"""
Modulo per la gestione della configurazione.
Gestisce il caricamento e salvataggio delle configurazioni in formato YAML.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CompanyProfile:
    """Profilo di un'azienda con i suoi alias."""
    name: str
    aliases: List[str]
    created_at: datetime
    last_used: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il profilo in dizionario."""
        return {
            'name': self.name,
            'aliases': self.aliases,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyProfile':
        """Crea un profilo da dizionario."""
        return cls(
            name=data['name'],
            aliases=data.get('aliases', []),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            last_used=datetime.fromisoformat(data.get('last_used', datetime.now().isoformat()))
        )


@dataclass
class AppSettings:
    """Impostazioni dell'applicazione."""
    # Impostazioni generali
    default_threshold: float = 85.0
    default_root_path: str = ""
    theme: str = "dark"  # "dark" o "light"
    language: str = "it"
    
    # Impostazioni filtri
    default_include_extensions: List[str] = None
    default_exclude_extensions: List[str] = None
    default_exclude_folders: List[str] = None
    
    # Impostazioni avanzate
    max_file_size_mb: float = 1000.0  # Dimensione massima file in MB
    enable_date_extraction: bool = True
    auto_create_year_folders: bool = True
    log_retention_days: int = 30
    
    # Impostazioni GUI
    window_width: int = 1200
    window_height: int = 800
    remember_window_size: bool = True
    show_preview_by_default: bool = True
    
    def __post_init__(self):
        """Inizializza i valori di default."""
        if self.default_include_extensions is None:
            self.default_include_extensions = []
        if self.default_exclude_extensions is None:
            self.default_exclude_extensions = ['.tmp', '.temp', '.log']
        if self.default_exclude_folders is None:
            self.default_exclude_folders = [
                'System Volume Information', '$RECYCLE.BIN', '.git', 
                '.svn', 'node_modules', '__pycache__'
            ]


class ConfigManager:
    """Gestore della configurazione dell'applicazione."""
    
    def __init__(self, config_dir: str = None):
        """
        Inizializza il gestore della configurazione.
        
        Args:
            config_dir: Directory di configurazione (default: ~/.file_organizer)
        """
        if config_dir is None:
            # Directory di configurazione di default
            home_dir = Path.home()
            self.config_dir = home_dir / '.file_organizer'
        else:
            self.config_dir = Path(config_dir)
        
        # Crea la directory se non esiste
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Percorsi dei file di configurazione
        self.settings_file = self.config_dir / 'settings.yaml'
        self.companies_file = self.config_dir / 'companies.yaml'
        self.recent_files_file = self.config_dir / 'recent.yaml'
        
        # Carica le configurazioni
        self.settings = self._load_settings()
        self.companies: Dict[str, CompanyProfile] = self._load_companies()
        self.recent_files: List[str] = self._load_recent_files()
    
    def _load_settings(self) -> AppSettings:
        """
        Carica le impostazioni dell'applicazione.
        
        Returns:
            Impostazioni caricate o default
        """
        if not self.settings_file.exists():
            return AppSettings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Crea l'oggetto settings dai dati YAML
            settings = AppSettings()
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            return settings
            
        except Exception as e:
            print(f"Errore nel caricamento delle impostazioni: {e}")
            return AppSettings()
    
    def _load_companies(self) -> Dict[str, CompanyProfile]:
        """
        Carica i profili delle aziende.
        
        Returns:
            Dizionario dei profili aziendali
        """
        if not self.companies_file.exists():
            return {}
        
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            companies = {}
            for name, profile_data in data.items():
                try:
                    companies[name] = CompanyProfile.from_dict(profile_data)
                except Exception as e:
                    print(f"Errore nel caricamento del profilo {name}: {e}")
            
            return companies
            
        except Exception as e:
            print(f"Errore nel caricamento dei profili aziendali: {e}")
            return {}
    
    def _load_recent_files(self) -> List[str]:
        """
        Carica la lista dei file recenti.
        
        Returns:
            Lista dei percorsi dei file recenti
        """
        if not self.recent_files_file.exists():
            return []
        
        try:
            with open(self.recent_files_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or []
            
            # Filtra solo i file che esistono ancora
            existing_files = []
            for file_path in data:
                if Path(file_path).exists():
                    existing_files.append(file_path)
            
            return existing_files[:10]  # Mantieni solo gli ultimi 10
            
        except Exception as e:
            print(f"Errore nel caricamento dei file recenti: {e}")
            return []
    
    def save_settings(self):
        """Salva le impostazioni su file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                yaml.dump(asdict(self.settings), f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=True)
        except Exception as e:
            print(f"Errore nel salvataggio delle impostazioni: {e}")
    
    def save_companies(self):
        """Salva i profili aziendali su file."""
        try:
            data = {}
            for name, profile in self.companies.items():
                data[name] = profile.to_dict()
            
            with open(self.companies_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=True)
        except Exception as e:
            print(f"Errore nel salvataggio dei profili aziendali: {e}")
    
    def save_recent_files(self):
        """Salva la lista dei file recenti."""
        try:
            with open(self.recent_files_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.recent_files, f, default_flow_style=False, 
                         allow_unicode=True)
        except Exception as e:
            print(f"Errore nel salvataggio dei file recenti: {e}")
    
    def add_company_profile(self, name: str, aliases: List[str] = None):
        """
        Aggiunge un nuovo profilo aziendale.
        
        Args:
            name: Nome dell'azienda
            aliases: Lista di alias (opzionale)
        """
        if aliases is None:
            aliases = []
        
        now = datetime.now()
        profile = CompanyProfile(
            name=name,
            aliases=aliases,
            created_at=now,
            last_used=now
        )
        
        self.companies[name] = profile
        self.save_companies()
    
    def update_company_profile(self, name: str, aliases: List[str]):
        """
        Aggiorna un profilo aziendale esistente.
        
        Args:
            name: Nome dell'azienda
            aliases: Nuova lista di alias
        """
        if name in self.companies:
            self.companies[name].aliases = aliases
            self.companies[name].last_used = datetime.now()
            self.save_companies()
    
    def remove_company_profile(self, name: str):
        """
        Rimuove un profilo aziendale.
        
        Args:
            name: Nome dell'azienda da rimuovere
        """
        if name in self.companies:
            del self.companies[name]
            self.save_companies()
    
    def get_company_profile(self, name: str) -> Optional[CompanyProfile]:
        """
        Ottiene un profilo aziendale.
        
        Args:
            name: Nome dell'azienda
            
        Returns:
            Profilo aziendale o None se non trovato
        """
        return self.companies.get(name)
    
    def get_all_company_names(self) -> List[str]:
        """
        Ottiene tutti i nomi delle aziende.
        
        Returns:
            Lista dei nomi delle aziende
        """
        return list(self.companies.keys())
    
    def add_recent_file(self, file_path: str):
        """
        Aggiunge un file alla lista dei recenti.
        
        Args:
            file_path: Percorso del file
        """
        # Rimuovi il file se già presente
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Aggiungi all'inizio
        self.recent_files.insert(0, file_path)
        
        # Mantieni solo gli ultimi 10
        self.recent_files = self.recent_files[:10]
        
        self.save_recent_files()
    
    def get_recent_files(self) -> List[str]:
        """
        Ottiene la lista dei file recenti.
        
        Returns:
            Lista dei percorsi dei file recenti
        """
        return self.recent_files.copy()
    
    def export_config(self, export_path: str):
        """
        Esporta tutta la configurazione in un file.
        
        Args:
            export_path: Percorso del file di esportazione
        """
        export_data = {
            'settings': asdict(self.settings),
            'companies': {name: profile.to_dict() for name, profile in self.companies.items()},
            'recent_files': self.recent_files,
            'export_date': datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=True)
        except Exception as e:
            raise Exception(f"Errore nell'esportazione della configurazione: {e}")
    
    def import_config(self, import_path: str, merge: bool = True):
        """
        Importa la configurazione da un file.
        
        Args:
            import_path: Percorso del file di importazione
            merge: Se True, unisce con la configurazione esistente
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Importa le impostazioni
            if 'settings' in data:
                if merge:
                    # Aggiorna solo i campi presenti
                    for key, value in data['settings'].items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
                else:
                    # Sostituisci completamente
                    self.settings = AppSettings()
                    for key, value in data['settings'].items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
            
            # Importa i profili aziendali
            if 'companies' in data:
                if not merge:
                    self.companies.clear()
                
                for name, profile_data in data['companies'].items():
                    try:
                        self.companies[name] = CompanyProfile.from_dict(profile_data)
                    except Exception as e:
                        print(f"Errore nell'importazione del profilo {name}: {e}")
            
            # Importa i file recenti
            if 'recent_files' in data and not merge:
                self.recent_files = data['recent_files'][:10]
            
            # Salva tutto
            self.save_settings()
            self.save_companies()
            self.save_recent_files()
            
        except Exception as e:
            raise Exception(f"Errore nell'importazione della configurazione: {e}")


# Istanza globale del gestore configurazione
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """
    Ottiene l'istanza globale del gestore configurazione.
    
    Returns:
        Gestore configurazione
    """
    return config_manager