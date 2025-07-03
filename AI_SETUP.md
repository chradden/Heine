# 🤖 AI-Integration Setup

## OpenAI API Einrichtung

### 1. OpenAI API Key erhalten
1. Gehe zu [OpenAI Platform](https://platform.openai.com/)
2. Erstelle ein Konto oder melde dich an
3. Gehe zu "API Keys" im Dashboard
4. Erstelle einen neuen API Key
5. Kopiere den Key (er beginnt mit `sk-`)

### 2. API Key konfigurieren

**Option A: Umgebungsvariable setzen**
```powershell
# PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Oder permanent in Windows
setx OPENAI_API_KEY "sk-your-api-key-here"
```

**Option B: In der Datei konfigurieren**
Bearbeite `ai_chat_server.py` und ändere diese Zeile:
```python
OPENAI_API_KEY = "sk-your-api-key-here"  # Dein echter API Key
```

### 3. AI-Server starten
```powershell
py -3.12 ai_chat_server.py
```

### 4. Dashboard starten
```powershell
py -3.12 -m streamlit run streamlit_dashboard.py --server.port 8501
```

## Features der AI-Integration

### 🧠 Echte KI-Antworten
- **OpenAI GPT-3.5-turbo** für natürliche Konversationen
- **Marken-spezifische Prompts** für Heine und Test-Brand
- **Konversationsgedächtnis** pro Session

### 🚨 Intelligente Eskalation
- **Automatische Erkennung** von Beschwerden und emotionalen Nachrichten
- **Schlüsselwort-basierte Eskalation** (beschwerde, unzufrieden, etc.)
- **Vertrauensbewertung** für Antwortqualität

### 📊 Erweiterte Metriken
- **Antwortzeiten** in Echtzeit
- **Vertrauenswerte** pro Antwort
- **Eskalationsraten** und -gründe
- **Session-Management** mit Historie

### 🌍 Mehrsprachiger Support
- **Deutsch** als Standardsprache
- **Englisch** automatisch erkannt
- **Marken-spezifische** Kommunikationsstile

## Test-Beispiele

### Heine Brand
```
"Guten Tag, ich habe eine Frage zu meiner Bestellung #12345"
"Wo kann ich Ihre Produkte kaufen?"
"Wie lange dauert die Lieferung?"
```

### Test Brand
```
"Hello, this is a test message"
"Can you help me with a question?"
```

### Eskalation Trigger
```
"Ich bin sehr unzufrieden mit dem Service"
"I want to speak to a manager immediately"
"Das ist eine Beschwerde über die Qualität"
```

## Nächste Schritte

1. **RAG-Integration**: Echte Heine-Dokumente einbinden
2. **E-Mail-Integration**: Automatische E-Mail-Verarbeitung
3. **Analytics**: Detaillierte Berichte und Metriken
4. **Multi-Tenant**: Erweiterte Mandanten-Features

## Troubleshooting

### API Key Fehler
- Prüfe ob der API Key korrekt gesetzt ist
- Stelle sicher, dass das OpenAI-Konto Guthaben hat
- Teste den Key in der OpenAI Playground

### Verbindungsfehler
- Prüfe ob der AI-Server läuft (Port 8001)
- Stelle sicher, dass keine Firewall den Port blockiert
- Teste die API direkt: http://127.0.0.1:8001/health

### Langsame Antworten
- Das ist normal bei der ersten Anfrage (Cold Start)
- Antwortzeiten verbessern sich bei häufiger Nutzung
- Für Produktion: Caching und Optimierungen implementieren 