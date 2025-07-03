"""
Datenmodelle für Chat-Interaktionen.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Rollen in einer Konversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Typen von Nachrichten."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    ESCALATION = "escalation"


class ChatMessage(BaseModel):
    """Einzelne Chat-Nachricht."""
    id: str = Field(..., description="Eindeutige ID der Nachricht")
    session_id: str = Field(..., description="Session-ID")
    brand: str = Field(..., description="Marke/Mandant")
    role: MessageRole = Field(..., description="Rolle des Absenders")
    message_type: MessageType = Field(MessageType.TEXT, description="Typ der Nachricht")
    content: str = Field(..., description="Inhalt der Nachricht")
    timestamp: datetime = Field(default_factory=datetime.now, description="Zeitstempel")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """Chat-Session mit Verlauf."""
    session_id: str = Field(..., description="Eindeutige Session-ID")
    brand: str = Field(..., description="Marke/Mandant")
    customer_id: Optional[str] = Field(None, description="Kunden-ID falls bekannt")
    created_at: datetime = Field(default_factory=datetime.now, description="Erstellungszeitpunkt")
    last_activity: datetime = Field(default_factory=datetime.now, description="Letzte Aktivität")
    messages: List[ChatMessage] = Field(default_factory=list, description="Nachrichtenverlauf")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session-Metadaten")
    escalated: bool = Field(False, description="Ob Session eskaliert wurde")
    escalation_reason: Optional[str] = Field(None, description="Grund für Eskalation")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_message(self, message: ChatMessage):
        """Fügt eine Nachricht zur Session hinzu."""
        self.messages.append(message)
        self.last_activity = datetime.now()
    
    def get_context_messages(self, max_messages: int = 10) -> List[ChatMessage]:
        """Gibt die letzten Nachrichten für Kontext zurück."""
        return self.messages[-max_messages:] if self.messages else []
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Prüft ob die Session noch aktiv ist."""
        timeout = datetime.now() - self.last_activity
        return timeout.total_seconds() < (timeout_minutes * 60)


class ChatRequest(BaseModel):
    """Anfrage für eine Chat-Antwort."""
    brand: str = Field(..., description="Marke/Mandant")
    message: str = Field(..., description="Benutzernachricht")
    session_id: str = Field(..., description="Session-ID")
    customer_id: Optional[str] = Field(None, description="Kunden-ID falls bekannt")
    context_messages: Optional[List[ChatMessage]] = Field(None, description="Kontext-Nachrichten")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")


class ChatResponse(BaseModel):
    """Antwort auf eine Chat-Anfrage."""
    session_id: str = Field(..., description="Session-ID")
    message: str = Field(..., description="AI-Antwort")
    confidence: float = Field(..., description="Konfidenz der Antwort (0-1)")
    escalated: bool = Field(False, description="Ob eskaliert wurde")
    escalation_reason: Optional[str] = Field(None, description="Grund für Eskalation")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Quellen der Antwort")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    response_time: float = Field(..., description="Antwortzeit in Sekunden")


class ConversationHistory(BaseModel):
    """Konversationsverlauf für eine Session."""
    session_id: str = Field(..., description="Session-ID")
    brand: str = Field(..., description="Marke/Mandant")
    messages: List[ChatMessage] = Field(default_factory=list, description="Nachrichtenverlauf")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    last_activity: datetime = Field(..., description="Letzte Aktivität")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 