"""
Marken-spezifische Agenten mit API-Tools.
"""
import uuid
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool, tool
from langchain.schema import BaseRetriever

from .base_agent import HeineBaseAgent
from ..api.client import get_api_client, get_mock_api_client
from ..utils.config import get_system_config
from ..utils.logger import get_logger
from ..models.api_models import Customer, Order, ShippingInfo, Product


class CustomerInfoTool(BaseTool):
    """Tool zum Abrufen von Kundendaten."""
    
    name = "get_customer_info"
    description = "Ruft Informationen über einen Kunden ab. Verwende diese Funktion, wenn der Kunde nach seinen Daten fragt oder eine Kunden-ID erwähnt wird."
    
    def __init__(self, brand: str, api_client):
        super().__init__()
        self.brand = brand
        self.api_client = api_client
    
    def _run(self, customer_id: str) -> str:
        """Synchroner Aufruf für LangChain."""
        import asyncio
        return asyncio.run(self._arun(customer_id))
    
    async def _arun(self, customer_id: str) -> str:
        """Asynchroner Aufruf für Kundendaten."""
        try:
            customer = await self.api_client.get_customer_info(self.brand, customer_id)
            if customer:
                return f"Kunde gefunden: {customer.first_name} {customer.last_name}, E-Mail: {customer.email}, Bestellungen: {customer.total_orders}, Gesamtausgaben: {customer.total_spent}€"
            else:
                return f"Kunde mit ID {customer_id} nicht gefunden."
        except Exception as e:
            return f"Fehler beim Abrufen der Kundendaten: {str(e)}"


class OrderInfoTool(BaseTool):
    """Tool zum Abrufen von Bestelldaten."""
    
    name = "get_order_info"
    description = "Ruft Informationen über eine Bestellung ab. Verwende diese Funktion, wenn der Kunde nach seinem Bestellstatus fragt oder eine Bestell-ID erwähnt wird."
    
    def __init__(self, brand: str, api_client):
        super().__init__()
        self.brand = brand
        self.api_client = api_client
    
    def _run(self, order_id: str) -> str:
        """Synchroner Aufruf für LangChain."""
        import asyncio
        return asyncio.run(self._arun(order_id))
    
    async def _arun(self, order_id: str) -> str:
        """Asynchroner Aufruf für Bestelldaten."""
        try:
            order = await self.api_client.get_order_info(self.brand, order_id)
            if order:
                items_text = ", ".join([f"{item.quantity}x {item.product_name}" for item in order.items])
                return f"Bestellung {order_id}: Status {order.status}, Betrag: {order.total_amount}€, Artikel: {items_text}"
            else:
                return f"Bestellung mit ID {order_id} nicht gefunden."
        except Exception as e:
            return f"Fehler beim Abrufen der Bestelldaten: {str(e)}"


class ShippingInfoTool(BaseTool):
    """Tool zum Abrufen von Versanddaten."""
    
    name = "get_shipping_info"
    description = "Ruft Versandinformationen ab. Verwende diese Funktion, wenn der Kunde nach dem Versandstatus fragt oder eine Tracking-ID erwähnt wird."
    
    def __init__(self, brand: str, api_client):
        super().__init__()
        self.brand = brand
        self.api_client = api_client
    
    def _run(self, tracking_id: str) -> str:
        """Synchroner Aufruf für LangChain."""
        import asyncio
        return asyncio.run(self._arun(tracking_id))
    
    async def _arun(self, tracking_id: str) -> str:
        """Asynchroner Aufruf für Versanddaten."""
        try:
            shipping = await self.api_client.get_shipping_info(self.brand, tracking_id)
            if shipping:
                status_text = f"Status: {shipping.status}"
                if shipping.estimated_delivery:
                    status_text += f", Geschätzte Lieferung: {shipping.estimated_delivery}"
                if shipping.actual_delivery:
                    status_text += f", Tatsächliche Lieferung: {shipping.actual_delivery}"
                return f"Versand {tracking_id}: {status_text}, Versandunternehmen: {shipping.carrier}"
            else:
                return f"Versand mit Tracking-ID {tracking_id} nicht gefunden."
        except Exception as e:
            return f"Fehler beim Abrufen der Versanddaten: {str(e)}"


class ProductSearchTool(BaseTool):
    """Tool zur Produktsuche."""
    
    name = "search_products"
    description = "Sucht nach Produkten. Verwende diese Funktion, wenn der Kunde nach Produkten fragt oder Produktinformationen benötigt."
    
    def __init__(self, brand: str, api_client):
        super().__init__()
        self.brand = brand
        self.api_client = api_client
    
    def _run(self, query: str, category: str = "") -> str:
        """Synchroner Aufruf für LangChain."""
        import asyncio
        return asyncio.run(self._arun(query, category))
    
    async def _arun(self, query: str, category: str = "") -> str:
        """Asynchroner Aufruf für Produktsuche."""
        try:
            products = await self.api_client.search_products(
                self.brand, query, category if category else None, max_results=5
            )
            if products:
                result = f"Gefundene Produkte für '{query}':\n"
                for product in products:
                    result += f"- {product.name}: {product.price}€ ({product.description})\n"
                return result
            else:
                return f"Keine Produkte für '{query}' gefunden."
        except Exception as e:
            return f"Fehler bei der Produktsuche: {str(e)}"


class HeineBrandAgent(HeineBaseAgent):
    """Marken-spezifischer Agent für Heine."""
    
    def __init__(self, brand: str, use_mock_api: bool = False):
        super().__init__(brand)
        
        # API-Client initialisieren
        if use_mock_api:
            self.api_client = get_mock_api_client()
        else:
            self.api_client = get_api_client()
        
        # Tools hinzufügen
        self._add_api_tools()
    
    def _add_api_tools(self):
        """Fügt API-Tools zum Agenten hinzu."""
        tools = [
            CustomerInfoTool(self.brand, self.api_client),
            OrderInfoTool(self.brand, self.api_client),
            ShippingInfoTool(self.brand, self.api_client),
            ProductSearchTool(self.brand, self.api_client)
        ]
        
        for tool in tools:
            self.add_tool(tool)
    
    def get_brand_specific_prompt(self) -> str:
        """Gibt ein markenspezifisches Prompt zurück."""
        return f"""Du bist der KI-Assistent für {self.brand_config.name}.
        
Markenspezifische Informationen:
- Marke: {self.brand_config.name}
- Beschreibung: {self.brand_config.description}
- Markenstimme: {self.brand_config.brand_voice}
- Support-E-Mail: {self.brand_config.support_email}

Verfügbare Tools:
- get_customer_info: Kundendaten abrufen
- get_order_info: Bestelldaten abrufen
- get_shipping_info: Versanddaten abrufen
- search_products: Produktsuche

Antworte immer freundlich und professionell im Stil von {self.brand_config.brand_voice}."""


class SubBrand1Agent(HeineBaseAgent):
    """Marken-spezifischer Agent für SubBrand1."""
    
    def __init__(self, brand: str = "subbrand1", use_mock_api: bool = False):
        super().__init__(brand)
        
        # API-Client initialisieren
        if use_mock_api:
            self.api_client = get_mock_api_client()
        else:
            self.api_client = get_api_client()
        
        # Tools hinzufügen
        self._add_api_tools()
    
    def _add_api_tools(self):
        """Fügt API-Tools zum Agenten hinzu."""
        tools = [
            CustomerInfoTool(self.brand, self.api_client),
            OrderInfoTool(self.brand, self.api_client),
            ShippingInfoTool(self.brand, self.api_client),
            ProductSearchTool(self.brand, self.api_client)
        ]
        
        for tool in tools:
            self.add_tool(tool)
    
    def get_brand_specific_prompt(self) -> str:
        """Gibt ein markenspezifisches Prompt zurück."""
        return f"""Du bist der KI-Assistent für {self.brand_config.name}.
        
Markenspezifische Informationen:
- Marke: {self.brand_config.name}
- Beschreibung: {self.brand_config.description}
- Markenstimme: {self.brand_config.brand_voice}
- Support-E-Mail: {self.brand_config.support_email}

Verfügbare Tools:
- get_customer_info: Kundendaten abrufen
- get_order_info: Bestelldaten abrufen
- get_shipping_info: Versanddaten abrufen
- search_products: Produktsuche

Antworte immer freundlich und professionell im Stil von {self.brand_config.brand_voice}."""


class AgentFactory:
    """Factory für die Erstellung von Marken-Agenten."""
    
    @staticmethod
    def create_agent(brand: str, use_mock_api: bool = False) -> HeineBaseAgent:
        """Erstellt einen Agenten für eine bestimmte Marke."""
        if brand == "heine":
            return HeineBrandAgent(brand, use_mock_api)
        elif brand == "subbrand1":
            return SubBrand1Agent(brand, use_mock_api)
        else:
            # Fallback: Generischer Agent
            return HeineBrandAgent(brand, use_mock_api)
    
    @staticmethod
    def get_available_brands() -> List[str]:
        """Gibt alle verfügbaren Marken zurück."""
        return ["heine", "subbrand1"]


# Globale Agent-Instanzen (Cache)
_agent_cache: Dict[str, HeineBaseAgent] = {}


def get_agent(brand: str, use_mock_api: bool = False) -> HeineBaseAgent:
    """Gibt einen Agenten für eine Marke zurück (mit Caching)."""
    cache_key = f"{brand}_{use_mock_api}"
    
    if cache_key not in _agent_cache:
        _agent_cache[cache_key] = AgentFactory.create_agent(brand, use_mock_api)
    
    return _agent_cache[cache_key]


def clear_agent_cache():
    """Löscht den Agent-Cache."""
    global _agent_cache
    _agent_cache.clear() 