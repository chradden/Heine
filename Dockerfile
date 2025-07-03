# Dockerfile für das Heine KI-Kundenkommunikationssystem
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Verzeichnisse für Daten erstellen
RUN mkdir -p /app/data/logs \
    /app/data/escalation_tickets \
    /app/data/vector_store \
    /app/data/documents

# Umgebungsvariablen setzen
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Ports exponieren
EXPOSE 8000

# Health-Check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Standard-Befehl
CMD ["python", "-m", "uvicorn", "src.channels.chat_interface:app", "--host", "0.0.0.0", "--port", "8000"] 