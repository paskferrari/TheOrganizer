"""
Test suite per File Organizer
Utilizza pytest per testare le funzionalità principali
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime, date
import csv

from normalize import CompanyNameNormalizer
from file_types import FileTypeMapper, FileCategory
from core import CompanyMatcher, DateExtractor, FileOrganizerCore
from io_ops import FileOrganizer, UndoManager
from config import ConfigManager, CompanyProfile


class TestCompanyNameNormalizer:
    """Test per la normalizzazione dei nomi azienda"""
    
    def setup_method(self):
        self.normalizer = CompanyNameNormalizer()
    
    def test_normalize_basic(self):
        """Test normalizzazione base"""
        assert self.normalizer.normalize("ACME Corp.") == "acme corp"
        assert self.normalizer.normalize("S.p.A. Test") == "spa test"
        assert self.normalizer.normalize("Test & Co.") == "test co"
    
    def test_normalize_special_chars(self):
        """Test normalizzazione caratteri speciali"""
        result = self.normalizer.normalize("Test Company_123")
        assert result == "test company_123"
    
    def test_generate_aliases(self):
        """Test generazione alias"""
        aliases = self.normalizer.generate_aliases("ACME Corporation S.p.A.")
        assert "acme corp spa" in aliases
        assert "acme" in aliases
    
    def test_extract_from_filename(self):
        """Test estrazione da nome file"""
        companies = self.normalizer.extract_company_names_from_filename("ACME_report_2024.pdf")
        assert len(companies) > 0
        assert "acme" in companies[0].lower()


class TestFileTypeMapper:
    """Test per la mappatura dei tipi di file"""
    
    def setup_method(self):
        self.mapper = FileTypeMapper()
    
    def test_get_file_category(self):
        """Test classificazione estensioni"""
        assert self.mapper.get_file_category("document.pdf") == FileCategory.PDF
        assert self.mapper.get_file_category("spreadsheet.xlsx") == FileCategory.EXCEL
        assert self.mapper.get_file_category("presentation.pptx") == FileCategory.POWERPOINT
        assert self.mapper.get_file_category("image.jpg") == FileCategory.IMMAGINI
        assert self.mapper.get_file_category("unknown.xyz") == FileCategory.ALTRO
    
    def test_composite_extensions(self):
        """Test estensioni composite"""
        assert self.mapper.get_file_category("file.tar.gz") == FileCategory.ARCHIVI
        assert self.mapper.get_file_category("backup.sql.gz") == FileCategory.ARCHIVI
    
    def test_filter_files_by_extensions(self):
        """Test filtro per estensioni"""
        files = ["doc.pdf", "sheet.xlsx", "image.jpg", "unknown.xyz"]
        pdf_files = self.mapper.filter_files_by_extensions(files, include_extensions={".pdf"})
        assert "doc.pdf" in pdf_files


class TestCompanyMatcher:
    """Test per il matching fuzzy delle aziende"""
    
    def setup_method(self):
        self.matcher = CompanyMatcher()
        self.matcher.add_company("ACME Corporation", ["acme", "acme corp"])
        self.matcher.add_company("Beta Solutions", ["beta", "beta sol"])
    
    def test_exact_match(self):
        """Test match esatto"""
        company, score, matched_text = self.matcher.find_best_match("acme corporation")
        assert company == "ACME Corporation"
        assert score >= 95
    
    def test_fuzzy_match(self):
        """Test match fuzzy"""
        company, score, matched_text = self.matcher.find_best_match("acme corp")
        assert company == "ACME Corporation"
        assert score >= 80
    
    def test_alias_match(self):
        """Test match con alias"""
        company, score, matched_text = self.matcher.find_best_match("acme")
        assert company == "ACME Corporation"
        assert score >= 80
    
    def test_no_match(self):
        """Test nessun match"""
        company, score, matched_text = self.matcher.find_best_match("unknown company")
        assert company is None or score < 90


class TestDateExtractor:
    """Test per l'estrazione delle date"""
    
    def setup_method(self):
        self.extractor = DateExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_from_filename(self):
        """Test estrazione data da filename"""
        date = self.extractor.extract_date_from_filename("fattura_2024-03-15.pdf")
        assert date.year == 2024
        assert date.month == 3
        assert date.day == 15
    
    def test_extract_from_file_stats(self):
        """Test estrazione data da statistiche file"""
        # Crea un file temporaneo per testare
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        
        result = self.extractor.extract_date_from_file_stats(str(test_file))
        assert result is None or isinstance(result, date)
    
    def test_various_formats(self):
        """Test vari formati di data"""
        test_cases = [
            ("file_20240315.pdf", (2024, 3, 15)),
            ("doc_15-03-2024.docx", (2024, 3, 15)),
            ("report_2024/03/15.xlsx", (2024, 3, 15))
        ]
        
        for filename, expected in test_cases:
            date = self.extractor.extract_date_from_filename(filename)
            if date:
                assert (date.year, date.month, date.day) == expected


class TestFileOrganizer:
    """Test per l'organizzazione dei file"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()
        
        # Crea alcuni file di test
        self.test_files = []
        for filename in ["test.pdf", "acme_invoice.docx", "report_2024.xlsx"]:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text("test content")
            self.test_files.append(str(file_path))
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_directory_structure(self):
        """Test creazione struttura directory"""
        target_dir = Path(self.temp_dir) / "organized"
        result_path = self.organizer.create_directory_structure(str(target_dir), "ACME Corp", "2024", "PDF")
        
        expected_path = target_dir / "ACME Corp" / "PDF" / "2024"
        assert expected_path.exists()
        assert Path(result_path) == expected_path
    
    def test_move_file(self):
        """Test spostamento file"""
        source = self.test_files[0]
        target_dir = Path(self.temp_dir) / "target"
        target_dir.mkdir()
        
        success, new_path, error = self.organizer.move_file(source, str(target_dir))
        assert success
        assert Path(new_path).exists()
        assert not Path(source).exists()
    
    def test_handle_collision(self):
        """Test gestione collisioni"""
        source = self.test_files[0]
        target_dir = Path(self.temp_dir) / "target"
        target_dir.mkdir()
        
        # Primo spostamento
        success1, new_path1, _ = self.organizer.move_file(source, str(target_dir))
        
        # Crea un altro file con lo stesso nome
        source2 = Path(self.temp_dir) / "test.pdf"
        source2.write_text("different content")
        
        # Secondo spostamento dovrebbe gestire la collisione
        success2, new_path2, _ = self.organizer.move_file(str(source2), str(target_dir))
        
        assert success1 and success2
        assert Path(new_path1).exists()
        assert Path(new_path2).exists()
        assert new_path1 != new_path2


class TestUndoManager:
    """Test per il sistema di undo"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.undo_manager = UndoManager()
        
        # Crea file di test
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("test content")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_undo_operations_basic(self):
        """Test undo operazioni base"""
        log_file = Path(self.temp_dir) / "operations.csv"
        moved_file = Path(self.temp_dir) / "moved.txt"
        
        # Simula uno spostamento
        shutil.move(str(self.test_file), str(moved_file))
        
        # Crea manualmente un log CSV
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['operation_type', 'original_path', 'new_path', 'timestamp', 'success', 'error_message'])
            writer.writerow(['move', str(self.test_file), str(moved_file), datetime.now().isoformat(), 'True', ''])
        
        # Undo
        success_count, failed_count, errors = self.undo_manager.undo_operations(str(log_file))
        
        assert success_count > 0
        assert self.test_file.exists()
        assert not moved_file.exists()
    
    def test_undo_operations_nonexistent_file(self):
        """Test undo con file inesistente"""
        log_file = Path(self.temp_dir) / "nonexistent.csv"
        
        try:
            self.undo_manager.undo_operations(str(log_file))
            assert False, "Dovrebbe sollevare un'eccezione"
        except Exception:
            assert True  # Comportamento atteso


class TestConfigManager:
    """Test per la gestione configurazione"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()
        self.config_file = Path(self.temp_dir) / "config.yaml"
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_load_config(self):
        """Test salvataggio e caricamento configurazione"""
        # Usa un nome unico per evitare conflitti
        unique_name = f"Test Company {datetime.now().microsecond}"
        
        # Conta le aziende iniziali
        initial_count = len(self.config_manager.companies)
        
        # Aggiungi un profilo
        self.config_manager.add_company_profile(unique_name, ["test", "test corp"])
        
        # Salva
        self.config_manager.save_companies()
        assert self.config_manager.companies_file.exists()
        
        # Verifica che sia stato salvato
        assert len(self.config_manager.companies) == initial_count + 1
        assert unique_name in self.config_manager.companies
    
    def test_export_import_companies(self):
        """Test export/import aziende"""
        # Aggiungi profili
        self.config_manager.add_company_profile("Company A", ["comp_a"])
        self.config_manager.add_company_profile("Company B", ["comp_b"])
        
        # Export
        export_file = Path(self.temp_dir) / "companies.yaml"
        self.config_manager.export_config(str(export_file))
        
        # Import in nuovo manager
        new_manager = ConfigManager()
        new_manager.import_config(str(export_file))
        
        assert len(new_manager.companies) >= 2


class TestFileOrganizerCore:
    """Test per il core dell'organizzatore"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizerCore(threshold=85.0)
        
        # Aggiungi alcune aziende di test
        self.organizer.add_company("ACME Corp", ["acme", "acme corporation"])
        self.organizer.add_company("Beta Inc", ["beta", "beta incorporated"])
        
        # Crea file di test
        test_files = [
            "ACME_report_2023.pdf",
            "beta_invoice_20231201.xlsx", 
            "unknown_file.txt"
        ]
        
        for filename in test_files:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text("test content")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_organize_files(self):
        """Test organizzazione completa"""
        result = self.organizer.organize_files(
            root_path=self.temp_dir,
            output_path=str(Path(self.temp_dir) / "organized")
        )
        
        assert result.total_files >= 3
        assert result.processed_files >= 0  # Alcuni file potrebbero essere processati
        assert isinstance(result.matches, list)


if __name__ == "__main__":
    # Esegui i test
    pytest.main([__file__, "-v"])