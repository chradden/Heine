"""
DSGVO-konformes Logging-System für das Heine KI-Kundenkommunikationssystem.
"""
import logging
import hashlib
import re
import json
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import wraps
import uuid

from .config import get_system_config


class DataAnonymizer:
    """Anonymisiert personenbezogene Daten in Logs."""
    
    def __init__(self):
        # Regex-Patterns für verschiedene Datentypen
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+49|0)[0-9\s\-\(\)]{8,}',
            'customer_id': r'cust[0-9]{6,}',
            'order_id': r'ord[0-9]{8,}',
            'name': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'address': r'\b[A-Za-zäöüß\s]+ \d+[A-Za-z]?\b',
            'postal_code': r'\b\d{5}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
        
        # Hash-Cache für konsistente Anonymisierung
        self.hash_cache: Dict[str, str] = {}
    
    def anonymize_text(self, text: str) -> str:
        """Anonymisiert Text durch Ersetzung sensibler Daten."""
        if not text:
            return text
        
        anonymized = text
        
        # E-Mail-Adressen
        anonymized = re.sub(
            self.patterns['email'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Telefonnummern
        anonymized = re.sub(
            self.patterns['phone'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Kunden-IDs
        anonymized = re.sub(
            self.patterns['customer_id'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Bestell-IDs
        anonymized = re.sub(
            self.patterns['order_id'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Namen (einfache Erkennung)
        anonymized = re.sub(
            self.patterns['name'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Adressen
        anonymized = re.sub(
            self.patterns['address'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # Postleitzahlen
        anonymized = re.sub(
            self.patterns['postal_code'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        # IP-Adressen
        anonymized = re.sub(
            self.patterns['ip_address'],
            lambda m: self._hash_value(m.group(0)),
            anonymized
        )
        
        return anonymized
    
    def _hash_value(self, value: str) -> str:
        """Erstellt einen konsistenten Hash für einen Wert."""
        if value in self.hash_cache:
            return self.hash_cache[value]
        
        # Erstelle einen kurzen, konsistenten Hash
        hash_obj = hashlib.sha256(value.encode())
        short_hash = hash_obj.hexdigest()[:8]
        self.hash_cache[value] = f"[HASH:{short_hash}]"
        
        return self.hash_cache[value]
    
    def anonymize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymisiert ein Dictionary rekursiv."""
        anonymized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                anonymized[key] = self.anonymize_text(value)
            elif isinstance(value, dict):
                anonymized[key] = self.anonymize_dict(value)
            elif isinstance(value, list):
                anonymized[key] = [
                    self.anonymize_text(item) if isinstance(item, str)
                    else self.anonymize_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                anonymized[key] = value
        
        return anonymized


class ConversationLogger:
    """Protokolliert Konversationen mit DSGVO-Konformität."""
    
    def __init__(self, log_dir: str = "./logs/conversations"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.anonymizer = DataAnonymizer()
        self.system_config = get_system_config()
    
    def log_conversation(
        self,
        session_id: str,
        brand: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Protokolliert eine Konversation."""
        timestamp = datetime.now()
        
        # Erstelle Session-Datei
        session_file = self.log_dir / f"{session_id}.jsonl"
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "brand": brand,
            "session_id": session_id,
            "user_message": self.anonymizer.anonymize_text(user_message),
            "ai_response": self.anonymizer.anonymize_text(ai_response),
            "metadata": self.anonymizer.anonymize_dict(metadata or {})
        }
        
        with open(session_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Lädt den Konversationsverlauf für eine Session."""
        session_file = self.log_dir / f"{session_id}.jsonl"
        
        if not session_file.exists():
            return []
        
        history = []
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
        
        return history
    
    def delete_conversation(self, session_id: str) -> bool:
        """Löscht eine Konversation (DSGVO-Recht auf Löschung)."""
        session_file = self.log_dir / f"{session_id}.jsonl"
        
        if session_file.exists():
            session_file.unlink()
            return True
        
        return False
    
    def cleanup_old_conversations(self, days: Optional[int] = None):
        """Löscht alte Konversationen basierend auf Aufbewahrungsrichtlinie."""
        if days is None:
            days = self.system_config.data_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for session_file in self.log_dir.glob("*.jsonl"):
            try:
                # Prüfe das Datum der ersten Zeile
                with open(session_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if first_line:
                        first_entry = json.loads(first_line)
                        file_date = datetime.fromisoformat(first_entry["timestamp"])
                        
                        if file_date < cutoff_date:
                            session_file.unlink()
            except Exception as e:
                # Bei Fehlern Datei trotzdem löschen
                session_file.unlink()


class HeineLogger:
    """Hauptlogger für das Heine-System."""
    
    def __init__(self):
        self.system_config = get_system_config()
        self.anonymizer = DataAnonymizer()
        self.conversation_logger = ConversationLogger()
        
        # Konfiguriere structlog
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
                self._anonymize_processor,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Erstelle Logger-Instanz
        self.logger = structlog.get_logger()
        
        # Konfiguriere File-Handler
        self._setup_file_handler()
    
    def _anonymize_processor(self, logger, method_name, event_dict):
        """Anonymisiert Log-Einträge."""
        if not self.system_config.anonymize_logs:
            return event_dict
        
        # Anonymisiere alle String-Werte
        for key, value in event_dict.items():
            if isinstance(value, str):
                event_dict[key] = self.anonymizer.anonymize_text(value)
            elif isinstance(value, dict):
                event_dict[key] = self.anonymizer.anonymize_dict(value)
        
        return event_dict
    
    def _setup_file_handler(self):
        """Konfiguriert File-Handler für Logs."""
        log_file = Path(self.system_config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Standard Python-Logging für File-Handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, self.system_config.log_level.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Füge Handler zum Root-Logger hinzu
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().setLevel(getattr(logging, self.system_config.log_level.upper()))
    
    def log_chat_interaction(
        self,
        brand: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        confidence: float = 0.0,
        escalated: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Protokolliert eine Chat-Interaktion."""
        # Protokolliere in Konversations-Log
        self.conversation_logger.log_conversation(
            session_id, brand, user_message, ai_response, metadata
        )
        
        # Protokolliere in System-Log
        self.logger.info(
            "chat_interaction",
            brand=brand,
            session_id=session_id,
            message_length=len(user_message),
            response_length=len(ai_response),
            confidence=confidence,
            escalated=escalated
        )
    
    def log_escalation(
        self,
        brand: str,
        session_id: str,
        reason: str,
        trigger_message: str
    ):
        """Protokolliert eine Eskalation."""
        self.logger.warning(
            "escalation_triggered",
            brand=brand,
            session_id=session_id,
            reason=reason,
            trigger_message=self.anonymizer.anonymize_text(trigger_message)
        )
    
    def log_api_call(
        self,
        brand: str,
        endpoint: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ):
        """Protokolliert API-Aufrufe."""
        self.logger.info(
            "api_call",
            brand=brand,
            endpoint=endpoint,
            success=success,
            response_time=response_time,
            error=error
        )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Protokolliert Fehler."""
        self.logger.error(
            "system_error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )
    
    def cleanup_old_data(self):
        """Bereinigt alte Daten."""
        self.conversation_logger.cleanup_old_conversations()


# Globale Logger-Instanz
heine_logger = HeineLogger()


def get_logger():
    """Gibt die globale Logger-Instanz zurück."""
    return heine_logger


def log_function_call(func):
    """Decorator zum Protokollieren von Funktionsaufrufen."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        
        try:
            result = func(*args, **kwargs)
            logger.logger.info(
                "function_call",
                function=func.__name__,
                success=True
            )
            return result
        except Exception as e:
            logger.log_error(e, {"function": func.__name__})
            raise
    
    return wrapper 