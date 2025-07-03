"""
Zentrale Konfigurationsverwaltung für das Heine KI-Kundenkommunikationssystem.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from pydantic import BaseSettings, Field


class BrandConfig(BaseSettings):
    """Konfiguration für einen einzelnen Mandanten/Marke."""
    name: str
    description: str
    knowledge_base_path: str
    api_endpoint: str
    escalation_threshold: float = 0.7
    support_email: str
    brand_voice: str
    primary_language: str = "de"
    supported_languages: List[str] = ["de", "en"]
    brand_colors: Dict[str, str] = {}
    escalation_rules: List[Dict[str, str]] = []
    knowledge_categories: List[str] = []
    api_endpoints: Dict[str, str] = {}


class SystemConfig(BaseSettings):
    """Hauptkonfiguration des Systems."""
    
    # LLM-Konfiguration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    local_model_path: Optional[str] = Field(None, env="LOCAL_MODEL_PATH")
    model_name: str = Field("gpt-3.5-turbo", env="MODEL_NAME")
    model_temperature: float = Field(0.7, env="MODEL_TEMPERATURE")
    model_max_tokens: int = Field(1000, env="MODEL_MAX_TOKENS")
    
    # Mandanten-Konfiguration
    brands: List[str] = Field(["heine"], env="BRANDS")
    default_brand: str = Field("heine", env="DEFAULT_BRAND")
    
    # Vector Store
    vector_store_type: str = Field("chromadb", env="VECTOR_STORE_TYPE")
    vector_store_path: str = Field("./data/vector_store", env="VECTOR_STORE_PATH")
    embedding_model: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # API-Konfiguration
    customer_api_url: str = Field("http://localhost:8001/api", env="CUSTOMER_API_URL")
    customer_api_key: Optional[str] = Field(None, env="CUSTOMER_API_KEY")
    api_timeout: int = Field(30, env="API_TIMEOUT")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("./logs/heine_ai.log", env="LOG_FILE")
    anonymize_logs: bool = Field(True, env="ANONYMIZE_LOGS")
    
    # Datenschutz
    data_retention_days: int = Field(30, env="DATA_RETENTION_DAYS")
    enable_data_deletion: bool = Field(True, env="ENABLE_DATA_DELETION")
    
    # Eskalation
    escalation_threshold: float = Field(0.7, env="ESCALATION_THRESHOLD")
    escalation_keywords: List[str] = Field(
        ["mitarbeiter", "beschwerde", "sofort", "unzufrieden"], 
        env="ESCALATION_KEYWORDS"
    )
    
    # Web Server
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    streamlit_port: int = Field(8501, env="STREAMLIT_PORT")
    
    # Email
    smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    
    # Security
    secret_key: str = Field("your_secret_key_here", env="SECRET_KEY")
    encryption_key: str = Field("your_encryption_key_here", env="ENCRYPTION_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class ConfigManager:
    """Zentrale Konfigurationsverwaltung."""
    
    def __init__(self, config_path: str = "config/brands"):
        self.config_path = Path(config_path)
        self.system_config = SystemConfig()
        self.brand_configs: Dict[str, BrandConfig] = {}
        self._load_brand_configs()
    
    def _load_brand_configs(self):
        """Lädt alle Mandanten-Konfigurationen."""
        if not self.config_path.exists():
            return
        
        for config_file in self.config_path.glob("*.yaml"):
            brand_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    self.brand_configs[brand_name] = BrandConfig(**config_data)
            except Exception as e:
                print(f"Fehler beim Laden der Konfiguration für {brand_name}: {e}")
    
    def get_brand_config(self, brand_name: str) -> Optional[BrandConfig]:
        """Gibt die Konfiguration für eine bestimmte Marke zurück."""
        return self.brand_configs.get(brand_name)
    
    def get_all_brands(self) -> List[str]:
        """Gibt alle verfügbaren Marken zurück."""
        return list(self.brand_configs.keys())
    
    def get_default_brand(self) -> str:
        """Gibt die Standard-Marke zurück."""
        return self.system_config.default_brand
    
    def validate_config(self) -> List[str]:
        """Validiert die Konfiguration und gibt Fehler zurück."""
        errors = []
        
        # Prüfe ob Standard-Marke existiert
        if self.system_config.default_brand not in self.brand_configs:
            errors.append(f"Standard-Marke '{self.system_config.default_brand}' nicht gefunden")
        
        # Prüfe API-Schlüssel
        if not self.system_config.openai_api_key:
            errors.append("OpenAI API-Schlüssel nicht konfiguriert")
        
        # Prüfe Pfade
        if not Path(self.system_config.vector_store_path).parent.exists():
            errors.append(f"Vector Store Pfad existiert nicht: {self.system_config.vector_store_path}")
        
        return errors
    
    def get_knowledge_base_path(self, brand_name: str) -> Optional[str]:
        """Gibt den Pfad zur Wissensdatenbank für eine Marke zurück."""
        brand_config = self.get_brand_config(brand_name)
        return brand_config.knowledge_base_path if brand_config else None
    
    def get_api_endpoint(self, brand_name: str) -> Optional[str]:
        """Gibt den API-Endpunkt für eine Marke zurück."""
        brand_config = self.get_brand_config(brand_name)
        return brand_config.api_endpoint if brand_config else None


# Globale Konfigurationsinstanz
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Gibt die globale Konfigurationsinstanz zurück."""
    return config_manager


def get_brand_config(brand_name: str) -> Optional[BrandConfig]:
    """Hilfsfunktion zum Abrufen der Marken-Konfiguration."""
    return config_manager.get_brand_config(brand_name)


def get_system_config() -> SystemConfig:
    """Gibt die System-Konfiguration zurück."""
    return config_manager.system_config 