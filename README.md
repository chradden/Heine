# KI-Kundenkommunikationssystem für Heine (Mehrmandantenfähig)

## Überblick

Dieses System bietet eine **KI-gestützte Kundenkommunikation** für die Heinrich Heine GmbH mit **Multi-Mandanten-Architektur**. Ein zentraler KI-Agent beantwortet Kundenanfragen automatisiert über Chat, E-Mail und (perspektivisch) Telefonie – jeweils unter Berücksichtigung des Marken-Kontexts.

## Kernfunktionen

- **Multi-Mandanten-Architektur**: Mandantentrennung für mehrere Marken
- **KI-gestützter Agent**: Antwortet basierend auf Wissensdatenbank und Kundendaten
- **Omnichannel-Anbindung**: Chat, E-Mail und Telefonie (Architektur-Platzhalter)
- **Eskalationslogik**: Automatische Übergabe an menschliche Mitarbeiter
- **DSGVO-konformes Logging**: Protokollierung unter Einhaltung europäischer Datenschutzrichtlinien

## Technische Architektur

- **Backend**: Python mit LangChain für LLM-gestützte KI-Agenten
- **Wissensdatenbank**: Vector Store (ChromaDB/FAISS) mit RAG-Ansatz
- **API-Integration**: REST-API für Kunden- und Versanddaten
- **Kommunikationskanäle**: WebSocket für Chat, SMTP für E-Mail
- **Datenschutz**: Anonymisierung, Löschkonzepte, DSGVO-Konformität

## Installation

### Voraussetzungen

- Python 3.10+
- Git
- Docker (optional, für Container-Deployment)

### Setup

1. **Repository klonen**:
```bash
git clone <repository-url>
cd heine-ai-support
```

2. **Virtuelle Umgebung erstellen**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. **Abhängigkeiten installieren**:
```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren**:
```bash
cp .env.example .env
# Bearbeiten Sie .env mit Ihren API-Schlüsseln und Konfigurationen
```

## Installation

### Voraussetzungen

- Python 3.11 oder höher
- OpenAI API-Schlüssel
- Mindestens 4GB RAM
- 2GB freier Speicherplatz

### Installation

1. Repository klonen:
```bash
git clone <repository-url>
cd heine-ai-system
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

**Hinweis für Windows-Benutzer:** Das System verwendet ChromaDB mit HNSWLib als Vector Store Backend, da FAISS unter Windows schwer installierbar ist. Alle Funktionalitäten bleiben vollständig erhalten.

## Konfiguration

### Umgebungsvariablen (.env)

```env
# LLM-Konfiguration
OPENAI_API_KEY=your_openai_api_key
# oder für lokale Modelle:
LOCAL_MODEL_PATH=/path/to/local/model

# Mandanten-Konfiguration
BRANDS=heine,subbrand1,subbrand2
DEFAULT_BRAND=heine

# Vector Store
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=./data/vector_store

# API-Konfiguration
CUSTOMER_API_URL=http://localhost:8001/api
CUSTOMER_API_KEY=your_api_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/heine_ai.log

# Datenschutz
DATA_RETENTION_DAYS=30
ANONYMIZE_LOGS=true
```

### Mandanten-Konfiguration

Jeder Mandant benötigt eine Konfigurationsdatei in `config/brands/`:

```yaml
# config/brands/heine.yaml
name: "Heine"
description: "Hauptmarke Heine"
knowledge_base_path: "./data/knowledge/heine"
api_endpoint: "https://api.heine.com"
escalation_threshold: 0.7
support_email: "support@heine.com"
```

## Verwendung

### Entwicklungsserver starten

```bash
# Chat-Interface (Streamlit)
python src/main.py --mode chat

# E-Mail-Interface
python src/main.py --mode email

# Demo-Modus (Konsolen-Interface)
python src/main.py --mode demo

# API-Server
python src/main.py --mode api
```

### Wissensdatenbank aktualisieren

```bash
# Neue Dokumente hinzufügen
python src/knowledge/ingest.py --brand heine --path ./new_documents/

# Wissensdatenbank neu aufbauen
python src/knowledge/ingest.py --brand heine --rebuild
```

### Tests ausführen

```bash
# Alle Tests
pytest

# Spezifische Tests
pytest tests/test_agent.py
pytest tests/test_privacy.py
```

## Deployment

### Docker

```bash
# Image bauen
docker build -t heine-ai-support .

# Container starten
docker run -p 8501:8501 -p 8000:8000 heine-ai-support
```

### Lokaler Server

```bash
# Mit uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Mit Streamlit
streamlit run src/main.py
```

## API-Dokumentation

### Chat-Endpunkt

```http
POST /api/v1/chat
Content-Type: application/json

{
  "brand": "heine",
  "message": "Wo ist meine Bestellung?",
  "session_id": "user123",
  "customer_id": "cust456"
}
```

### E-Mail-Verarbeitung

```http
POST /api/v1/email/process
Content-Type: application/json

{
  "brand": "heine",
  "email_content": "Sehr geehrtes Team, ...",
  "from_email": "customer@example.com",
  "subject": "Frage zu Bestellung"
}
```

## Mandanten-Management

### Neuen Mandanten hinzufügen

1. Konfigurationsdatei erstellen: `config/brands/neue_marke.yaml`
2. Wissensdatenbank vorbereiten: `data/knowledge/neue_marke/`
3. API-Endpunkte konfigurieren
4. System neu starten

### Mandanten-Isolation

- Jeder Mandant hat eigene Wissensdatenbank
- API-Zugriffe sind mandantenspezifisch
- Logs werden pro Mandant getrennt
- Eskalationsregeln sind mandantenabhängig

## Datenschutz

### DSGVO-Konformität

- **Anonymisierung**: Personenbezogene Daten werden in Logs anonymisiert
- **Löschung**: Automatische Löschung nach konfigurierbarer Zeit
- **Einwilligung**: Transparente Information über Datenverarbeitung
- **Betroffenenrechte**: Auskunft, Berichtigung, Löschung

### Datensicherheit

- Verschlüsselte Kommunikation (HTTPS)
- Sichere API-Schlüssel-Verwaltung
- Zugriffskontrolle auf Datenbanken
- Regelmäßige Sicherheitsaudits

## Monitoring und Logging

### Logs

- Anwendungslogs: `logs/heine_ai.log`
- Chat-Verläufe: `logs/conversations/`
- Fehlerlogs: `logs/errors/`

### Metriken

- Antwortzeiten
- Eskalationsrate
- Kundenzufriedenheit
- System-Performance

## Troubleshooting

### Häufige Probleme

1. **LLM-API nicht erreichbar**
   - API-Schlüssel prüfen
   - Netzwerkverbindung testen
   - Rate Limits beachten

2. **Wissensdatenbank nicht gefunden**
   - Pfade in Konfiguration prüfen
   - `ingest.py` ausführen
   - Berechtigungen kontrollieren

3. **Mandanten-Isolation funktioniert nicht**
   - Konfigurationsdateien prüfen
   - Vector Store neu initialisieren
   - Logs auf Datenlecks untersuchen

## Support

Bei Fragen oder Problemen:

1. Dokumentation prüfen
2. Logs analysieren
3. Tests ausführen
4. Issue im Repository erstellen

## Lizenz

Proprietär - Heinrich Heine GmbH

## Changelog

### v1.0.0 (2024-01-XX)
- Initiale Version
- Multi-Mandanten-Architektur
- Chat- und E-Mail-Integration
- DSGVO-konformes Logging
- Eskalationslogik 