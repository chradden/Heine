"""
API-Client für Kunden- und Versanddaten.
"""
import time
import uuid
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime

from ..models.api_models import (
    Customer, Order, ShippingInfo, Product,
    CustomerInfoRequest, OrderInfoRequest, ShippingInfoRequest,
    ProductSearchRequest, APIResponse
)
from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger


class HeineAPIClient:
    """API-Client für Heine-Systeme."""
    
    def __init__(self):
        self.system_config = get_system_config()
        self.logger = get_logger()
        
        # HTTP-Client mit Timeout
        self.client = httpx.AsyncClient(
            timeout=self.system_config.api_timeout,
            headers={
                "User-Agent": "Heine-AI-Support/1.0",
                "Content-Type": "application/json"
            }
        )
    
    def _get_api_url(self, brand: str, endpoint: str) -> str:
        """Gibt die vollständige API-URL für eine Marke zurück."""
        brand_config = get_brand_config(brand)
        if not brand_config:
            raise ValueError(f"Marken-Konfiguration nicht gefunden: {brand}")
        
        base_url = brand_config.api_endpoint.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"
    
    def _add_auth_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Fügt Authentifizierungs-Header hinzu."""
        if self.system_config.customer_api_key:
            headers["Authorization"] = f"Bearer {self.system_config.customer_api_key}"
        return headers
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Führt einen API-Request aus."""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        if headers is None:
            headers = {}
        
        headers = self._add_auth_headers(headers)
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Nicht unterstützte HTTP-Methode: {method}")
            
            response_time = time.time() - start_time
            
            # Log API-Aufruf
            self.logger.log_api_call(
                brand=data.get("brand", "unknown") if data else "unknown",
                endpoint=url,
                success=response.status_code < 400,
                response_time=response_time,
                error=None if response.status_code < 400 else f"HTTP {response.status_code}"
            )
            
            if response.status_code < 400:
                return APIResponse(
                    request_id=request_id,
                    success=True,
                    data=response.json() if response.content else None,
                    response_time=response_time
                )
            else:
                return APIResponse(
                    request_id=request_id,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    response_time=response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.log_error(e, {"url": url, "method": method})
            
            return APIResponse(
                request_id=request_id,
                success=False,
                error=str(e),
                response_time=response_time
            )
    
    async def get_customer_info(self, brand: str, customer_id: str) -> Optional[Customer]:
        """Ruft Kundendaten ab."""
        try:
            url = self._get_api_url(brand, f"customers/{customer_id}")
            
            response = await self._make_request("GET", url)
            
            if response.success and response.data:
                return Customer(**response.data)
            else:
                self.logger.logger.warning(
                    f"Kundendaten nicht gefunden: {customer_id} für Marke {brand}"
                )
                return None
                
        except Exception as e:
            self.logger.log_error(e, {"customer_id": customer_id, "brand": brand})
            return None
    
    async def get_order_info(self, brand: str, order_id: str) -> Optional[Order]:
        """Ruft Bestelldaten ab."""
        try:
            url = self._get_api_url(brand, f"orders/{order_id}")
            
            response = await self._make_request("GET", url)
            
            if response.success and response.data:
                return Order(**response.data)
            else:
                self.logger.logger.warning(
                    f"Bestelldaten nicht gefunden: {order_id} für Marke {brand}"
                )
                return None
                
        except Exception as e:
            self.logger.log_error(e, {"order_id": order_id, "brand": brand})
            return None
    
    async def get_shipping_info(self, brand: str, tracking_id: str) -> Optional[ShippingInfo]:
        """Ruft Versanddaten ab."""
        try:
            url = self._get_api_url(brand, f"shipping/{tracking_id}")
            
            response = await self._make_request("GET", url)
            
            if response.success and response.data:
                return ShippingInfo(**response.data)
            else:
                self.logger.logger.warning(
                    f"Versanddaten nicht gefunden: {tracking_id} für Marke {brand}"
                )
                return None
                
        except Exception as e:
            self.logger.log_error(e, {"tracking_id": tracking_id, "brand": brand})
            return None
    
    async def search_products(
        self,
        brand: str,
        query: str,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[Product]:
        """Sucht nach Produkten."""
        try:
            url = self._get_api_url(brand, "products/search")
            
            data = {
                "query": query,
                "max_results": max_results
            }
            if category:
                data["category"] = category
            
            response = await self._make_request("POST", url, data)
            
            if response.success and response.data:
                products = []
                for product_data in response.data.get("products", []):
                    products.append(Product(**product_data))
                return products
            else:
                return []
                
        except Exception as e:
            self.logger.log_error(e, {"query": query, "brand": brand})
            return []
    
    async def get_customer_orders(
        self,
        brand: str,
        customer_id: str,
        limit: int = 10
    ) -> List[Order]:
        """Ruft Bestellungen eines Kunden ab."""
        try:
            url = self._get_api_url(brand, f"customers/{customer_id}/orders")
            
            data = {"limit": limit}
            response = await self._make_request("GET", url)
            
            if response.success and response.data:
                orders = []
                for order_data in response.data.get("orders", []):
                    orders.append(Order(**order_data))
                return orders
            else:
                return []
                
        except Exception as e:
            self.logger.log_error(e, {"customer_id": customer_id, "brand": brand})
            return []
    
    async def update_order_status(
        self,
        brand: str,
        order_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Aktualisiert den Status einer Bestellung."""
        try:
            url = self._get_api_url(brand, f"orders/{order_id}/status")
            
            data = {"status": status}
            if notes:
                data["notes"] = notes
            
            response = await self._make_request("PUT", url, data)
            
            return response.success
                
        except Exception as e:
            self.logger.log_error(e, {"order_id": order_id, "brand": brand})
            return False
    
    async def create_support_ticket(
        self,
        brand: str,
        customer_id: str,
        subject: str,
        description: str,
        priority: str = "medium"
    ) -> Optional[str]:
        """Erstellt ein Support-Ticket."""
        try:
            url = self._get_api_url(brand, "support/tickets")
            
            data = {
                "customer_id": customer_id,
                "subject": subject,
                "description": description,
                "priority": priority,
                "created_at": datetime.now().isoformat()
            }
            
            response = await self._make_request("POST", url, data)
            
            if response.success and response.data:
                return response.data.get("ticket_id")
            else:
                return None
                
        except Exception as e:
            self.logger.log_error(e, {"customer_id": customer_id, "brand": brand})
            return None
    
    async def close(self):
        """Schließt den HTTP-Client."""
        await self.client.aclose()


class MockHeineAPIClient(HeineAPIClient):
    """Mock-API-Client für Tests und Entwicklung."""
    
    def __init__(self):
        super().__init__()
        self._mock_data = self._initialize_mock_data()
    
    def _initialize_mock_data(self) -> Dict[str, Any]:
        """Initialisiert Mock-Daten."""
        return {
            "customers": {
                "cust123456": {
                    "customer_id": "cust123456",
                    "brand": "heine",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max.mustermann@example.com",
                    "phone": "+49 123 456789",
                    "address": {
                        "street": "Musterstraße 123",
                        "city": "Musterstadt",
                        "postal_code": "12345",
                        "country": "Deutschland"
                    },
                    "created_at": "2023-01-15T10:30:00",
                    "last_order_date": "2024-01-10T14:20:00",
                    "total_orders": 5,
                    "total_spent": 299.99,
                    "is_vip": False
                },
                "cust789012": {
                    "customer_id": "cust789012",
                    "brand": "heine",
                    "first_name": "Anna",
                    "last_name": "Schmidt",
                    "email": "anna.schmidt@example.com",
                    "phone": "+49 987 654321",
                    "address": {
                        "street": "Beispielweg 456",
                        "city": "Beispielstadt",
                        "postal_code": "54321",
                        "country": "Deutschland"
                    },
                    "created_at": "2022-06-20T09:15:00",
                    "last_order_date": "2024-01-05T16:45:00",
                    "total_orders": 12,
                    "total_spent": 899.50,
                    "is_vip": True
                }
            },
            "orders": {
                "ord2024001": {
                    "order_id": "ord2024001",
                    "customer_id": "cust123456",
                    "brand": "heine",
                    "status": "shipped",
                    "items": [
                        {
                            "product_id": "prod001",
                            "product_name": "Heine Premium Bier 6er Pack",
                            "quantity": 2,
                            "unit_price": 12.99,
                            "total_price": 25.98
                        }
                    ],
                    "total_amount": 29.98,
                    "shipping_address": {
                        "street": "Musterstraße 123",
                        "city": "Musterstadt",
                        "postal_code": "12345",
                        "country": "Deutschland"
                    },
                    "billing_address": {
                        "street": "Musterstraße 123",
                        "city": "Musterstadt",
                        "postal_code": "12345",
                        "country": "Deutschland"
                    },
                    "created_at": "2024-01-10T14:20:00",
                    "updated_at": "2024-01-12T09:30:00",
                    "shipping_tracking_id": "TRK123456789",
                    "notes": "Standardversand"
                },
                "ord2024002": {
                    "order_id": "ord2024002",
                    "customer_id": "cust789012",
                    "brand": "heine",
                    "status": "delivered",
                    "items": [
                        {
                            "product_id": "prod002",
                            "product_name": "Heine Radler 12er Pack",
                            "quantity": 1,
                            "unit_price": 18.99,
                            "total_price": 18.99
                        }
                    ],
                    "total_amount": 22.99,
                    "shipping_address": {
                        "street": "Beispielweg 456",
                        "city": "Beispielstadt",
                        "postal_code": "54321",
                        "country": "Deutschland"
                    },
                    "billing_address": {
                        "street": "Beispielweg 456",
                        "city": "Beispielstadt",
                        "postal_code": "54321",
                        "country": "Deutschland"
                    },
                    "created_at": "2024-01-05T16:45:00",
                    "updated_at": "2024-01-08T11:20:00",
                    "shipping_tracking_id": "TRK987654321",
                    "notes": "VIP-Versand"
                }
            },
            "shipping": {
                "TRK123456789": {
                    "tracking_id": "TRK123456789",
                    "order_id": "ord2024001",
                    "brand": "heine",
                    "status": "in_transit",
                    "carrier": "DHL",
                    "estimated_delivery": "2024-01-15T14:00:00",
                    "tracking_url": "https://www.dhl.de/tracking?tracking-id=TRK123456789",
                    "events": [
                        {
                            "timestamp": "2024-01-12T09:30:00",
                            "status": "in_transit",
                            "location": "DHL-Verteilzentrum Hamburg",
                            "description": "Paket ist unterwegs"
                        }
                    ]
                },
                "TRK987654321": {
                    "tracking_id": "TRK987654321",
                    "order_id": "ord2024002",
                    "brand": "heine",
                    "status": "delivered",
                    "carrier": "DHL",
                    "estimated_delivery": "2024-01-08T14:00:00",
                    "actual_delivery": "2024-01-08T11:20:00",
                    "tracking_url": "https://www.dhl.de/tracking?tracking-id=TRK987654321",
                    "events": [
                        {
                            "timestamp": "2024-01-08T11:20:00",
                            "status": "delivered",
                            "location": "Beispielstadt",
                            "description": "Paket erfolgreich zugestellt"
                        }
                    ]
                }
            },
            "products": [
                {
                    "product_id": "prod001",
                    "brand": "heine",
                    "name": "Heine Premium Bier 6er Pack",
                    "description": "6 Flaschen Heine Premium Bier à 0,33l",
                    "category": "bier",
                    "price": 12.99,
                    "currency": "EUR",
                    "in_stock": True,
                    "stock_quantity": 150,
                    "images": ["https://example.com/heine-premium.jpg"],
                    "specifications": {
                        "alcohol_content": "5.0%",
                        "volume": "0.33l",
                        "packaging": "Glasflaschen"
                    }
                },
                {
                    "product_id": "prod002",
                    "brand": "heine",
                    "name": "Heine Radler 12er Pack",
                    "description": "12 Dosen Heine Radler à 0,33l",
                    "category": "radler",
                    "price": 18.99,
                    "currency": "EUR",
                    "in_stock": True,
                    "stock_quantity": 75,
                    "images": ["https://example.com/heine-radler.jpg"],
                    "specifications": {
                        "alcohol_content": "2.5%",
                        "volume": "0.33l",
                        "packaging": "Dosen"
                    }
                }
            ]
        }
    
    async def get_customer_info(self, brand: str, customer_id: str) -> Optional[Customer]:
        """Mock-Implementierung für Kundendaten."""
        customer_data = self._mock_data["customers"].get(customer_id)
        if customer_data and customer_data["brand"] == brand:
            return Customer(**customer_data)
        return None
    
    async def get_order_info(self, brand: str, order_id: str) -> Optional[Order]:
        """Mock-Implementierung für Bestelldaten."""
        order_data = self._mock_data["orders"].get(order_id)
        if order_data and order_data["brand"] == brand:
            return Order(**order_data)
        return None
    
    async def get_shipping_info(self, brand: str, tracking_id: str) -> Optional[ShippingInfo]:
        """Mock-Implementierung für Versanddaten."""
        shipping_data = self._mock_data["shipping"].get(tracking_id)
        if shipping_data and shipping_data["brand"] == brand:
            return ShippingInfo(**shipping_data)
        return None
    
    async def search_products(
        self,
        brand: str,
        query: str,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[Product]:
        """Mock-Implementierung für Produktsuche."""
        products = []
        query_lower = query.lower()
        
        for product_data in self._mock_data["products"]:
            if product_data["brand"] == brand:
                if category and product_data["category"] != category:
                    continue
                
                if (query_lower in product_data["name"].lower() or
                    query_lower in product_data["description"].lower()):
                    products.append(Product(**product_data))
                    
                    if len(products) >= max_results:
                        break
        
        return products


# Globale API-Client-Instanz
api_client = HeineAPIClient()


def get_api_client() -> HeineAPIClient:
    """Gibt die globale API-Client-Instanz zurück."""
    return api_client


def get_mock_api_client() -> MockHeineAPIClient:
    """Gibt eine Mock-API-Client-Instanz zurück."""
    return MockHeineAPIClient() 