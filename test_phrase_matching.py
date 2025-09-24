#!/usr/bin/env python3
"""
Test per verificare le correzioni del matching di frasi complete vs parole singole.
Questo test verifica che il sistema non faccia più match su singole parole
quando dovrebbe cercare frasi complete come "SKY LINE EUROPA".
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory corrente al path per importare i moduli
sys.path.insert(0, str(Path(__file__).parent))

from core import CompanyMatcher


def test_phrase_vs_single_word_matching():
    """Test principale per verificare il matching di frasi vs parole singole."""
    print("=== Test Matching Frasi Complete vs Parole Singole ===\n")
    
    # Inizializza il matcher
    matcher = CompanyMatcher(threshold=92.0)
    
    # Test case per SKY LINE EUROPA
    print("--- Test SKY LINE EUROPA ---")
    
    # Casi che DOVREBBERO fare match (frase completa)
    positive_cases = [
        "SKY LINE EUROPA - Contratto 2024.pdf",
        "Documento_Sky_Line_Europa_2023.docx",
        "Report Sky Line Europa S.p.A.xlsx",
        "SKYLINE_EUROPA_bilancio.pdf",
        "sky-line-europa-fattura.pdf",
        "SkyLineEuropa_documento.txt"
    ]
    
    # Casi che NON dovrebbero fare match (parole singole)
    negative_cases = [
        "sky_document.pdf",
        "line_report.txt", 
        "europa_file.docx",
        "sky_only.pdf",
        "line_only.txt",
        "europa_only.docx",
        "C:\\Users\\UTENTE\\Desktop\\sky\\file.pdf",
        "C:\\Users\\UTENTE\\Desktop\\line\\document.txt",
        "C:\\Users\\UTENTE\\Desktop\\europa\\report.pdf"
    ]
    
    print("Casi che DOVREBBERO fare match:")
    success_count = 0
    for test_file in positive_cases:
        matches = matcher.extract_company_names_from_path(test_file)
        if matches:
            company, score, matched_text = matches[0]
            if company == "SKY LINE EUROPA":
                print(f"✅ {test_file}")
                print(f"   Match: {company} (score: {score:.1f}, text: '{matched_text}')")
                success_count += 1
            else:
                print(f"❌ {test_file}")
                print(f"   Match SBAGLIATO: {company} (score: {score:.1f})")
        else:
            print(f"❌ {test_file} - NESSUN MATCH TROVATO")
    
    print(f"\nSuccessi: {success_count}/{len(positive_cases)}")
    
    print("\nCasi che NON dovrebbero fare match:")
    avoid_count = 0
    for test_file in negative_cases:
        matches = matcher.extract_company_names_from_path(test_file)
        if matches:
            company, score, matched_text = matches[0]
            print(f"❌ {test_file}")
            print(f"   Match INDESIDERATO: {company} (score: {score:.1f}, text: '{matched_text}')")
        else:
            print(f"✅ {test_file} - Correttamente ignorato")
            avoid_count += 1
    
    print(f"\nEvitati correttamente: {avoid_count}/{len(negative_cases)}")
    
    # Test per altre aziende esistenti
    print("\n--- Test Altre Aziende (verifica non regressione) ---")
    
    other_tests = [
        ("Area Finanza Spa - Bilancio 2023.pdf", "Area Finanza Spa"),
        ("area_development_report.pdf", None),  # Non dovrebbe fare match
        ("spa_generic_document.pdf", None),    # Non dovrebbe fare match
        ("NOAH SPA - Contratto.pdf", "NOAH SPA"),
        ("noah_document.pdf", None),           # Non dovrebbe fare match (solo "noah")
    ]
    
    for test_file, expected_company in other_tests:
        matches = matcher.extract_company_names_from_path(test_file)
        if matches:
            company, score, matched_text = matches[0]
            if company == expected_company:
                print(f"✅ {test_file} -> {company}")
            else:
                print(f"❌ {test_file} -> {company} (atteso: {expected_company})")
        else:
            if expected_company is None:
                print(f"✅ {test_file} -> Nessun match (corretto)")
            else:
                print(f"❌ {test_file} -> Nessun match (atteso: {expected_company})")
    
    print("\n=== Test Completato ===")


if __name__ == "__main__":
    test_phrase_vs_single_word_matching()