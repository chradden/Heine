# Makefile für das Heine KI-Kundenkommunikationssystem

.PHONY: help install test run docker-build docker-run docker-stop clean

# Standardziel
help:
	@echo "Verfügbare Befehle:"
	@echo "  install      - Abhängigkeiten installieren"
	@echo "  test         - Tests ausführen"
	@echo "  run          - Entwicklungsserver starten"
	@echo "  docker-build - Docker-Image erstellen"
	@echo "  docker-run   - Docker-Container starten"
	@echo "  docker-stop  - Docker-Container stoppen"
	@echo "  clean        - Cache und temporäre Dateien löschen"
	@echo "  example      - Beispiel-Skript ausführen"

# Abhängigkeiten installieren
install:
	pip install -r requirements.txt

# Tests ausführen
test:
	pytest tests/ -v --cov=src --cov-report=html

# Entwicklungsserver starten
run:
	uvicorn src.channels.chat_interface:app --host 0.0.0.0 --port 8000 --reload

# Docker-Image erstellen
docker-build:
	docker build -t heine-ai-system .

# Docker-Container starten
docker-run:
	docker-compose up -d

# Docker-Container stoppen
docker-stop:
	docker-compose down

# Docker-Container mit Produktions-Services starten
docker-run-prod:
	docker-compose --profile production up -d

# Cache und temporäre Dateien löschen
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Beispiel-Skript ausführen
example:
	python examples/basic_usage.py

# Dokumenten ingestieren
ingest:
	python -c "import asyncio; from src.knowledge.ingest import ingest_documents; asyncio.run(ingest_documents('heine', ['data/documents/'], 500, 50))"

# Logs anzeigen
logs:
	docker-compose logs -f heine-ai

# Shell im Container öffnen
shell:
	docker-compose exec heine-ai bash

# Health-Check
health:
	curl -f http://localhost:8000/api/v1/health

# API-Dokumentation öffnen
docs:
	open http://localhost:8000/docs

# Linting
lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

# Formatierung
format:
	black src/ tests/
	isort src/ tests/

# Sicherheits-Check
security:
	bandit -r src/
	safety check

# Vollständiger Check
check: lint test security
	@echo "Alle Checks abgeschlossen!"

# Entwicklungssetup
dev-setup: install
	@echo "Entwicklungsumgebung eingerichtet!"
	@echo "Führen Sie 'make run' aus, um den Server zu starten." 