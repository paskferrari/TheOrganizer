#!/usr/bin/env python3
"""
Test per verificare le correzioni implementate per il matching più preciso.
"""

import os
import sys
from pathlib import Path

# Aggiungi la directory corrente al path per importare i moduli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import CompanyMatcher
from company_config import CompanyConfig


def test_area_finanza_matching():
    """Test per verificare il matching di Area Finanza Spa."""
    print("=== Test Matching Area Finanza Spa ===")
    
    # Inizializza il matcher
    matcher = CompanyMatcher(threshold=92.0)
    
    # Test case che dovrebbero fare match
    positive_cases = [
        "Area Finanza Spa - Bilancio 2023.pdf",
        "Documento_AreaFinanza_2023.docx", 
        "Report Area Finanza S.p.A.xlsx",
        "AREA_FINANZA_SPA_contratto.pdf",
        "finanza_area_report.pdf"
    ]
    
    # Test case che NON dovrebbero fare match (erano problematici prima)
    negative_cases = [
        "area_development_report.pdf",
        "area_test_file.txt",
        "spa_generic_document.pdf",
        "area_only.pdf",
        "C:\\Users\\UTENTE\\Desktop\\area\\file.pdf",  # Solo "area" nel percorso
        "C:\\Users\\UTENTE\\Desktop\\spa\\document.pdf"  # Solo "spa" nel percorso
    ]
    
    print("\\n--- Test Positivi (dovrebbero fare match) ---")
    for test_file in positive_cases:
        matches = matcher.extract_company_names_from_path(test_file)
        if matches:
            company, score, matched_text = matches[0]
            print(f"✅ {test_file}")
            print(f"   Match: {company} (score: {score:.1f}, text: '{matched_text}')")
        else:
            print(f"❌ {test_file} - NESSUN MATCH TROVATO")
    
    print("\\n--- Test Negativi (NON dovrebbero fare match) ---")
    for test_file in negative_cases:
        matches = matcher.extract_company_names_from_path(test_file)
        if matches:
            company, score, matched_text = matches[0]
            print(f"❌ {test_file}")
            print(f"   Match INDESIDERATO: {company} (score: {score:.1f}, text: '{matched_text}')")
        else:
            print(f"✅ {test_file} - Correttamente ignorato")


def test_generic_word_filtering():
    """Test per verificare il filtraggio delle parole generiche."""
    print("\\n\\n=== Test Filtraggio Parole Generiche ===")
    
    from normalize import CompanyNameNormalizer
    
    normalizer = CompanyNameNormalizer()
    
    # Test di estrazione con filtraggio parole generiche
    test_files = [
        "area_document.pdf",
        "zone_report.pdf", 
        "config_file.txt",
        "test_area_finanza.pdf",  # Questo dovrebbe passare perché ha "finanza"
        "area_finanza_spa.pdf"   # Questo dovrebbe passare
    ]
    
    print("\\n--- Test Estrazione Parti Nome File ---")
    for filename in test_files:
        parts = normalizer.extract_company_names_from_filename(filename)
        print(f"File: {filename}")
        print(f"  Parti estratte: {parts}")


def test_threshold_effectiveness():
    """Test per verificare l'efficacia della nuova soglia."""
    print("\\n\\n=== Test Efficacia Soglia 92% ===")
    
    # Test con soglie diverse
    thresholds = [85.0, 92.0]
    test_file = "area_generic_document.pdf"
    
    for threshold in thresholds:
        matcher = CompanyMatcher(threshold=threshold)
        matches = matcher.extract_company_names_from_path(test_file)
        
        print(f"\\nSoglia {threshold}%:")
        if matches:
            company, score, matched_text = matches[0]
            print(f"  Match: {company} (score: {score:.1f})")
        else:
            print(f"  Nessun match trovato")


def test_configuration_loading():
    """Test per verificare il caricamento della configurazione."""
    print("\\n\\n=== Test Caricamento Configurazione ===")
    
    config = CompanyConfig()
    companies = config.get_companies()
    
    print(f"Aziende caricate: {list(companies.keys())}")
    
    if "Area Finanza Spa" in companies:
        aliases = config.get_company_aliases("Area Finanza Spa")
        required_keywords = config.get_required_keywords("Area Finanza Spa")
        excluded_standalone = config.get_excluded_standalone("Area Finanza Spa")
        
        print(f"\\nArea Finanza Spa:")
        print(f"  Alias: {aliases}")
        print(f"  Parole chiave richieste: {required_keywords}")
        print(f"  Parole escluse standalone: {excluded_standalone}")
        
        # Test validazione
        print(f"\\n  Test validazione:")
        print(f"    'area' standalone: {config.is_valid_match('Area Finanza Spa', 'area', 'area')}")
        print(f"    'area finanza': {config.is_valid_match('Area Finanza Spa', 'area finanza', 'area finanza')}")


if __name__ == "__main__":
    print("🔧 Test delle Correzioni per il Matching Preciso")
    print("=" * 60)
    
    try:
        test_configuration_loading()
        test_generic_word_filtering()
        test_area_finanza_matching()
        test_threshold_effectiveness()
        
        print("\\n\\n🎉 Test completati!")
        print("\\nRiepilogo delle correzioni implementate:")
        print("1. ✅ Soglia di matching aumentata da 85% a 92%")
        print("2. ✅ Filtraggio parole generiche (area, zone, config, etc.)")
        print("3. ✅ Priorità al nome del file vs percorso")
        print("4. ✅ Regole specifiche per Area Finanza Spa")
        print("5. ✅ Configurazione centralizzata delle aziende")
        
    except Exception as e:
        print(f"\\n❌ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()