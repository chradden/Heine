# 🤖 Heine AI-Kundenkommunikationssystem

## 📋 Projektübersicht

Das **Heine AI-Kundenkommunikationssystem** ist ein mehrmandantenfähiges KI-System für die Heinrich Heine GmbH, das automatische Kundenkommunikation über Chat, E-Mail und Telefon (Platzhalter) ermöglicht. Das System nutzt moderne AI-Technologien wie OpenAI GPT und LangChain für natürliche Konversationen.

### 🎯 Projektziele
- **Automatisierte Kundenkommunikation** über multiple Kanäle
- **Mehrmandantenfähigkeit** für verschiedene Marken/Tochtergesellschaften
- **Intelligente Eskalation** komplexer Anfragen an menschliche Mitarbeiter
- **DSGVO-konforme** Datenverarbeitung und -speicherung
- **Skalierbare Architektur** für wachsende Anforderungen

---

## 🏗️ Systemarchitektur

### 📁 Verzeichnisstruktur
```
heine-ai-system/
├── src/                          # Hauptquellcode
│   ├── agents/                   # AI-Agenten und Logik
│   ├── api/                      # REST-API Endpunkte
│   ├── channels/                 # Kommunikationskanäle
│   ├── knowledge/                # Wissensdatenbank und RAG
│   ├── models/                   # Datenmodelle
│   └── utils/                    # Hilfsfunktionen
├── config/                       # Konfigurationsdateien
│   └── brands/                   # Mandanten-Konfigurationen
├── data/                         # Datenverzeichnis
│   ├── knowledge/                # Wissensdatenbank-Dateien
│   └── vector_store/             # Vektor-Datenbank
├── logs/                         # Log-Dateien
├── tests/                        # Test-Suite
├── docs/                         # Dokumentation
├── examples/                     # Beispielskripte
├── requirements.txt              # Python-Abhängigkeiten
├── Dockerfile                    # Docker-Konfiguration
├── docker-compose.yml           # Multi-Container Setup
├── Makefile                     # Build-Automation
└── README.md                    # Projekt-Übersicht
```

### 🔧 Technologie-Stack
- **Backend:** Python 3.12, FastAPI, LangChain
- **AI/ML:** OpenAI GPT-3.5-turbo, ChromaDB (HNSWLib)
- **Frontend:** Streamlit, React (geplant)
- **Datenbank:** ChromaDB (Vektor), SQLite (Metadaten)
- **Deployment:** Docker, Docker Compose
- **Monitoring:** Prometheus, Structlog

---

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.11 oder höher
- OpenAI API-Schlüssel
- Mindestens 4GB RAM
- 2GB freier Speicherplatz

### Schnellstart (Windows)

1. **Repository klonen**
```bash
git clone <repository-url>
cd heine-ai-system
```

2. **Virtuelle Umgebung erstellen**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Abhängigkeiten installieren**
```bash
pip install -r requirements.txt
```

4. **OpenAI API Key konfigurieren**
```bash
# PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

5. **AI-Server starten**
```bash
py -3.12 ai_chat_server.py
```

6. **Dashboard starten**
```bash
py -3.12 -m streamlit run streamlit_dashboard.py --server.port 8501
```

### Docker Setup (Empfohlen für Produktion)
```bash
docker-compose up -d
```

---

## 🧠 AI-Integration

### OpenAI Konfiguration
Das System nutzt OpenAI GPT-3.5-turbo für natürliche Konversationen:

```python
# Konfiguration in ai_chat_server.py
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-3.5-turbo"
TEMPERATURE = 0.7
```

### Marken-spezifische Prompts
Jede Marke hat eigene Kommunikationsrichtlinien:

- **Heine:** Professioneller Kundenservice mit Fokus auf Qualität
- **Test-Brand:** Einfache Test-Umgebung für Entwicklung

### Intelligente Eskalation
Automatische Erkennung von:
- Beschwerden und emotionalen Nachrichten
- Schlüsselwörtern (beschwerde, unzufrieden, manager)
- Technischen Problemen

---

## 📊 Features & Funktionalitäten

### 🤖 Chat-Interface
- **Echtzeit-Konversationen** mit AI-Agenten
- **Session-Management** mit Konversationshistorie
- **Marken-spezifische** Kommunikationsstile
- **Mehrsprachiger Support** (DE/EN)

### 📧 E-Mail-Integration
- **Automatische E-Mail-Verarbeitung**
- **Intelligente Antwortgenerierung**
- **Eskalationslogik** für komplexe Anfragen
- **DSGVO-konforme** Datenverarbeitung

### 📞 Telefon-Integration (Platzhalter)
- **Sprach-zu-Text Konvertierung**
- **Text-zu-Sprache Antworten**
- **Integration mit Telefonie-Systemen**

### 🔍 RAG (Retrieval-Augmented Generation)
- **Vektor-basierte Dokumentensuche**
- **ChromaDB mit HNSWLib Backend**
- **Automatische Dokumenten-Ingestion**
- **Kontext-basierte Antworten**

---

## 🔧 Konfiguration

### System-Konfiguration
```yaml
# config/system.yaml
openai_api_key: "sk-..."
model_name: "gpt-3.5-turbo"
temperature: 0.7
vector_store_type: "chromadb"
log_level: "INFO"
```

### Mandanten-Konfiguration
```yaml
# config/brands/heine.yaml
name: "Heine"
description: "Hauptmarke Heine"
knowledge_base_path: "./data/knowledge/heine"
api_endpoint: "https://api.heine.com"
escalation_threshold: 0.7
support_email: "support@heine.com"
```

### Umgebungsvariablen
```bash
OPENAI_API_KEY=sk-your-api-key
MODEL_NAME=gpt-3.5-turbo
VECTOR_STORE_PATH=./data/vector_store
LOG_LEVEL=INFO
```

---

## 📈 Monitoring & Analytics

### Metriken
- **Antwortzeiten** pro Anfrage
- **Vertrauenswerte** der AI-Antworten
- **Eskalationsraten** und -gründe
- **Kundenzufriedenheit** (geplant)

### Logging
- **Strukturiertes Logging** mit Structlog
- **DSGVO-konforme** Anonymisierung
- **Automatische Rotation** und Archivierung
- **Prometheus-Metriken** für Monitoring

### Health Checks
- **API-Status** Überwachung
- **Datenbank-Verbindungen**
- **AI-Model-Verfügbarkeit**
- **System-Ressourcen**

---

## 🔒 Sicherheit & Datenschutz

### DSGVO-Konformität
- **Anonymisierung** personenbezogener Daten
- **Automatische Löschung** nach konfigurierbarer Zeit
- **Transparente Datenverarbeitung**
- **Betroffenenrechte** (Auskunft, Berichtigung, Löschung)

### Datensicherheit
- **Verschlüsselte Kommunikation** (HTTPS)
- **Sichere API-Schlüssel-Verwaltung**
- **Zugriffskontrolle** auf Datenbanken
- **Regelmäßige Sicherheitsaudits**

### Backup & Recovery
- **Automatische Backups** der Vektor-Datenbank
- **Konfigurations-Backups**
- **Disaster Recovery** Pläne
- **Point-in-Time Recovery**

---

## 🧪 Testing

### Test-Suite
```bash
# Alle Tests ausführen
pytest

# Spezifische Tests
pytest tests/test_agents.py
pytest tests/test_api.py
pytest tests/test_privacy.py
```

### Test-Coverage
- **Unit Tests** für alle Module
- **Integration Tests** für API-Endpunkte
- **End-to-End Tests** für Chat-Flows
- **Performance Tests** für Skalierbarkeit

---

## 🚀 Deployment

### Entwicklung
```bash
# Lokaler Server
py -3.12 ai_chat_server.py
py -3.12 -m streamlit run streamlit_dashboard.py
```

### Staging
```bash
# Docker Compose
docker-compose -f docker-compose.staging.yml up -d
```

### Produktion
```bash
# Kubernetes (geplant)
kubectl apply -f k8s/

# Docker Swarm
docker stack deploy -c docker-compose.prod.yml heine-ai
```

---

## 📚 API-Dokumentation

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

### Health Check
```http
GET /api/v1/health
```

### Session-Management
```http
GET /api/v1/sessions/{session_id}/history
DELETE /api/v1/sessions/{session_id}
```

### Vollständige API-Dokumentation
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

---

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: docker-compose up -d
```

---

## 📞 Support & Wartung

### Troubleshooting

#### Häufige Probleme
1. **OpenAI API nicht erreichbar**
   - API-Schlüssel prüfen
   - Netzwerkverbindung testen
   - Rate Limits beachten

2. **ChromaDB-Fehler unter Windows**
   - HNSWLib Backend verwenden
   - Docker-Container für ChromaDB
   - Alternative Vector Stores prüfen

3. **Port-Konflikte**
   - Andere Ports verwenden
   - Laufende Services beenden
   - Firewall-Einstellungen prüfen

### Wartung
- **Regelmäßige Updates** der AI-Modelle
- **Backup-Verifizierung** der Datenbanken
- **Performance-Monitoring** und Optimierung
- **Sicherheits-Patches** und Updates

---

## 🔮 Roadmap

### Version 2.0 (Q3 2025)
- [ ] **RAG-Integration** mit echten Heine-Dokumenten
- [ ] **E-Mail-Integration** vollständig implementieren
- [ ] **React Frontend** für professionelle Nutzung
- [ ] **Multi-Language Support** erweitern

### Version 3.0 (Q4 2025)
- [ ] **Telefon-Integration** mit Spracherkennung
- [ ] **Advanced Analytics** Dashboard
- [ ] **Machine Learning** für Eskalationsvorhersage
- [ ] **Mobile App** für Support-Teams

### Version 4.0 (Q1 2026)
- [ ] **Multi-Tenant** erweiterte Features
- [ ] **Advanced RAG** mit Hybrid-Suche
- [ ] **Real-time Collaboration** zwischen AI und Menschen
- [ ] **Predictive Analytics** für Kundenverhalten

---

## 👥 Team & Kontakt

### Projektteam
- **Projektleiter:** [Name]
- **AI-Entwicklung:** [Name]
- **Backend-Entwicklung:** [Name]
- **Frontend-Entwicklung:** [Name]
- **DevOps:** [Name]

### Kontakt
- **E-Mail:** ai-support@heine.com
- **Jira:** [Projekt-Link]
- **Slack:** #heine-ai-project

---

## 📄 Lizenz

**Proprietär - Heinrich Heine GmbH**

Alle Rechte vorbehalten. Dieses System ist das geistige Eigentum der Heinrich Heine GmbH und darf ohne ausdrückliche Genehmigung nicht weitergegeben oder verwendet werden.

---

*Dokumentation erstellt: [Datum]*  
*Letzte Aktualisierung: [Datum]*  
*Version: 1.0.0* 