# File Organizer - Organizzatore File Aziendali

Un tool Python multipiattaforma per organizzare automaticamente i file aziendali utilizzando matching fuzzy e intelligenza artificiale per il riconoscimento dei nomi delle aziende.

## 🚀 Caratteristiche Principali

- **Interfaccia Doppia**: CLI per automazione e GUI moderna per uso interattivo
- **Matching Fuzzy Intelligente**: Riconoscimento robusto dei nomi aziendali con normalizzazione avanzata
- **Sistema di Configurazione Avanzato**: Regole specifiche per azienda con configurazione YAML centralizzata
- **Filtraggio Intelligente**: Eliminazione automatica di parole generiche e falsi positivi
- **Priorità Contestuale**: Bonus per match nel nome file, penalità per match solo nel percorso
- **Organizzazione Automatica**: Struttura gerarchica Azienda → Tipo File → Anno → Data
- **Sistema di Undo**: Ripristino completo delle operazioni con log CSV
- **Multipiattaforma**: Windows, macOS, Linux con eseguibili standalone
- **Interfaccia Moderna**: Tema scuro/chiaro, drag & drop, operazioni asincrone

## 📋 Requisiti

- Python 3.10 o superiore
- PyQt6 per l'interfaccia grafica
- Dipendenze automaticamente installate da `requirements.txt`

## 🛠️ Installazione

### Opzione 1: Eseguibile Precompilato (Raccomandato)

1. Scarica l'eseguibile per il tuo sistema operativo dalla sezione Releases
2. Esegui direttamente il file:
   - **Windows**: `FileOrganizer.exe`
   - **macOS/Linux**: `./FileOrganizer`

### Opzione 2: Da Codice Sorgente

```bash
# Clona o scarica il repository
git clone <repository-url>
cd file-organizer

# Installa le dipendenze
pip install -r requirements.txt

# Esegui l'applicazione
python main.py          # Avvia GUI
python main.py --help   # Mostra opzioni CLI
```

### Opzione 3: Build Personalizzata

```bash
# Windows
build.bat

# macOS/Linux
./build.sh
```

## 🖥️ Utilizzo

### Interfaccia Grafica (GUI)

Avvia l'applicazione senza parametri per aprire l'interfaccia grafica:

```bash
python main.py
# oppure
python main.py gui
```

**Funzionalità GUI:**
- **Selezione Cartella**: Drag & drop o selezione manuale
- **Gestione Aziende**: Aggiungi profili con alias personalizzati
- **Parametri Avanzati**: Soglia fuzzy, filtri data, estensioni
- **Anteprima**: Modalità dry-run per vedere i risultati prima dell'organizzazione
- **Monitoraggio**: Barra di progresso e log in tempo reale
- **Undo**: Ripristino rapido delle operazioni

### Interfaccia a Riga di Comando (CLI)

```bash
# Organizzazione base
python main.py organize /path/to/files --company "ACME Corporation"

# Con parametri avanzati
python main.py organize /path/to/files \
    --company "ACME Corp" \
    --aliases "acme,acme spa" \
    --threshold 85 \
    --since 2024-01-01 \
    --until 2024-12-31 \
    --include-ext pdf,docx,xlsx \
    --dry-run

# Undo operazioni
python main.py undo operations_log.csv

# Gestione profili aziendali
python main.py list-companies
python main.py add-company "Beta Solutions" --aliases "beta,beta sol"
python main.py remove-company "Old Company"
```

### Parametri CLI Completi

```
organize:
  source_dir              Cartella sorgente da organizzare
  --company              Nome azienda principale
  --aliases              Alias separati da virgola
  --target-dir           Cartella destinazione (default: source_dir/organized)
  --threshold            Soglia fuzzy matching (default: 85)
  --since                Data inizio filtro (YYYY-MM-DD)
  --until                Data fine filtro (YYYY-MM-DD)
  --include-ext          Estensioni da includere (es: pdf,docx)
  --exclude-ext          Estensioni da escludere
  --exclude-dirs         Directory da escludere
  --dry-run              Solo anteprima, non sposta file
  --log-file             File di log personalizzato

undo:
  log_file               File CSV con log delle operazioni

list-companies:          Mostra profili aziendali salvati
add-company:             Aggiungi nuovo profilo aziendale
remove-company:          Rimuovi profilo aziendale
```

## 📁 Struttura di Organizzazione

I file vengono organizzati nella seguente gerarchia:

```
Cartella_Destinazione/
├── ACME Corporation/
│   ├── PDF/
│   │   ├── 2024/
│   │   │   ├── 2024-03-15_fattura_acme.pdf
│   │   │   └── 2024-03-20_contratto_acme.pdf
│   │   └── 2023/
│   ├── Word/
│   │   └── 2024/
│   │       └── 2024-03-10_proposta_acme.docx
│   ├── Excel/
│   ├── Immagini/
│   └── Altro/
└── Beta Solutions/
    └── PDF/
        └── 2024/
```

## 🔧 Configurazione

### File di Configurazione

L'applicazione utilizza due file di configurazione principali:

#### 1. Configurazione Generale (`config.yaml`)

```yaml
app_settings:
  default_fuzzy_threshold: 92  # Soglia più restrittiva
  default_target_suffix: "_organized"
  auto_create_date_folders: true
  log_operations: true
  theme: "dark"

company_profiles:
  - name: "ACME Corporation"
    aliases: ["acme", "acme corp", "acme spa"]
    fuzzy_threshold: 92
    custom_folders: {}
```

#### 2. Configurazione Aziende Avanzata (`companies_config.yaml`)

```yaml
companies:
  "Area Finanza Spa":
    aliases:
      - "Area Finanza"
      - "AreaFinanza"
      - "Area Finanza S.p.A."
      - "Area Finanza SpA"
    required_keywords:
      - "finanza"
    excluded_standalone:
      - "area"
      - "spa"
      - "s.p.a"
    
  "Alcotec S.p.A":
    aliases:
      - "Alcotec"
      - "Alcotec SpA"
    required_keywords:
      - "alcotec"
    excluded_standalone:
      - "spa"
      - "s.p.a"

# Parole generiche filtrate automaticamente
generic_words:
  - "area"
  - "zone"
  - "config"
  - "test"
  - "document"
  - "file"
  - "data"
  - "temp"
  - "backup"

# Impostazioni matching avanzato
matching_settings:
  filename_bonus: 15      # Bonus % per match nel nome file
  path_only_penalty: -10  # Penalità % per match solo nel percorso
  min_threshold: 92       # Soglia minima matching
```

### Personalizzazione Tipi File

Modifica `types.py` per aggiungere nuove categorie o estensioni:

```python
# Aggiungi nuove estensioni
EXTENSION_MAPPING = {
    # Esistenti...
    '.dwg': FileCategory.OTHER,  # File CAD
    '.psd': FileCategory.IMAGES, # Photoshop
}
```

## 🧪 Test

Esegui la suite di test completa:

```bash
# Installa pytest se non presente
pip install pytest pytest-qt

# Esegui tutti i test
python -m pytest test_organizer.py -v

# Test specifici
python -m pytest test_organizer.py::TestCompanyMatcher -v
```

## 📊 Sistema di Logging

Ogni operazione viene registrata in un file CSV con le seguenti colonne:

- `timestamp`: Data e ora dell'operazione
- `action`: Tipo di operazione (move, copy, create_dir)
- `original_path`: Percorso originale del file
- `new_path`: Nuovo percorso del file
- `company`: Azienda riconosciuta
- `category`: Categoria del file
- `score`: Punteggio del matching fuzzy

### Esempio Log CSV

```csv
timestamp,action,original_path,new_path,company,category,score
2024-03-15 10:30:15,move,/docs/fattura_acme.pdf,/organized/ACME Corp/PDF/2024/2024-03-15_fattura_acme.pdf,ACME Corp,PDF,95.5
```

## 🎨 Personalizzazione Interfaccia

### Temi

L'applicazione supporta temi scuro e chiaro. Modifica `assets/style.qss` per personalizzare:

```css
/* Tema personalizzato */
QMainWindow {
    background-color: #your-color;
    color: #your-text-color;
}
```

### Icone

Aggiungi icone personalizzate nella cartella `assets/` e aggiorna i riferimenti in `gui.py`.

## 🚨 Risoluzione Problemi

### Problemi Comuni

1. **"ModuleNotFoundError: No module named 'PyQt6'"**
   ```bash
   pip install PyQt6
   ```

2. **"Permission denied" durante lo spostamento file**
   - Verifica i permessi della cartella destinazione
   - Chiudi file aperti in altre applicazioni

3. **Matching fuzzy non accurato**
   - Riduci la soglia fuzzy (es: da 85 a 75)
   - Aggiungi più alias per l'azienda
   - Verifica la normalizzazione in `normalize.py`

4. **GUI non si avvia**
   - Verifica installazione PyQt6: `python -c "import PyQt6"`
   - Su Linux: installa `python3-pyqt6` dal package manager

### Debug

Abilita logging dettagliato:

```bash
python main.py --debug organize /path/to/files --company "Test"
```

## 🤝 Contributi

1. Fork del repository
2. Crea branch per la feature: `git checkout -b feature/nuova-funzionalita`
3. Commit delle modifiche: `git commit -am 'Aggiungi nuova funzionalità'`
4. Push del branch: `git push origin feature/nuova-funzionalita`
5. Crea Pull Request

### Linee Guida per Contributi

- Segui lo stile di codice esistente
- Aggiungi test per nuove funzionalità
- Aggiorna la documentazione
- Testa su multiple piattaforme quando possibile

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🙏 Ringraziamenti

- **PyQt6**: Framework per l'interfaccia grafica
- **rapidfuzz**: Libreria per matching fuzzy veloce
- **PyInstaller**: Tool per la creazione di eseguibili
- **pytest**: Framework per i test

## 📞 Supporto

Per bug, richieste di funzionalità o domande:

1. Controlla la sezione [Issues](../../issues) per problemi simili
2. Crea un nuovo Issue con:
   - Descrizione dettagliata del problema
   - Passi per riprodurre
   - Sistema operativo e versione Python
   - Log di errore (se disponibile)

## 🔄 Changelog

### v1.1.0 (2025-01-22) - Matching Avanzato
- **🔧 Sistema di Configurazione Centralizzato**: Nuovo file `companies_config.yaml` per regole specifiche
- **🎯 Matching Più Preciso**: Soglia aumentata da 85% a 92% per ridurre falsi positivi
- **🚫 Filtraggio Parole Generiche**: Eliminazione automatica di parole come "area", "zone", "config"
- **📁 Priorità Contestuale**: Bonus +15% per match nel nome file, penalità -10% per match solo nel percorso
- **⚙️ Regole Specifiche per Azienda**: Parole chiave richieste e parole escluse standalone
- **🧪 Suite di Test Avanzata**: Nuovi test per verificare correzioni e precisione matching
- **📋 Gestione Configurazione**: Classe `CompanyConfig` per caricamento e validazione automatica

### v1.0.0 (2024-03-15)
- Rilascio iniziale
- Interfaccia GUI completa con PyQt6
- CLI con argparse
- Sistema di matching fuzzy
- Organizzazione automatica file
- Sistema di undo con logging CSV
- Build multipiattaforma con PyInstaller
- Suite di test completa

---

**Sviluppato con ❤️ per semplificare l'organizzazione dei documenti aziendali**#
