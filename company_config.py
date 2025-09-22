"""
Modulo per la gestione della configurazione delle aziende.
Carica le aziende e i loro alias da un file di configurazione YAML.
"""

import os
import yaml
from typing import Dict, List, Set, Optional
from pathlib import Path


class CompanyConfig:
    """Classe per gestire la configurazione delle aziende."""
    
    def __init__(self, config_file: str = None):
        """
        Inizializza la configurazione delle aziende.
        
        Args:
            config_file: Percorso del file di configurazione (opzionale)
        """
        self.companies: Dict[str, Dict] = {}
        self.settings: Dict = {}
        
        # Percorso predefinito del file di configurazione
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "companies_config.yaml")
        
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Carica la configurazione dal file YAML."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                self.companies = config_data.get('companies', {})
                self.settings = config_data.get('settings', {})
                
                print(f"[DEBUG] Configurazione caricata da: {self.config_file}")
                print(f"[DEBUG] Aziende configurate: {list(self.companies.keys())}")
            else:
                print(f"[DEBUG] File di configurazione non trovato: {self.config_file}")
                self._create_default_config()
        except Exception as e:
            print(f"[DEBUG] Errore nel caricamento della configurazione: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Crea una configurazione predefinita."""
        self.companies = {
            "Area Finanza Spa": {
                "aliases": [
                    "Area Finanza",
                    "AreaFinanza", 
                    "Area Finanza S.p.A.",
                    "Area Finanza SpA",
                    "AREA FINANZA SPA"
                ],
                "required_keywords": ["finanza"],
                "excluded_standalone": ["area", "spa", "s.p.a"]
            }
        }
        
        self.settings = {
            "min_threshold": 92.0,
            "filename_bonus": 15.0,
            "path_penalty": 10.0,
            "generic_words": ["area", "zone", "zona", "document", "file"]
        }
    
    def get_companies(self) -> Dict[str, Dict]:
        """Restituisce tutte le aziende configurate."""
        return self.companies
    
    def get_company_aliases(self, company_name: str) -> List[str]:
        """
        Restituisce gli alias di un'azienda.
        
        Args:
            company_name: Nome dell'azienda
            
        Returns:
            Lista degli alias
        """
        company_data = self.companies.get(company_name, {})
        return company_data.get('aliases', [])
    
    def get_required_keywords(self, company_name: str) -> List[str]:
        """
        Restituisce le parole chiave richieste per un'azienda.
        
        Args:
            company_name: Nome dell'azienda
            
        Returns:
            Lista delle parole chiave richieste
        """
        company_data = self.companies.get(company_name, {})
        return company_data.get('required_keywords', [])
    
    def get_excluded_standalone(self, company_name: str) -> List[str]:
        """
        Restituisce le parole che non possono essere match standalone per un'azienda.
        
        Args:
            company_name: Nome dell'azienda
            
        Returns:
            Lista delle parole escluse
        """
        company_data = self.companies.get(company_name, {})
        return company_data.get('excluded_standalone', [])
    
    def get_setting(self, key: str, default=None):
        """
        Restituisce un'impostazione dalla configurazione.
        
        Args:
            key: Chiave dell'impostazione
            default: Valore predefinito se la chiave non esiste
            
        Returns:
            Valore dell'impostazione
        """
        return self.settings.get(key, default)
    
    def is_valid_match(self, company_name: str, matched_text: str, full_text: str) -> bool:
        """
        Verifica se un match è valido secondo le regole dell'azienda.
        
        Args:
            company_name: Nome dell'azienda
            matched_text: Testo che ha fatto match
            full_text: Testo completo analizzato
            
        Returns:
            True se il match è valido
        """
        # Verifica parole chiave richieste
        required_keywords = self.get_required_keywords(company_name)
        if required_keywords:
            full_text_lower = full_text.lower()
            if not any(keyword.lower() in full_text_lower for keyword in required_keywords):
                return False
        
        # Verifica parole escluse standalone
        excluded_standalone = self.get_excluded_standalone(company_name)
        if excluded_standalone:
            matched_text_lower = matched_text.lower().strip()
            if matched_text_lower in [word.lower() for word in excluded_standalone]:
                return False
        
        return True
    
    def add_company(self, company_name: str, aliases: List[str] = None, 
                   required_keywords: List[str] = None, 
                   excluded_standalone: List[str] = None):
        """
        Aggiunge una nuova azienda alla configurazione.
        
        Args:
            company_name: Nome dell'azienda
            aliases: Lista degli alias
            required_keywords: Parole chiave richieste
            excluded_standalone: Parole escluse standalone
        """
        company_data = {}
        
        if aliases:
            company_data['aliases'] = aliases
        
        if required_keywords:
            company_data['required_keywords'] = required_keywords
        
        if excluded_standalone:
            company_data['excluded_standalone'] = excluded_standalone
        
        self.companies[company_name] = company_data
    
    def save_config(self):
        """Salva la configurazione corrente nel file YAML."""
        try:
            config_data = {
                'companies': self.companies,
                'settings': self.settings
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            print(f"[DEBUG] Configurazione salvata in: {self.config_file}")
        except Exception as e:
            print(f"[DEBUG] Errore nel salvataggio della configurazione: {e}")


# Istanza globale della configurazione
company_config = CompanyConfig()