# 🔧 Entwickler-Dokumentation - Heine AI-System

## 📋 Übersicht

Diese Dokumentation richtet sich an Entwickler und DevOps-Teams, die am Heine AI-Kundenkommunikationssystem arbeiten. Sie enthält technische Details, Architektur-Entscheidungen und Entwicklungsrichtlinien.

---

## 🏗️ Architektur-Details

### System-Komponenten

#### 1. AI-Agenten (`src/agents/`)
```python
# Hauptagent für Kundenkommunikation
class CustomerServiceAgent:
    def __init__(self, brand_config: BrandConfig):
        self.llm = OpenAI(model_name="gpt-3.5-turbo")
        self.memory = ConversationBufferMemory()
        self.vector_store = ChromaDB()
    
    async def process_message(self, message: str, session_id: str) -> Response:
        # RAG-basierte Antwortgenerierung
        context = self.vector_store.similarity_search(message)
        response = await self.llm.agenerate(
            messages=[{"role": "user", "content": f"Context: {context}\nMessage: {message}"}]
        )
        return Response(content=response.content)
```

#### 2. Kommunikationskanäle (`src/channels/`)
- **Chat:** WebSocket-basierte Echtzeit-Kommunikation
- **E-Mail:** SMTP/IMAP Integration mit automatischer Verarbeitung
- **Telefon:** Platzhalter für zukünftige Spracherkennung

#### 3. Wissensdatenbank (`src/knowledge/`)
```python
# RAG-Implementation mit ChromaDB
class KnowledgeBase:
    def __init__(self, brand: str):
        self.vector_store = ChromaDB(
            persist_directory=f"./data/vector_store/{brand}",
            embedding_function=HNSWLibEmbedding()
        )
    
    def add_document(self, content: str, metadata: dict):
        # Dokumenten-Ingestion mit Embeddings
        embeddings = self.embedding_function.embed_query(content)
        self.vector_store.add_texts([content], metadatas=[metadata])
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        # Ähnlichkeitssuche
        return self.vector_store.similarity_search(query, k=k)
```

---

## 🔧 Entwicklungsumgebung Setup

### Lokale Entwicklung

1. **Python-Umgebung**
```bash
# Python 3.12 installieren
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Abhängigkeiten installieren
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Entwicklungsabhängigkeiten
```

2. **Pre-commit Hooks**
```bash
# Pre-commit installieren
pip install pre-commit
pre-commit install

# Hooks konfigurieren
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

3. **IDE-Konfiguration**
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

---

## 📝 Coding Standards

### Python-Stil (PEP 8 + Black)

```python
# ✅ Korrekt
from typing import List, Optional, Dict
import asyncio
from dataclasses import dataclass

@dataclass
class CustomerMessage:
    """Repräsentiert eine Kunden-Nachricht."""
    
    content: str
    session_id: str
    customer_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

# ❌ Falsch
from typing import *
import asyncio, datetime
from dataclasses import dataclass

@dataclass
class CustomerMessage:
    content:str
    session_id:str
    customer_id:str=None
    timestamp:datetime=None
```

### Async/Await Patterns

```python
# ✅ Korrekt - Async/Await
async def process_customer_request(message: str) -> Response:
    try:
        # Async Operationen
        context = await get_context(message)
        response = await generate_response(context, message)
        await log_interaction(message, response)
        return response
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung: {e}")
        raise

# ❌ Falsch - Blocking Operations
def process_customer_request(message: str) -> Response:
    context = get_context(message)  # Blocking
    response = generate_response(context, message)  # Blocking
    return response
```

### Error Handling

```python
# ✅ Korrekt - Strukturiertes Error Handling
class AIProcessingError(Exception):
    """Basis-Exception für AI-Verarbeitungsfehler."""
    pass

class OpenAIError(AIProcessingError):
    """OpenAI API-spezifische Fehler."""
    pass

async def safe_ai_call(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit erreicht: {e}")
        raise OpenAIError("Rate limit erreicht") from e
    except openai.APIError as e:
        logger.error(f"OpenAI API Fehler: {e}")
        raise OpenAIError(f"API Fehler: {e}") from e
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        raise AIProcessingError(f"Verarbeitungsfehler: {e}") from e
```

---

## 🧪 Testing

### Test-Struktur

```
tests/
├── unit/                    # Unit Tests
│   ├── test_agents.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/             # Integration Tests
│   ├── test_api.py
│   ├── test_channels.py
│   └── test_knowledge.py
├── e2e/                     # End-to-End Tests
│   ├── test_chat_flow.py
│   └── test_escalation.py
└── fixtures/                # Test-Daten
    ├── sample_messages.json
    └── mock_responses.json
```

### Test-Beispiele

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import AsyncMock, patch
from src.agents.customer_service_agent import CustomerServiceAgent

class TestCustomerServiceAgent:
    @pytest.fixture
    def agent(self):
        """Agent-Fixture für Tests."""
        with patch('src.agents.customer_service_agent.OpenAI'):
            return CustomerServiceAgent(brand_config=mock_brand_config())
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, agent):
        """Test erfolgreiche Nachrichtenverarbeitung."""
        # Arrange
        message = "Wo ist meine Bestellung?"
        session_id = "test_session_123"
        
        # Mock OpenAI Response
        agent.llm.agenerate = AsyncMock(return_value=mock_response())
        
        # Act
        response = await agent.process_message(message, session_id)
        
        # Assert
        assert response.content is not None
        assert len(response.content) > 0
        agent.llm.agenerate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_escalation(self, agent):
        """Test Eskalation bei Beschwerden."""
        # Arrange
        message = "Ich bin sehr unzufrieden mit dem Service!"
        
        # Act
        response = await agent.process_message(message, "test_session")
        
        # Assert
        assert response.escalation_required is True
        assert "manager" in response.content.lower()

# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.channels.chat_interface import app

class TestChatAPI:
    @pytest.fixture
    def client(self):
        """FastAPI Test Client."""
        return TestClient(app)
    
    def test_chat_endpoint_success(self, client):
        """Test erfolgreicher Chat-Endpunkt."""
        response = client.post(
            "/api/v1/chat",
            json={
                "brand": "heine",
                "message": "Hallo, ich habe eine Frage",
                "session_id": "test_session"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
```

### Test-Ausführung

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=src --cov-report=html

# Spezifische Tests
pytest tests/unit/test_agents.py -v

# Performance Tests
pytest tests/performance/ -m "slow"

# Parallel Execution
pytest -n auto
```

---

## 🔍 Debugging & Logging

### Strukturiertes Logging

```python
# src/utils/logger.py
import structlog
from typing import Any, Dict

def setup_logging(level: str = "INFO") -> None:
    """Konfiguriert strukturiertes Logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# Verwendung
logger = structlog.get_logger()

async def process_customer_request(message: str, session_id: str):
    logger.info(
        "Kundenanfrage verarbeiten",
        session_id=session_id,
        message_length=len(message),
        brand="heine"
    )
    
    try:
        # Verarbeitung
        result = await ai_agent.process(message)
        
        logger.info(
            "Anfrage erfolgreich verarbeitet",
            session_id=session_id,
            response_length=len(result.content),
            processing_time=result.processing_time
        )
        
        return result
    except Exception as e:
        logger.error(
            "Fehler bei der Verarbeitung",
            session_id=session_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### Debug-Modus

```python
# config/debug.py
import os
from typing import Dict, Any

DEBUG_CONFIG: Dict[str, Any] = {
    "log_level": "DEBUG",
    "ai_model": "gpt-3.5-turbo",
    "vector_store": "mock",  # Mock für schnelle Tests
    "enable_profiling": True,
    "mock_external_apis": True,
}

def is_debug_mode() -> bool:
    """Prüft ob Debug-Modus aktiv ist."""
    return os.getenv("DEBUG", "false").lower() == "true"

def get_debug_config() -> Dict[str, Any]:
    """Gibt Debug-Konfiguration zurück."""
    if is_debug_mode():
        return DEBUG_CONFIG
    return {}
```

---

## 🚀 Performance & Optimierung

### Caching-Strategien

```python
# src/utils/cache.py
import asyncio
from typing import Any, Optional
import aioredis
import json

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Wert aus Cache abrufen."""
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache-Fehler: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Wert im Cache speichern."""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache-Speicherfehler: {e}")

# Verwendung in Agenten
class OptimizedCustomerServiceAgent:
    def __init__(self):
        self.cache = CacheManager()
    
    async def get_cached_response(self, query_hash: str) -> Optional[str]:
        """Cached Antwort abrufen."""
        return await self.cache.get(f"response:{query_hash}")
    
    async def process_message(self, message: str) -> Response:
        # Cache-Check
        query_hash = hashlib.md5(message.encode()).hexdigest()
        cached_response = await self.get_cached_response(query_hash)
        
        if cached_response:
            return Response(content=cached_response, cached=True)
        
        # Normale Verarbeitung
        response = await self.ai_model.generate(message)
        
        # Cache-Response
        await self.cache.set(f"response:{query_hash}", response.content)
        
        return response
```

### Async Performance

```python
# src/utils/async_utils.py
import asyncio
from typing import List, Any
import time

class AsyncPerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def measure_async_operation(self, operation_name: str, coro):
        """Misst Performance einer Async-Operation."""
        start_time = time.time()
        try:
            result = await coro
            duration = time.time() - start_time
            
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            
            self.metrics[operation_name].append(duration)
            
            logger.info(
                "Async-Operation abgeschlossen",
                operation=operation_name,
                duration=duration,
                avg_duration=sum(self.metrics[operation_name]) / len(self.metrics[operation_name])
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Async-Operation fehlgeschlagen",
                operation=operation_name,
                duration=duration,
                error=str(e)
            )
            raise

# Verwendung
monitor = AsyncPerformanceMonitor()

async def process_batch_messages(messages: List[str]):
    """Verarbeitet mehrere Nachrichten parallel."""
    tasks = []
    
    for message in messages:
        task = monitor.measure_async_operation(
            "message_processing",
            ai_agent.process_message(message)
        )
        tasks.append(task)
    
    # Parallel ausführen
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## 🔒 Sicherheit

### API-Sicherheit

```python
# src/middleware/security.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import jwt
from typing import Optional

security = HTTPBearer()

class SecurityMiddleware:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    async def verify_token(self, request: Request) -> Optional[dict]:
        """Verifiziert JWT-Token."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None
    
    async def __call__(self, request: Request, call_next):
        """Middleware für Request-Verarbeitung."""
        # Token-Verifikation
        payload = await self.verify_token(request)
        if not payload:
            raise HTTPException(status_code=401, detail="Ungültiger Token")
        
        # Request mit Payload erweitern
        request.state.user = payload
        
        response = await call_next(request)
        return response
```

### Datenverschlüsselung

```python
# src/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, key: str):
        self.key = self._derive_key(key)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Leitet Schlüssel aus Passwort ab."""
        salt = b'heine_ai_salt'  # In Produktion: zufälliger Salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Verschlüsselt Daten."""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Entschlüsselt Daten."""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

# Verwendung für sensitive Daten
encryption = DataEncryption(os.getenv("ENCRYPTION_KEY"))

def store_customer_data(customer_id: str, data: dict):
    """Speichert Kundendaten verschlüsselt."""
    encrypted_data = encryption.encrypt(json.dumps(data))
    # In Datenbank speichern
    db.store(f"customer:{customer_id}", encrypted_data)
```

---

## 📊 Monitoring & Observability

### Prometheus Metriken

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metriken definieren
REQUEST_COUNT = Counter(
    'ai_requests_total',
    'Total number of AI requests',
    ['brand', 'channel', 'status']
)

REQUEST_DURATION = Histogram(
    'ai_request_duration_seconds',
    'AI request duration in seconds',
    ['brand', 'channel']
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions',
    'Number of active chat sessions',
    ['brand']
)

ERROR_COUNT = Counter(
    'ai_errors_total',
    'Total number of AI processing errors',
    ['brand', 'error_type']
)

# Middleware für automatische Metriken
class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Metriken aktualisieren
            REQUEST_COUNT.labels(
                brand=request.path_params.get('brand', 'unknown'),
                channel='chat',
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                brand=request.path_params.get('brand', 'unknown'),
                channel='chat'
            ).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            ERROR_COUNT.labels(
                brand=request.path_params.get('brand', 'unknown'),
                error_type=type(e).__name__
            ).inc()
            raise
```

### Health Checks

```python
# src/monitoring/health.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'openai_api': self._check_openai_api,
            'vector_store': self._check_vector_store,
            'redis': self._check_redis,
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Prüft Datenbank-Verbindung."""
        try:
            # Datenbank-Ping
            await db.ping()
            return {"status": "healthy", "response_time": 0.1}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_openai_api(self) -> Dict[str, Any]:
        """Prüft OpenAI API-Verbindung."""
        try:
            start_time = time.time()
            response = await openai_client.models.list()
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": duration,
                "models_available": len(response.data)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Führt alle Health Checks aus."""
        results = {}
        
        for check_name, check_func in self.checks.items():
            try:
                results[check_name] = await check_func()
            except Exception as e:
                results[check_name] = {"status": "error", "error": str(e)}
        
        # Gesamtstatus bestimmen
        overall_status = "healthy"
        if any(result.get("status") != "healthy" for result in results.values()):
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check src/
        isort --check-only src/
        flake8 src/
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/develop'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Staging deployment commands
    
    - name: Run smoke tests
      run: |
        echo "Running smoke tests on staging"
        # Smoke test commands

  deploy-production:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Production deployment commands
```

---

## 📚 API-Referenz

### Chat API

#### POST /api/v1/chat
Verarbeitet eine Kunden-Nachricht und gibt eine AI-Antwort zurück.

**Request Body:**
```json
{
  "brand": "heine",
  "message": "Wo ist meine Bestellung?",
  "session_id": "user123",
  "customer_id": "cust456",
  "metadata": {
    "channel": "web",
    "user_agent": "Mozilla/5.0..."
  }
}
```

**Response:**
```json
{
  "response": "Gerne helfe ich Ihnen bei Ihrer Bestellung. Können Sie mir Ihre Bestellnummer mitteilen?",
  "session_id": "user123",
  "confidence": 0.85,
  "escalation_required": false,
  "processing_time": 1.2,
  "sources": [
    {
      "title": "Bestellverfolgung FAQ",
      "url": "/faq/order-tracking",
      "relevance": 0.9
    }
  ]
}
```

#### GET /api/v1/sessions/{session_id}/history
Ruft die Konversationshistorie einer Session ab.

**Response:**
```json
{
  "session_id": "user123",
  "messages": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "role": "user",
      "content": "Wo ist meine Bestellung?"
    },
    {
      "timestamp": "2024-01-15T10:30:01Z",
      "role": "assistant",
      "content": "Gerne helfe ich Ihnen bei Ihrer Bestellung..."
    }
  ],
  "total_messages": 2,
  "session_duration": 3600
}
```

### Admin API

#### GET /api/v1/admin/health
System-Health-Check für Administratoren.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "response_time": 0.1},
    "openai_api": {"status": "healthy", "response_time": 0.5},
    "vector_store": {"status": "healthy", "response_time": 0.2}
  },
  "metrics": {
    "active_sessions": 15,
    "requests_per_minute": 120,
    "average_response_time": 1.2
  }
}
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# AI-Konfiguration
OPENAI_API_KEY=sk-your-api-key-here
AI_MODEL_NAME=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000

# Datenbank-Konfiguration
DATABASE_URL=sqlite:///./data/heine_ai.db
VECTOR_STORE_PATH=./data/vector_store
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=./logs/heine_ai.log

# Sicherheit
JWT_SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
CORS_ORIGINS=["http://localhost:3000", "https://app.heine.com"]

# Performance
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
CACHE_TTL=3600

# Monitoring
PROMETHEUS_PORT=9090
HEALTH_CHECK_INTERVAL=30
```

### Konfigurationsdateien

```yaml
# config/system.yaml
ai:
  model: gpt-3.5-turbo
  temperature: 0.7
  max_tokens: 1000
  timeout: 30

vector_store:
  type: chromadb
  backend: hnswlib
  persist_directory: ./data/vector_store
  similarity_threshold: 0.8

logging:
  level: INFO
  format: json
  file: ./logs/heine_ai.log
  max_size: 100MB
  backup_count: 5

security:
  jwt_secret: your-secret-key
  encryption_key: your-encryption-key
  cors_origins:
    - http://localhost:3000
    - https://app.heine.com

monitoring:
  prometheus_port: 9090
  health_check_interval: 30
  metrics_enabled: true
```

---

## 🐛 Troubleshooting

### Häufige Probleme

#### 1. OpenAI API-Fehler
```python
# Problem: Rate Limit Error
openai.RateLimitError: Rate limit exceeded

# Lösung: Retry-Logic implementieren
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(openai.RateLimitError)
)
async def safe_openai_call(func, *args, **kwargs):
    return await func(*args, **kwargs)
```

#### 2. ChromaDB Windows-Probleme
```bash
# Problem: ONNX Runtime DLL-Fehler
ImportError: DLL load failed while importing onnxruntime

# Lösung: Alternative Backend verwenden
# In src/knowledge/vector_store.py
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/vector_store"
))
```

#### 3. Memory Leaks
```python
# Problem: Memory wächst kontinuierlich
# Lösung: Session-Cleanup implementieren

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.max_sessions = 1000
    
    async def cleanup_old_sessions(self):
        """Bereinigt alte Sessions."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_activity > 3600  # 1 Stunde
        ]
        
        for session_id in expired_sessions:
            await self.remove_session(session_id)
```

### Debug-Tools

```python
# src/utils/debug_tools.py
import tracemalloc
import asyncio
import time
from typing import Dict, Any

class DebugTools:
    def __init__(self):
        tracemalloc.start()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Gibt aktuellen Speicherverbrauch zurück."""
        current, peak = tracemalloc.get_traced_memory()
        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
            "top_allocations": tracemalloc.get_traced_memory()
        }
    
    async def profile_function(self, func, *args, **kwargs):
        """Profiliert eine Funktion."""
        start_time = time.time()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = tracemalloc.get_traced_memory()[0]
            
            return {
                "result": result,
                "execution_time": end_time - start_time,
                "memory_delta": end_memory - start_memory
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_top_allocations(self, limit: int = 10):
        """Gibt Top-Speicherallokationen zurück."""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        return [
            {
                "file": stat.traceback.format()[0],
                "size_mb": stat.size / 1024 / 1024,
                "count": stat.count
            }
            for stat in top_stats[:limit]
        ]
```

---

*Entwickler-Dokumentation erstellt: [Datum]*  
*Letzte Aktualisierung: [Datum]*  
*Version: 1.0.0* 