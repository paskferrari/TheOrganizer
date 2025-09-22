"""
Modulo per la normalizzazione delle stringhe aziendali.
Gestisce la normalizzazione di nomi aziendali per il matching fuzzy.
"""

import re
import unicodedata
from typing import List, Set


class CompanyNameNormalizer:
    """Classe per normalizzare i nomi delle aziende per il matching fuzzy."""
    
    # Mapping delle forme societarie comuni
    COMPANY_FORMS = {
        # Italiane
        's.p.a.': 'spa',
        's.p.a': 'spa',
        'spa': 'spa',
        's.r.l.': 'srl',
        's.r.l': 'srl',
        'srl': 'srl',
        's.a.s.': 'sas',
        's.a.s': 'sas',
        'sas': 'sas',
        's.n.c.': 'snc',
        's.n.c': 'snc',
        'snc': 'snc',
        's.s.': 'ss',
        's.s': 'ss',
        'ss': 'ss',
        
        # Internazionali
        'ltd.': 'ltd',
        'ltd': 'ltd',
        'limited': 'ltd',
        'inc.': 'inc',
        'inc': 'inc',
        'incorporated': 'inc',
        'corp.': 'corp',
        'corp': 'corp',
        'corporation': 'corp',
        'llc': 'llc',
        'l.l.c.': 'llc',
        'l.l.c': 'llc',
        'gmbh': 'gmbh',
        'g.m.b.h.': 'gmbh',
        'ag': 'ag',
        'a.g.': 'ag',
        'sa': 'sa',
        's.a.': 'sa',
        'sarl': 'sarl',
        's.a.r.l.': 'sarl',
        'bv': 'bv',
        'b.v.': 'bv',
        'nv': 'nv',
        'n.v.': 'nv',
    }
    
    # Parole comuni da rimuovere o normalizzare
    COMMON_WORDS = {
        'company', 'co', 'co.', 'group', 'gruppo', 'holding', 'international',
        'internazionale', 'global', 'worldwide', 'enterprise', 'enterprises',
        'business', 'services', 'servizi', 'solutions', 'soluzioni',
        'consulting', 'consulenza', 'technology', 'tecnologia', 'tech',
        'systems', 'sistemi', 'software', 'hardware', 'digital',
        'innovation', 'innovazione', 'development', 'sviluppo'
    }
    
    # Parole troppo generiche che non dovrebbero essere considerate nomi aziendali
    GENERIC_WORDS = {
        'area', 'zone', 'zona', 'region', 'regione', 'city', 'citta', 'town',
        'place', 'posto', 'location', 'posizione', 'site', 'sito', 'page',
        'pagina', 'file', 'document', 'documento', 'report', 'rapporto',
        'data', 'dati', 'info', 'information', 'informazione', 'detail',
        'dettaglio', 'item', 'elemento', 'component', 'componente', 'module',
        'modulo', 'lib', 'library', 'libreria', 'util', 'utils', 'utility',
        'helper', 'support', 'supporto', 'test', 'demo', 'example', 'esempio',
        'sample', 'campione', 'template', 'modello', 'base', 'core', 'main',
        'index', 'home', 'root', 'src', 'source', 'dist', 'build', 'node',
        'modules', 'assets', 'static', 'public', 'private', 'config',
        'configurazione', 'setting', 'impostazione', 'option', 'opzione'
    }
    
    def __init__(self):
        """Inizializza il normalizzatore."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compila i pattern regex per l'ottimizzazione."""
        # Pattern per rimuovere caratteri speciali
        self.special_chars_pattern = re.compile(r'[^\w\s]', re.UNICODE)
        
        # Pattern per spazi multipli
        self.multiple_spaces_pattern = re.compile(r'\s+')
        
        # Pattern per forme societarie
        company_forms_pattern = '|'.join(
            re.escape(form) for form in sorted(self.COMPANY_FORMS.keys(), key=len, reverse=True)
        )
        self.company_forms_pattern = re.compile(
            rf'\b({company_forms_pattern})\b', 
            re.IGNORECASE
        )
    
    def normalize(self, text: str) -> str:
        """
        Normalizza una stringa per il matching fuzzy.
        
        Args:
            text: Testo da normalizzare
            
        Returns:
            Testo normalizzato
        """
        if not text:
            return ""
        
        # Converti in lowercase
        normalized = text.lower().strip()
        
        # Rimuovi accenti e caratteri diacritici
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        # Normalizza forme societarie
        normalized = self._normalize_company_forms(normalized)
        
        # Rimuovi caratteri speciali (mantieni solo lettere, numeri e spazi)
        normalized = self.special_chars_pattern.sub(' ', normalized)
        
        # Normalizza spazi multipli
        normalized = self.multiple_spaces_pattern.sub(' ', normalized)
        
        # Rimuovi spazi iniziali e finali
        normalized = normalized.strip()
        
        return normalized
    
    def _normalize_company_forms(self, text: str) -> str:
        """
        Normalizza le forme societarie nel testo.
        
        Args:
            text: Testo da normalizzare
            
        Returns:
            Testo con forme societarie normalizzate
        """
        def replace_form(match):
            form = match.group(1).lower()
            return self.COMPANY_FORMS.get(form, form)
        
        return self.company_forms_pattern.sub(replace_form, text)
    
    def generate_aliases(self, company_name: str) -> List[str]:
        """
        Genera alias per un nome aziendale.
        
        Args:
            company_name: Nome dell'azienda
            
        Returns:
            Lista di alias possibili
        """
        aliases = []
        normalized = self.normalize(company_name)
        
        # Alias base
        aliases.append(normalized)
        
        # Rimuovi forme societarie
        without_forms = self._remove_company_forms(normalized)
        if without_forms != normalized:
            aliases.append(without_forms)
        
        # Rimuovi parole comuni
        without_common = self._remove_common_words(normalized)
        if without_common != normalized:
            aliases.append(without_common)
        
        # Combinazione: senza forme societarie e parole comuni
        without_both = self._remove_common_words(without_forms)
        if without_both not in aliases:
            aliases.append(without_both)
        
        # Acronimi (se il nome ha più parole)
        words = normalized.split()
        if len(words) > 1:
            acronym = ''.join(word[0] for word in words if word)
            if len(acronym) > 1:
                aliases.append(acronym)
        
        # Rimuovi duplicati e stringhe vuote
        aliases = list(dict.fromkeys(alias for alias in aliases if alias.strip()))
        
        return aliases
    
    def _remove_company_forms(self, text: str) -> str:
        """Rimuove le forme societarie dal testo."""
        words = text.split()
        filtered_words = []
        
        for word in words:
            if word not in self.COMPANY_FORMS.values():
                filtered_words.append(word)
        
        return ' '.join(filtered_words).strip()
    
    def _remove_common_words(self, text: str) -> str:
        """Rimuove le parole comuni dal testo."""
        words = text.split()
        filtered_words = []
        
        for word in words:
            if word not in self.COMMON_WORDS:
                filtered_words.append(word)
        
        return ' '.join(filtered_words).strip()
    
    def extract_company_names_from_filename(self, filename: str) -> List[str]:
        """
        Estrae possibili nomi aziendali da un nome file.
        
        Args:
            filename: Nome del file
            
        Returns:
            Lista di possibili nomi aziendali estratti
        """
        # Rimuovi estensione
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Normalizza
        normalized = self.normalize(name_without_ext)
        
        # Dividi per separatori comuni
        separators = ['-', '_', ' ', '.']
        parts = [normalized]
        
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        # Filtra parti troppo corte, date/numeri e parole troppo generiche
        filtered_parts = []
        for part in parts:
            part = part.strip()
            if (len(part) >= 3 and 
                not self._is_date_or_number(part) and 
                not self._is_generic_word(part)):
                filtered_parts.append(part)
        
        return filtered_parts
    
    def _is_date_or_number(self, text: str) -> bool:
        """Verifica se il testo sembra essere una data o un numero."""
        # Pattern per date comuni
        date_patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # dd/mm/yyyy, dd-mm-yyyy
            r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',    # yyyy/mm/dd, yyyy-mm-dd
            r'^\d{8}$',                           # yyyymmdd
            r'^\d{6}$',                           # yymmdd o ddmmyy
            r'^\d{4}$',                           # yyyy
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, text):
                return True
        
        # Verifica se è solo numeri
        if text.isdigit():
            return True
        
        # Verifica se è un numero con decimali
        try:
            float(text.replace(',', '.'))
            return True
        except ValueError:
            pass
        
        return False
    
    def _is_generic_word(self, text: str) -> bool:
        """Verifica se il testo è una parola troppo generica per essere un nome aziendale."""
        normalized_text = text.lower().strip()
        return normalized_text in self.GENERIC_WORDS


# Istanza globale del normalizzatore
normalizer = CompanyNameNormalizer()


def normalize_company_name(name: str) -> str:
    """
    Funzione di convenienza per normalizzare un nome aziendale.
    
    Args:
        name: Nome dell'azienda da normalizzare
        
    Returns:
        Nome normalizzato
    """
    return normalizer.normalize(name)


def generate_company_aliases(name: str) -> List[str]:
    """
    Funzione di convenienza per generare alias di un'azienda.
    
    Args:
        name: Nome dell'azienda
        
    Returns:
        Lista di alias
    """
    return normalizer.generate_aliases(name)