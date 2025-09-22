"""
Interfaccia grafica moderna per il File Organizer.
Utilizza PyQt6 con tema scuro/chiaro, drag&drop e operazioni asincrone.
"""

import sys
import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Set
import threading
import traceback

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QProgressBar, QSlider, QCheckBox, QComboBox, QDateEdit, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox, QSplitter, QHeaderView, QFrame,
    QScrollArea, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, QSize, QMimeData, QUrl
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QDragEnterEvent,
    QDropEvent, QAction
)

from core import FileOrganizerCore, OrganizationResult, FileMatch
from config import get_config_manager, CompanyProfile
from normalize import generate_company_aliases
from io_ops import UndoManager


class WorkerThread(QThread):
    """Thread per operazioni asincrone."""
    
    progress_updated = pyqtSignal(str, int, int)  # phase, current, total
    result_ready = pyqtSignal(object)  # OrganizationResult
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, organizer: FileOrganizerCore, root_path: str, output_path: str,
                 since_date: Optional[date] = None, until_date: Optional[date] = None):
        super().__init__()
        self.organizer = organizer
        self.root_path = root_path
        self.output_path = output_path
        self.since_date = since_date
        self.until_date = until_date
        self._is_cancelled = False
    
    def run(self):
        """Esegue l'organizzazione in background."""
        try:
            def progress_callback(phase: str, current: int, total: int):
                if not self._is_cancelled:
                    self.progress_updated.emit(phase, current, total)
            
            result = self.organizer.organize_files(
                self.root_path,
                self.output_path,
                since_date=self.since_date,
                until_date=self.until_date,
                progress_callback=progress_callback
            )
            
            if not self._is_cancelled:
                self.result_ready.emit(result)
                
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancella l'operazione."""
        self._is_cancelled = True


class UndoWorkerThread(QThread):
    """Thread per operazioni di undo."""
    
    progress_updated = pyqtSignal(str, int, int)
    result_ready = pyqtSignal(int, int, list)  # undone_count, error_count, errors
    error_occurred = pyqtSignal(str)
    
    def __init__(self, log_file: str, dry_run: bool = False):
        super().__init__()
        self.log_file = log_file
        self.dry_run = dry_run
        self._is_cancelled = False
    
    def run(self):
        """Esegue l'undo in background."""
        try:
            undo_manager = UndoManager(dry_run=self.dry_run)
            undone_count, error_count, errors = undo_manager.undo_operations(self.log_file)
            
            if not self._is_cancelled:
                self.result_ready.emit(undone_count, error_count, errors)
                
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancella l'operazione."""
        self._is_cancelled = True


class CompanyProfileDialog(QDialog):
    """Dialog per gestire i profili azienda."""
    
    def __init__(self, parent=None, profile: Optional[CompanyProfile] = None):
        super().__init__(parent)
        self.profile = profile
        self.setup_ui()
        
        if profile:
            self.load_profile(profile)
    
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        self.setWindowTitle("Profilo Azienda")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Nome azienda
        layout.addWidget(QLabel("Nome Azienda:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Alias
        layout.addWidget(QLabel("Alias (uno per riga):"))
        self.aliases_edit = QTextEdit()
        self.aliases_edit.setMaximumHeight(100)
        layout.addWidget(self.aliases_edit)
        
        # Pulsante per generare alias automatici
        auto_btn = QPushButton("Genera Alias Automatici")
        auto_btn.clicked.connect(self.generate_auto_aliases)
        layout.addWidget(auto_btn)
        
        # Soglia fuzzy
        layout.addWidget(QLabel("Soglia Fuzzy:"))
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 100)
        self.threshold_slider.setValue(85)
        self.threshold_label = QLabel("85%")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"{v}%")
        )
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        layout.addLayout(threshold_layout)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def generate_auto_aliases(self):
        """Genera alias automatici per l'azienda."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Attenzione", "Inserisci prima il nome dell'azienda.")
            return
        
        aliases = generate_company_aliases(name)
        current_aliases = self.aliases_edit.toPlainText().strip()
        
        if current_aliases:
            current_list = [a.strip() for a in current_aliases.split('\n') if a.strip()]
            aliases.extend(current_list)
            aliases = list(set(aliases))  # Rimuovi duplicati
        
        self.aliases_edit.setPlainText('\n'.join(aliases))
    
    def load_profile(self, profile: CompanyProfile):
        """Carica un profilo esistente."""
        self.name_edit.setText(profile.name)
        self.aliases_edit.setPlainText('\n'.join(profile.aliases))
        # Usa la soglia di default dalle impostazioni
        from config import get_config_manager
        config_manager = get_config_manager()
        self.threshold_slider.setValue(int(config_manager.settings.default_threshold))
    
    def get_profile(self) -> Optional[CompanyProfile]:
        """Restituisce il profilo configurato."""
        name = self.name_edit.text().strip()
        if not name:
            return None
        
        aliases_text = self.aliases_edit.toPlainText().strip()
        aliases = [a.strip() for a in aliases_text.split('\n') if a.strip()]
        
        return CompanyProfile(
            name=name,
            aliases=aliases,
            created_at=datetime.now(),
            last_used=datetime.now()
        )


class DragDropWidget(QWidget):
    """Widget che supporta drag & drop di file e cartelle."""
    
    files_dropped = pyqtSignal(list)  # Lista di percorsi
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia."""
        layout = QVBoxLayout(self)
        
        self.drop_label = QLabel("Trascina file o cartelle qui\no usa il pulsante Sfoglia")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: rgba(0, 0, 0, 0.05);
                font-size: 14px;
                color: #666;
            }
        """)
        layout.addWidget(self.drop_label)
        
        self.browse_btn = QPushButton("Sfoglia...")
        self.browse_btn.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Gestisce l'ingresso del drag."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                    background-color: rgba(76, 175, 80, 0.1);
                    font-size: 14px;
                    color: #4CAF50;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Gestisce l'uscita del drag."""
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: rgba(0, 0, 0, 0.05);
                font-size: 14px;
                color: #666;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Gestisce il drop dei file."""
        self.dragLeaveEvent(event)
        
        urls = event.mimeData().urls()
        paths = []
        
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.exists(path):
                    paths.append(path)
        
        if paths:
            self.files_dropped.emit(paths)
    
    def browse_folder(self):
        """Apre il dialog per selezionare una cartella."""
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella")
        if folder:
            self.files_dropped.emit([folder])


class FileOrganizerGUI(QMainWindow):
    """Interfaccia grafica principale del File Organizer."""
    
    def __init__(self):
        super().__init__()
        self.config_manager = get_config_manager()
        self.settings = QSettings("FileOrganizer", "GUI")
        self.current_worker = None
        self.current_undo_worker = None
        
        # Timer per salvare le impostazioni
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_settings)
        self.save_timer.setSingleShot(True)
        
        self.setup_ui()
        self.load_settings()
        self.load_stylesheet()
    
    def setup_ui(self):
        """Configura l'interfaccia utente."""
        self.setWindowTitle("File Organizer - Organizzatore File Aziendali")
        self.setMinimumSize(1000, 700)
        
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principale
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter per dividere controlli e risultati
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Pannello controlli (sinistra)
        controls_widget = self.create_controls_panel()
        splitter.addWidget(controls_widget)
        
        # Pannello risultati (destra)
        results_widget = self.create_results_panel()
        splitter.addWidget(results_widget)
        
        # Imposta le proporzioni del splitter
        splitter.setSizes([400, 600])
        
        # Barra di stato
        self.statusBar().showMessage("Pronto")
        
        # Menu bar
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """Crea la barra dei menu."""
        menubar = self.menuBar()
        
        # Menu File
        file_menu = menubar.addMenu("File")
        
        new_profile_action = QAction("Nuovo Profilo Azienda", self)
        new_profile_action.triggered.connect(self.new_company_profile)
        file_menu.addAction(new_profile_action)
        
        import_action = QAction("Importa Configurazione", self)
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        export_action = QAction("Esporta Configurazione", self)
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Esci", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Visualizza
        view_menu = menubar.addMenu("Visualizza")
        
        theme_action = QAction("Cambia Tema", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Menu Aiuto
        help_menu = menubar.addMenu("Aiuto")
        
        about_action = QAction("Informazioni", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_controls_panel(self) -> QWidget:
        """Crea il pannello dei controlli."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area per i controlli
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        controls_content = QWidget()
        controls_layout = QVBoxLayout(controls_content)
        
        # Sezione Input
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        
        # Drag & Drop per cartella
        self.drag_drop = DragDropWidget()
        self.drag_drop.files_dropped.connect(self.handle_dropped_files)
        input_layout.addWidget(self.drag_drop)
        
        # Percorso cartella
        input_layout.addWidget(QLabel("Cartella Sorgente:"))
        path_layout = QHBoxLayout()
        self.root_path_edit = QLineEdit()
        self.browse_btn = QPushButton("Sfoglia")
        self.browse_btn.clicked.connect(self.browse_root_folder)
        path_layout.addWidget(self.root_path_edit)
        path_layout.addWidget(self.browse_btn)
        input_layout.addLayout(path_layout)
        
        # Cartella destinazione
        input_layout.addWidget(QLabel("Cartella Destinazione (opzionale):"))
        output_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_browse_btn = QPushButton("Sfoglia")
        self.output_browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        input_layout.addLayout(output_layout)
        
        controls_layout.addWidget(input_group)
        
        # Sezione Azienda
        company_group = QGroupBox("Azienda")
        company_layout = QVBoxLayout(company_group)
        
        # Selezione azienda
        company_select_layout = QHBoxLayout()
        self.company_combo = QComboBox()
        self.company_combo.setEditable(True)
        self.company_combo.currentTextChanged.connect(self.on_company_changed)
        self.new_company_btn = QPushButton("Nuovo")
        self.new_company_btn.clicked.connect(self.new_company_profile)
        self.edit_company_btn = QPushButton("Modifica")
        self.edit_company_btn.clicked.connect(self.edit_company_profile)
        
        company_select_layout.addWidget(self.company_combo, 2)
        company_select_layout.addWidget(self.new_company_btn)
        company_select_layout.addWidget(self.edit_company_btn)
        company_layout.addLayout(company_select_layout)
        
        # Alias
        company_layout.addWidget(QLabel("Alias (separati da virgola):"))
        self.aliases_edit = QLineEdit()
        company_layout.addWidget(self.aliases_edit)
        
        controls_layout.addWidget(company_group)
        
        # Sezione Parametri
        params_group = QGroupBox("Parametri")
        params_layout = QVBoxLayout(params_group)
        
        # Soglia fuzzy
        params_layout.addWidget(QLabel("Soglia Fuzzy Matching:"))
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 100)
        self.threshold_slider.setValue(85)
        self.threshold_label = QLabel("85%")
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        params_layout.addLayout(threshold_layout)
        
        # Filtri data
        date_layout = QGridLayout()
        date_layout.addWidget(QLabel("Data Inizio:"), 0, 0)
        self.since_date = QDateEdit()
        self.since_date.setCalendarPopup(True)
        self.since_date.setDate(datetime.now().date().replace(month=1, day=1))
        self.since_check = QCheckBox("Abilita")
        date_layout.addWidget(self.since_date, 0, 1)
        date_layout.addWidget(self.since_check, 0, 2)
        
        date_layout.addWidget(QLabel("Data Fine:"), 1, 0)
        self.until_date = QDateEdit()
        self.until_date.setCalendarPopup(True)
        self.until_date.setDate(datetime.now().date())
        self.until_check = QCheckBox("Abilita")
        date_layout.addWidget(self.until_date, 1, 1)
        date_layout.addWidget(self.until_check, 1, 2)
        
        params_layout.addLayout(date_layout)
        
        # Filtri estensioni
        params_layout.addWidget(QLabel("Includi Estensioni (es: pdf,docx,xlsx):"))
        self.include_ext_edit = QLineEdit()
        params_layout.addWidget(self.include_ext_edit)
        
        params_layout.addWidget(QLabel("Escludi Estensioni (es: tmp,log):"))
        self.exclude_ext_edit = QLineEdit()
        params_layout.addWidget(self.exclude_ext_edit)
        
        # Dimensione massima file
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Dimensione Max (MB):"))
        self.max_size_spin = QDoubleSpinBox()
        self.max_size_spin.setRange(0.1, 10000)
        self.max_size_spin.setValue(100)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_check = QCheckBox("Abilita")
        size_layout.addWidget(self.max_size_spin)
        size_layout.addWidget(self.max_size_check)
        params_layout.addLayout(size_layout)
        
        controls_layout.addWidget(params_group)
        
        # Sezione Opzioni
        options_group = QGroupBox("Opzioni")
        options_layout = QVBoxLayout(options_group)
        
        self.dry_run_check = QCheckBox("Modalità Simulazione (Dry Run)")
        self.dry_run_check.setChecked(False)
        options_layout.addWidget(self.dry_run_check)
        
        controls_layout.addWidget(options_group)
        
        # Pulsanti azione
        buttons_layout = QVBoxLayout()
        
        self.preview_btn = QPushButton("Anteprima")
        self.preview_btn.clicked.connect(self.preview_organization)
        self.preview_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        buttons_layout.addWidget(self.preview_btn)
        
        self.organize_btn = QPushButton("Organizza File")
        self.organize_btn.clicked.connect(self.organize_files)
        self.organize_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; background-color: #4CAF50; }")
        buttons_layout.addWidget(self.organize_btn)
        
        self.undo_btn = QPushButton("Annulla Ultima Operazione")
        self.undo_btn.clicked.connect(self.undo_last_operation)
        buttons_layout.addWidget(self.undo_btn)
        
        self.cancel_btn = QPushButton("Annulla Operazione")
        self.cancel_btn.clicked.connect(self.cancel_operation)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)
        
        controls_layout.addLayout(buttons_layout)
        
        # Aggiungi stretch per spingere tutto in alto
        controls_layout.addStretch()
        
        scroll.setWidget(controls_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_results_panel(self) -> QWidget:
        """Crea il pannello dei risultati."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tab widget per organizzare i risultati
        self.results_tabs = QTabWidget()
        layout.addWidget(self.results_tabs)
        
        # Tab Anteprima
        self.preview_tab = self.create_preview_tab()
        self.results_tabs.addTab(self.preview_tab, "Anteprima")
        
        # Tab Log
        self.log_tab = self.create_log_tab()
        self.results_tabs.addTab(self.log_tab, "Log")
        
        # Barra di progresso
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("Pronto")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Statistiche
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("QLabel { font-weight: bold; padding: 5px; }")
        progress_layout.addWidget(self.stats_label)
        
        layout.addLayout(progress_layout)
        
        return widget
    
    def create_preview_tab(self) -> QWidget:
        """Crea il tab dell'anteprima."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabella risultati
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Origine", "Corrispondenza %", "Tipo di file", "Data file"
        ])
        
        # Configura la tabella
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Origine - stretch per mostrare il percorso completo
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Corrispondenza %
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tipo di file
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Data file
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.results_table)
        
        return widget
    
    def create_log_tab(self) -> QWidget:
        """Crea il tab del log."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Area di testo per il log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Pulsanti per il log
        log_buttons = QHBoxLayout()
        
        clear_log_btn = QPushButton("Pulisci Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_buttons.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("Salva Log")
        save_log_btn.clicked.connect(self.save_log)
        log_buttons.addWidget(save_log_btn)
        
        log_buttons.addStretch()
        layout.addLayout(log_buttons)
        
        return widget
    
    def load_settings(self):
        """Carica le impostazioni salvate."""
        # Geometria finestra
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Ultimo percorso
        last_path = self.settings.value("last_root_path", "")
        if last_path and os.path.exists(last_path):
            self.root_path_edit.setText(last_path)
        
        # Ultima azienda
        last_company = self.settings.value("last_company", "")
        
        # Carica le aziende nel combo
        self.refresh_companies()
        
        if last_company:
            index = self.company_combo.findText(last_company)
            if index >= 0:
                self.company_combo.setCurrentIndex(index)
        
        # Altri parametri
        self.threshold_slider.setValue(self.settings.value("threshold", 85, int))
        self.dry_run_check.setChecked(self.settings.value("dry_run", True, bool))
    
    def save_settings(self):
        """Salva le impostazioni."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_root_path", self.root_path_edit.text())
        self.settings.setValue("last_company", self.company_combo.currentText())
        self.settings.setValue("threshold", self.threshold_slider.value())
        self.settings.setValue("dry_run", self.dry_run_check.isChecked())
    
    def load_stylesheet(self):
        """Carica il foglio di stile."""
        style_path = Path(__file__).parent / "assets" / "style.qss"
        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
    
    def refresh_companies(self):
        """Aggiorna la lista delle aziende."""
        current_text = self.company_combo.currentText()
        self.company_combo.clear()
        
        companies = self.config_manager.get_all_company_names()
        self.company_combo.addItems(sorted(companies))
        
        # Ripristina la selezione se possibile
        if current_text:
            index = self.company_combo.findText(current_text)
            if index >= 0:
                self.company_combo.setCurrentIndex(index)
            else:
                self.company_combo.setCurrentText(current_text)
    
    def handle_dropped_files(self, paths: List[str]):
        """Gestisce i file trascinati."""
        # Prendi il primo percorso valido
        for path in paths:
            if os.path.isdir(path):
                self.root_path_edit.setText(path)
                self.log_message(f"Cartella selezionata: {path}")
                break
        else:
            # Se non ci sono cartelle, prendi la directory del primo file
            if paths:
                first_file = Path(paths[0])
                if first_file.is_file():
                    self.root_path_edit.setText(str(first_file.parent))
                    self.log_message(f"Cartella selezionata: {first_file.parent}")
    
    def browse_root_folder(self):
        """Apre il dialog per selezionare la cartella sorgente."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona Cartella Sorgente", self.root_path_edit.text()
        )
        if folder:
            self.root_path_edit.setText(folder)
    
    def browse_output_folder(self):
        """Apre il dialog per selezionare la cartella destinazione."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleziona Cartella Destinazione", self.output_path_edit.text()
        )
        if folder:
            self.output_path_edit.setText(folder)
    
    def update_threshold_label(self, value: int):
        """Aggiorna l'etichetta della soglia."""
        self.threshold_label.setText(f"{value}%")
        # Avvia il timer per salvare le impostazioni
        self.save_timer.start(1000)
    
    def on_company_changed(self, company_name: str):
        """Gestisce il cambio di azienda."""
        if not company_name:
            return
        
        # Carica il profilo se esiste
        if company_name in self.config_manager.get_all_company_names():
            profile = self.config_manager.get_company_profile(company_name)
            self.aliases_edit.setText(', '.join(profile.aliases))
            self.threshold_slider.setValue(int(self.config_manager.settings.default_threshold))
    
    def new_company_profile(self):
        """Crea un nuovo profilo azienda."""
        dialog = CompanyProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile = dialog.get_profile()
            if profile:
                self.config_manager.add_company_profile(profile.name, profile.aliases)
                self.refresh_companies()
                
                # Seleziona la nuova azienda
                index = self.company_combo.findText(profile.name)
                if index >= 0:
                    self.company_combo.setCurrentIndex(index)
                
                self.log_message(f"Profilo azienda '{profile.name}' creato con successo")
    
    def edit_company_profile(self):
        """Modifica il profilo azienda corrente."""
        company_name = self.company_combo.currentText().strip()
        if not company_name:
            QMessageBox.warning(self, "Attenzione", "Seleziona un'azienda da modificare.")
            return
        
        profile = None
        if company_name in self.config_manager.get_all_company_names():
            profile = self.config_manager.get_company_profile(company_name)
        
        dialog = CompanyProfileDialog(self, profile)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_profile = dialog.get_profile()
            if new_profile:
                # Rimuovi il vecchio profilo se il nome è cambiato
                if profile and profile.name != new_profile.name:
                    self.config_manager.remove_company_profile(profile.name)
                
                self.config_manager.add_company_profile(new_profile.name, new_profile.aliases)
                self.refresh_companies()
                
                # Seleziona l'azienda modificata
                index = self.company_combo.findText(new_profile.name)
                if index >= 0:
                    self.company_combo.setCurrentIndex(index)
                
                self.log_message(f"Profilo azienda '{new_profile.name}' aggiornato")
    
    def validate_inputs(self) -> bool:
        """Valida gli input dell'utente."""
        # Controlla il percorso sorgente
        root_path = self.root_path_edit.text().strip()
        if not root_path:
            QMessageBox.warning(self, "Errore", "Seleziona una cartella sorgente.")
            return False
        
        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            QMessageBox.warning(self, "Errore", "La cartella sorgente non esiste.")
            return False
        
        # Controlla il nome azienda
        company_name = self.company_combo.currentText().strip()
        if not company_name:
            QMessageBox.warning(self, "Errore", "Inserisci il nome dell'azienda.")
            return False
        
        # Controlla il percorso destinazione se specificato
        output_path = self.output_path_edit.text().strip()
        if output_path and not os.path.exists(output_path):
            reply = QMessageBox.question(
                self, "Conferma", 
                f"La cartella destinazione '{output_path}' non esiste. Vuoi crearla?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(output_path, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Impossibile creare la cartella: {e}")
                    return False
            else:
                return False
        
        return True
    
    def create_organizer(self) -> FileOrganizerCore:
        """Crea l'organizzatore con i parametri correnti."""
        organizer = FileOrganizerCore(
            threshold=self.threshold_slider.value(),
            dry_run=self.dry_run_check.isChecked()
        )
        
        # Configura i filtri
        include_ext = None
        exclude_ext = None
        
        if self.include_ext_edit.text().strip():
            include_ext = set()
            for ext in self.include_ext_edit.text().split(','):
                ext = ext.strip()
                if ext:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    include_ext.add(ext.lower())
        
        if self.exclude_ext_edit.text().strip():
            exclude_ext = set()
            for ext in self.exclude_ext_edit.text().split(','):
                ext = ext.strip()
                if ext:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    exclude_ext.add(ext.lower())
        
        max_size = None
        if self.max_size_check.isChecked():
            max_size = self.max_size_spin.value()
        
        organizer.set_filters(
            include_extensions=include_ext,
            exclude_extensions=exclude_ext,
            max_file_size_mb=max_size
        )
        
        # Aggiungi l'azienda
        company_name = self.company_combo.currentText().strip()
        aliases = []
        if self.aliases_edit.text().strip():
            aliases = [a.strip() for a in self.aliases_edit.text().split(',') if a.strip()]
        
        organizer.add_company(company_name, aliases)
        
        return organizer
    
    def preview_organization(self):
        """Esegue l'anteprima dell'organizzazione."""
        if not self.validate_inputs():
            return
        
        # Forza la modalità dry run per l'anteprima
        original_dry_run = self.dry_run_check.isChecked()
        self.dry_run_check.setChecked(True)
        
        try:
            self.start_organization()
        finally:
            # Ripristina la modalità originale
            self.dry_run_check.setChecked(original_dry_run)
    
    def organize_files(self):
        """Esegue l'organizzazione dei file."""
        if not self.validate_inputs():
            return
        
        # Conferma se non è in modalità dry run
        if not self.dry_run_check.isChecked():
            reply = QMessageBox.question(
                self, "Conferma", 
                "Sei sicuro di voler procedere con l'organizzazione dei file?\n"
                "Questa operazione sposterà fisicamente i file.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.start_organization()
    
    def start_organization(self):
        """Avvia l'organizzazione in background."""
        if self.current_worker and self.current_worker.isRunning():
            return
        
        # Prepara i parametri
        root_path = self.root_path_edit.text().strip()
        output_path = self.output_path_edit.text().strip() or root_path
        
        since_date = None
        until_date = None
        
        if self.since_check.isChecked():
            qdate = self.since_date.date()
            since_date = date(qdate.year(), qdate.month(), qdate.day())
        
        if self.until_check.isChecked():
            qdate = self.until_date.date()
            until_date = date(qdate.year(), qdate.month(), qdate.day())
        
        # Crea l'organizzatore
        organizer = self.create_organizer()
        
        # Verifica che ci sia almeno un'azienda configurata
        if not organizer.matcher.company_aliases:
            self.log_message("ERRORE: Nessuna azienda configurata!")
            self.log_message("Aggiungi almeno un'azienda nel campo 'Nome Azienda' prima di procedere.")
            QMessageBox.warning(
                self, "Nessuna Azienda", 
                "Devi inserire almeno un nome di azienda prima di organizzare i file.\n"
                "Inserisci il nome dell'azienda nel campo apposito."
            )
            return
        
        # Configura il logging se non è dry run
        if not self.dry_run_check.isChecked():
            log_file = f"file_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            from io_ops import FileOperationLogger
            logger = FileOperationLogger(log_file)
            organizer.set_logger(logger)
            self.log_message(f"Log delle operazioni: {log_file}")
        
        # Avvia il worker thread
        self.current_worker = WorkerThread(organizer, root_path, output_path, since_date, until_date)
        self.current_worker.progress_updated.connect(self.update_progress)
        self.current_worker.result_ready.connect(self.handle_organization_result)
        self.current_worker.error_occurred.connect(self.handle_organization_error)
        self.current_worker.finished.connect(self.organization_finished)
        
        # Aggiorna l'interfaccia
        self.set_operation_running(True)
        self.clear_results()
        self.log_message(f"{'[ANTEPRIMA] ' if self.dry_run_check.isChecked() else ''}Avvio organizzazione...")
        
        self.current_worker.start()
    
    def update_progress(self, phase: str, current: int, total: int):
        """Aggiorna la barra di progresso."""
        self.progress_label.setText(f"{phase} [{current}/{total}]")
        
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
        
        # Aggiorna anche la barra di stato
        if total > 0:
            self.statusBar().showMessage(f"{phase} - {percentage}% completato")
        else:
            self.statusBar().showMessage(f"{phase} - {current} elementi")
    
    def handle_organization_result(self, result: OrganizationResult):
        """Gestisce il risultato dell'organizzazione."""
        self.display_results(result)
        
        # Aggiorna le statistiche
        stats = f"File trovati: {result.total_files} | "
        stats += f"Processati: {result.processed_files} | "
        stats += f"Saltati: {result.skipped_files}"
        
        if not self.dry_run_check.isChecked():
            stats += f" | Spostati: {result.successful_moves} | Errori: {result.failed_moves}"
        
        self.stats_label.setText(stats)
        
        # Log del risultato
        self.log_message(f"Organizzazione completata: {len(result.matches)} match trovati")
        
        # Fornisci feedback dettagliato se non sono stati trovati file da organizzare
        if result.total_files == 0:
            self.log_message("ATTENZIONE: Nessun file trovato nella cartella sorgente.")
            self.log_message("Verifica che la cartella contenga file PDF, DOC, DOCX, XLS, XLSX o TXT.")
        elif result.processed_files == 0:
            self.log_message("ATTENZIONE: Nessun file processato.")
            self.log_message("Possibili cause:")
            self.log_message("- I file non contengono il nome dell'azienda specificata")
            self.log_message("- La soglia di matching è troppo alta")
            self.log_message("- I file sono stati filtrati per data o dimensione")
        elif result.successful_moves == 0 and not self.dry_run_check.isChecked():
            self.log_message("ATTENZIONE: Nessun file è stato spostato.")
            self.log_message("Verifica i permessi della cartella di destinazione.")
        
        if result.errors:
            self.log_message(f"Errori: {len(result.errors)}")
            for error in result.errors[:10]:  # Mostra solo i primi 10 errori
                self.log_message(f"  - {error}")
        
        # Salva le impostazioni
        self.save_settings()
    
    def handle_organization_error(self, error_message: str):
        """Gestisce gli errori dell'organizzazione."""
        self.log_message(f"ERRORE: {error_message}")
        QMessageBox.critical(self, "Errore", f"Errore durante l'organizzazione:\n{error_message}")
    
    def organization_finished(self):
        """Chiamato quando l'organizzazione è terminata."""
        self.set_operation_running(False)
        self.statusBar().showMessage("Operazione completata")
    
    def cancel_operation(self):
        """Cancella l'operazione corrente."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(3000)  # Aspetta max 3 secondi
            self.log_message("Operazione cancellata dall'utente")
    
    def set_operation_running(self, running: bool):
        """Aggiorna l'interfaccia per indicare se un'operazione è in corso."""
        # Disabilita/abilita i controlli
        self.preview_btn.setEnabled(not running)
        self.organize_btn.setEnabled(not running)
        self.undo_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        
        # Mostra/nasconde la barra di progresso
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setValue(0)
        
        if not running:
            self.progress_label.setText("Pronto")
    
    def clear_results(self):
        """Pulisce i risultati precedenti."""
        self.results_table.setRowCount(0)
        self.stats_label.setText("")
    
    def display_results(self, result: OrganizationResult):
        """Mostra i risultati nella tabella."""
        self.results_table.setRowCount(len(result.matches))
        
        for row, match in enumerate(result.matches):
            # Origine (percorso completo: "cartella file trovato"\filetrovato.*)
            file_path = Path(match.file_path)
            origin_path = f"{file_path.parent}\\{file_path.name}"
            self.results_table.setItem(row, 0, QTableWidgetItem(origin_path))
            
            # Corrispondenza %
            score_item = QTableWidgetItem(f"{match.match_score:.1f}%")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 1, score_item)
            
            # Tipo di file
            file_type = file_path.suffix.upper() if file_path.suffix else "N/A"
            if file_type.startswith('.'):
                file_type = file_type[1:]  # Rimuove il punto iniziale
            type_item = QTableWidgetItem(file_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 2, type_item)
            
            # Data file
            date_str = match.file_date.strftime("%Y-%m-%d") if match.file_date else "N/A"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 3, date_item)
    
    def undo_last_operation(self):
        """Annulla l'ultima operazione."""
        # Trova l'ultimo file di log
        log_files = list(Path.cwd().glob("file_organizer_*.csv"))
        if not log_files:
            QMessageBox.information(self, "Info", "Nessun file di log trovato.")
            return
        
        # Ordina per data di modifica
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        latest_log = log_files[0]
        
        # Conferma
        reply = QMessageBox.question(
            self, "Conferma Undo", 
            f"Vuoi annullare le operazioni dal file:\n{latest_log.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_undo_operation(str(latest_log))
    
    def start_undo_operation(self, log_file: str):
        """Avvia l'operazione di undo."""
        if self.current_undo_worker and self.current_undo_worker.isRunning():
            return
        
        self.current_undo_worker = UndoWorkerThread(log_file, self.dry_run_check.isChecked())
        self.current_undo_worker.result_ready.connect(self.handle_undo_result)
        self.current_undo_worker.error_occurred.connect(self.handle_undo_error)
        self.current_undo_worker.finished.connect(self.undo_finished)
        
        self.set_operation_running(True)
        self.log_message(f"{'[SIMULAZIONE] ' if self.dry_run_check.isChecked() else ''}Avvio undo da {log_file}...")
        
        self.current_undo_worker.start()
    
    def handle_undo_result(self, undone_count: int, error_count: int, errors: List[str]):
        """Gestisce il risultato dell'undo."""
        self.log_message(f"Undo completato: {undone_count} operazioni annullate, {error_count} errori")
        
        if errors:
            for error in errors[:10]:  # Mostra solo i primi 10 errori
                self.log_message(f"  - {error}")
        
        QMessageBox.information(
            self, "Undo Completato", 
            f"Operazioni annullate: {undone_count}\nErrori: {error_count}"
        )
    
    def handle_undo_error(self, error_message: str):
        """Gestisce gli errori dell'undo."""
        self.log_message(f"ERRORE UNDO: {error_message}")
        QMessageBox.critical(self, "Errore Undo", f"Errore durante l'undo:\n{error_message}")
    
    def undo_finished(self):
        """Chiamato quando l'undo è terminato."""
        self.set_operation_running(False)
    
    def log_message(self, message: str):
        """Aggiunge un messaggio al log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Scorri automaticamente verso il basso
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Pulisce il log."""
        self.log_text.clear()
    
    def save_log(self):
        """Salva il log su file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salva Log", f"file_organizer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "File di testo (*.txt);;Tutti i file (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log_message(f"Log salvato in: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile salvare il log:\n{e}")
    
    def import_config(self):
        """Importa la configurazione da file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importa Configurazione", "", "File YAML (*.yaml *.yml);;Tutti i file (*)"
        )
        
        if filename:
            try:
                self.config_manager.import_config(filename)
                self.refresh_companies()
                self.log_message(f"Configurazione importata da: {filename}")
                QMessageBox.information(self, "Successo", "Configurazione importata con successo!")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile importare la configurazione:\n{e}")
    
    def export_config(self):
        """Esporta la configurazione su file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Esporta Configurazione", "file_organizer_config.yaml",
            "File YAML (*.yaml *.yml);;Tutti i file (*)"
        )
        
        if filename:
            try:
                self.config_manager.export_config(filename)
                self.log_message(f"Configurazione esportata in: {filename}")
                QMessageBox.information(self, "Successo", "Configurazione esportata con successo!")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile esportare la configurazione:\n{e}")
    
    def toggle_theme(self):
        """Cambia il tema dell'applicazione."""
        # Implementazione semplificata - in una versione completa
        # si potrebbe avere un sistema di temi più sofisticato
        current_style = self.styleSheet()
        if "dark" in current_style.lower():
            # Passa al tema chiaro
            self.setStyleSheet("")
        else:
            # Passa al tema scuro
            self.load_stylesheet()
    
    def show_about(self):
        """Mostra le informazioni sull'applicazione."""
        QMessageBox.about(
            self, "Informazioni", 
            "File Organizer v1.0\n\n"
            "Organizzatore di file aziendali con matching fuzzy.\n\n"
            "Caratteristiche:\n"
            "• Matching fuzzy robusto\n"
            "• Organizzazione automatica per tipo e data\n"
            "• Supporto per alias aziendali\n"
            "• Modalità anteprima e undo\n"
            "• Interfaccia moderna con drag & drop\n\n"
            "Sviluppato con PyQt6 e Python 3.10+"
        )
    
    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione."""
        # Cancella eventuali operazioni in corso
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Conferma Chiusura", 
                "Un'operazione è in corso. Vuoi cancellarla e uscire?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_worker.cancel()
                self.current_worker.wait(3000)
            else:
                event.ignore()
                return
        
        # Salva le impostazioni
        self.save_settings()
        event.accept()


def main():
    """Funzione principale della GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("File Organizer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("FileOrganizer")
    
    # Configura l'applicazione per supportare i temi
    app.setStyle("Fusion")
    
    window = FileOrganizerGUI()
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())