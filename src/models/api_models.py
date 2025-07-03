"""
Datenmodelle für API-Interaktionen.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Status einer Bestellung."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ShippingStatus(str, Enum):
    """Status eines Versands."""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class Customer(BaseModel):
    """Kundendaten."""
    customer_id: str = Field(..., description="Eindeutige Kunden-ID")
    brand: str = Field(..., description="Marke/Mandant")
    first_name: str = Field(..., description="Vorname")
    last_name: str = Field(..., description="Nachname")
    email: str = Field(..., description="E-Mail-Adresse")
    phone: Optional[str] = Field(None, description="Telefonnummer")
    address: Optional[Dict[str, str]] = Field(None, description="Adresse")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    last_order_date: Optional[datetime] = Field(None, description="Datum der letzten Bestellung")
    total_orders: int = Field(0, description="Anzahl der Bestellungen")
    total_spent: float = Field(0.0, description="Gesamtausgaben")
    is_vip: bool = Field(False, description="VIP-Kunde")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderItem(BaseModel):
    """Einzelner Artikel in einer Bestellung."""
    product_id: str = Field(..., description="Produkt-ID")
    product_name: str = Field(..., description="Produktname")
    quantity: int = Field(..., description="Menge")
    unit_price: float = Field(..., description="Einzelpreis")
    total_price: float = Field(..., description="Gesamtpreis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")


class Order(BaseModel):
    """Bestelldaten."""
    order_id: str = Field(..., description="Eindeutige Bestell-ID")
    customer_id: str = Field(..., description="Kunden-ID")
    brand: str = Field(..., description="Marke/Mandant")
    status: OrderStatus = Field(..., description="Bestellstatus")
    items: List[OrderItem] = Field(default_factory=list, description="Bestellte Artikel")
    total_amount: float = Field(..., description="Gesamtbetrag")
    shipping_address: Dict[str, str] = Field(..., description="Lieferadresse")
    billing_address: Dict[str, str] = Field(..., description="Rechnungsadresse")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime = Field(..., description="Letzte Aktualisierung")
    shipping_tracking_id: Optional[str] = Field(None, description="Versand-Tracking-ID")
    notes: Optional[str] = Field(None, description="Notizen")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ShippingInfo(BaseModel):
    """Versandinformationen."""
    tracking_id: str = Field(..., description="Tracking-ID")
    order_id: str = Field(..., description="Bestell-ID")
    brand: str = Field(..., description="Marke/Mandant")
    status: ShippingStatus = Field(..., description="Versandstatus")
    carrier: str = Field(..., description="Versandunternehmen")
    estimated_delivery: Optional[datetime] = Field(None, description="Geschätzte Lieferung")
    actual_delivery: Optional[datetime] = Field(None, description="Tatsächliche Lieferung")
    tracking_url: Optional[str] = Field(None, description="Tracking-URL")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Versand-Events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Product(BaseModel):
    """Produktdaten."""
    product_id: str = Field(..., description="Eindeutige Produkt-ID")
    brand: str = Field(..., description="Marke/Mandant")
    name: str = Field(..., description="Produktname")
    description: str = Field(..., description="Produktbeschreibung")
    category: str = Field(..., description="Kategorie")
    price: float = Field(..., description="Preis")
    currency: str = Field("EUR", description="Währung")
    in_stock: bool = Field(True, description="Verfügbar")
    stock_quantity: int = Field(0, description="Lagerbestand")
    images: List[str] = Field(default_factory=list, description="Produktbilder")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Spezifikationen")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")


class APIRequest(BaseModel):
    """Basis für API-Anfragen."""
    brand: str = Field(..., description="Marke/Mandant")
    request_id: str = Field(..., description="Eindeutige Anfrage-ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Zeitstempel")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIResponse(BaseModel):
    """Basis für API-Antworten."""
    request_id: str = Field(..., description="Anfrage-ID")
    success: bool = Field(..., description="Erfolg der Anfrage")
    data: Optional[Dict[str, Any]] = Field(None, description="Antwortdaten")
    error: Optional[str] = Field(None, description="Fehlermeldung")
    timestamp: datetime = Field(default_factory=datetime.now, description="Zeitstempel")
    response_time: float = Field(..., description="Antwortzeit in Sekunden")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomerInfoRequest(APIRequest):
    """Anfrage für Kundendaten."""
    customer_id: str = Field(..., description="Kunden-ID")


class OrderInfoRequest(APIRequest):
    """Anfrage für Bestelldaten."""
    order_id: str = Field(..., description="Bestell-ID")


class ShippingInfoRequest(APIRequest):
    """Anfrage für Versanddaten."""
    tracking_id: str = Field(..., description="Tracking-ID")


class ProductSearchRequest(APIRequest):
    """Anfrage für Produktsuche."""
    query: str = Field(..., description="Suchanfrage")
    category: Optional[str] = Field(None, description="Kategorie")
    max_results: int = Field(10, description="Maximale Anzahl Ergebnisse") 