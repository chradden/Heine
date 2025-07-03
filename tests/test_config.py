"""
Tests für die Konfigurationsverwaltung.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, mock_open

from src.utils.config import (
    get_system_config, get_brand_config, load_brand_config,
    SystemConfig, BrandConfig
)


class TestSystemConfig:
    """Tests für SystemConfig."""
    
    def test_system_config_defaults(self):
        """Testet Standardwerte der SystemConfig."""
        config = SystemConfig()
        
        assert config.openai_api_key == ""
        assert config.model_name == "gpt-3.5-turbo"
        assert config.model_temperature == 0.7
        assert config.model_max_tokens == 1000
        assert config.escalation_threshold == 0.5
        assert isinstance(config.escalation_keywords, list)
    
    def test_system_config_from_env(self):
        """Testet SystemConfig aus Umgebungsvariablen."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'MODEL_NAME': 'gpt-4',
            'MODEL_TEMPERATURE': '0.5',
            'MODEL_MAX_TOKENS': '2000',
            'ESCALATION_THRESHOLD': '0.6'
        }):
            config = SystemConfig()
            
            assert config.openai_api_key == 'test-key'
            assert config.model_name == 'gpt-4'
            assert config.model_temperature == 0.5
            assert config.model_max_tokens == 2000
            assert config.escalation_threshold == 0.6


class TestBrandConfig:
    """Tests für BrandConfig."""
    
    def test_brand_config_defaults(self):
        """Testet Standardwerte der BrandConfig."""
        config = BrandConfig()
        
        assert config.name == ""
        assert config.description == ""
        assert config.brand_voice == ""
        assert config.support_email == ""
        assert config.escalation_threshold == 0.5
        assert isinstance(config.escalation_rules, list)
    
    def test_brand_config_from_dict(self):
        """Testet BrandConfig aus Dictionary."""
        config_data = {
            "name": "Test Brand",
            "description": "Test Description",
            "brand_voice": "Friendly and professional",
            "support_email": "support@test.com",
            "escalation_threshold": 0.7,
            "escalation_rules": [
                {"trigger": "complaint", "priority": "high", "department": "support"}
            ]
        }
        
        config = BrandConfig(**config_data)
        
        assert config.name == "Test Brand"
        assert config.description == "Test Description"
        assert config.brand_voice == "Friendly and professional"
        assert config.support_email == "support@test.com"
        assert config.escalation_threshold == 0.7
        assert len(config.escalation_rules) == 1


class TestConfigLoading:
    """Tests für das Laden von Konfigurationen."""
    
    def test_load_brand_config_valid_yaml(self):
        """Testet das Laden einer gültigen YAML-Konfiguration."""
        yaml_content = """
name: Test Brand
description: Test Description
brand_voice: Friendly and professional
support_email: support@test.com
escalation_threshold: 0.7
escalation_rules:
  - trigger: complaint
    priority: high
    department: support
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = load_brand_config("test_brand")
            
            assert config.name == "Test Brand"
            assert config.description == "Test Description"
            assert config.brand_voice == "Friendly and professional"
            assert config.support_email == "support@test.com"
            assert config.escalation_threshold == 0.7
            assert len(config.escalation_rules) == 1
    
    def test_load_brand_config_invalid_yaml(self):
        """Testet das Laden einer ungültigen YAML-Konfiguration."""
        invalid_yaml = "invalid: yaml: content:"
        
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(Exception):
                load_brand_config("test_brand")
    
    def test_load_brand_config_file_not_found(self):
        """Testet das Laden einer nicht existierenden Konfigurationsdatei."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            config = load_brand_config("nonexistent_brand")
            assert config is None
    
    def test_get_system_config(self):
        """Testet get_system_config."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            config = get_system_config()
            
            assert isinstance(config, SystemConfig)
            assert config.openai_api_key == 'test-key'
    
    def test_get_brand_config_existing(self):
        """Testet get_brand_config für existierende Marke."""
        yaml_content = """
name: Test Brand
description: Test Description
brand_voice: Friendly
support_email: support@test.com
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = get_brand_config("test_brand")
            
            assert isinstance(config, BrandConfig)
            assert config.name == "Test Brand"
    
    def test_get_brand_config_nonexistent(self):
        """Testet get_brand_config für nicht existierende Marke."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            config = get_brand_config("nonexistent_brand")
            assert config is None


class TestConfigValidation:
    """Tests für Konfigurationsvalidierung."""
    
    def test_system_config_validation(self):
        """Testet Validierung der SystemConfig."""
        # Gültige Konfiguration
        config = SystemConfig(
            openai_api_key="test-key",
            model_name="gpt-3.5-turbo",
            model_temperature=0.5,
            model_max_tokens=1000,
            escalation_threshold=0.6
        )
        
        assert config.model_temperature >= 0.0
        assert config.model_temperature <= 1.0
        assert config.model_max_tokens > 0
        assert config.escalation_threshold >= 0.0
        assert config.escalation_threshold <= 1.0
    
    def test_brand_config_validation(self):
        """Testet Validierung der BrandConfig."""
        # Gültige Konfiguration
        config = BrandConfig(
            name="Test Brand",
            description="Test Description",
            brand_voice="Friendly",
            support_email="support@test.com",
            escalation_threshold=0.6
        )
        
        assert config.name != ""
        assert config.support_email != ""
        assert config.escalation_threshold >= 0.0
        assert config.escalation_threshold <= 1.0


if __name__ == "__main__":
    pytest.main([__file__]) 