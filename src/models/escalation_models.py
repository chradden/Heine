"""
Datenmodelle für Eskalationslogik.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class EscalationReason(str, Enum):
    """Gründe für Eskalation."""
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_QUESTIONS = "repeated_questions"
    EMOTIONAL_DISTRESS = "emotional_distress"
    VIP_CUSTOMER = "vip_customer"
    CRITICAL_ISSUE = "critical_issue"
    TECHNICAL_PROBLEM = "technical_problem"
    COMPLAINT = "complaint"
    COMPLEX_REQUEST = "complex_request"
    MANUAL_INTERVENTION = "manual_intervention"


class EscalationPriority(str, Enum):
    """Prioritäten für Eskalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EscalationStatus(str, Enum):
    """Status einer Eskalation."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationTrigger(BaseModel):
    """Trigger für eine Eskalation."""
    reason: EscalationReason = Field(..., description="Grund für Eskalation")
    priority: EscalationPriority = Field(..., description="Priorität")
    confidence_threshold: float = Field(0.7, description="Konfidenz-Schwellwert")
    keywords: List[str] = Field(default_factory=list, description="Trigger-Schlüsselwörter")
    department: str = Field(..., description="Zuständige Abteilung")
    auto_escalate: bool = Field(True, description="Automatische Eskalation")
    message_template: str = Field(..., description="Nachrichten-Template")


class EscalationRequest(BaseModel):
    """Eskalationsanfrage."""
    session_id: str = Field(..., description="Session-ID")
    brand: str = Field(..., description="Marke/Mandant")
    customer_id: Optional[str] = Field(None, description="Kunden-ID")
    reason: EscalationReason = Field(..., description="Grund für Eskalation")
    priority: EscalationPriority = Field(..., description="Priorität")
    trigger_message: str = Field(..., description="Auslösende Nachricht")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Konversationsverlauf")
    customer_data: Optional[Dict[str, Any]] = Field(None, description="Kundendaten")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    timestamp: datetime = Field(default_factory=datetime.now, description="Zeitstempel")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EscalationTicket(BaseModel):
    """Eskalations-Ticket."""
    ticket_id: str = Field(..., description="Eindeutige Ticket-ID")
    session_id: str = Field(..., description="Session-ID")
    brand: str = Field(..., description="Marke/Mandant")
    customer_id: Optional[str] = Field(None, description="Kunden-ID")
    reason: EscalationReason = Field(..., description="Grund für Eskalation")
    priority: EscalationPriority = Field(..., description="Priorität")
    status: EscalationStatus = Field(EscalationStatus.PENDING, description="Status")
    assigned_to: Optional[str] = Field(None, description="Zugewiesener Mitarbeiter")
    department: str = Field(..., description="Zuständige Abteilung")
    trigger_message: str = Field(..., description="Auslösende Nachricht")
    conversation_summary: str = Field(..., description="Zusammenfassung der Konversation")
    customer_data: Optional[Dict[str, Any]] = Field(None, description="Kundendaten")
    notes: List[str] = Field(default_factory=list, description="Notizen")
    created_at: datetime = Field(default_factory=datetime.now, description="Erstellungszeitpunkt")
    updated_at: datetime = Field(default_factory=datetime.now, description="Letzte Aktualisierung")
    resolved_at: Optional[datetime] = Field(None, description="Lösungszeitpunkt")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def assign_to(self, agent_id: str):
        """Weist das Ticket einem Mitarbeiter zu."""
        self.assigned_to = agent_id
        self.status = EscalationStatus.ASSIGNED
        self.updated_at = datetime.now()
    
    def start_processing(self):
        """Markiert das Ticket als in Bearbeitung."""
        self.status = EscalationStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def resolve(self, resolution_notes: str = ""):
        """Markiert das Ticket als gelöst."""
        self.status = EscalationStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()
        if resolution_notes:
            self.notes.append(f"Lösung: {resolution_notes}")
    
    def close(self):
        """Schließt das Ticket."""
        self.status = EscalationStatus.CLOSED
        self.updated_at = datetime.now()


class EscalationRule(BaseModel):
    """Regel für automatische Eskalation."""
    rule_id: str = Field(..., description="Eindeutige Regel-ID")
    brand: str = Field(..., description="Marke/Mandant")
    name: str = Field(..., description="Regelname")
    description: str = Field(..., description="Regelbeschreibung")
    triggers: List[EscalationTrigger] = Field(default_factory=list, description="Trigger")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Bedingungen")
    actions: List[str] = Field(default_factory=list, description="Aktionen")
    enabled: bool = Field(True, description="Regel aktiv")
    priority: int = Field(0, description="Priorität der Regel")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")


class EscalationMetrics(BaseModel):
    """Metriken für Eskalationen."""
    brand: str = Field(..., description="Marke/Mandant")
    period: str = Field(..., description="Zeitraum")
    total_conversations: int = Field(0, description="Gesamte Konversationen")
    total_escalations: int = Field(0, description="Gesamte Eskalationen")
    escalation_rate: float = Field(0.0, description="Eskalationsrate")
    avg_resolution_time: float = Field(0.0, description="Durchschnittliche Lösungszeit")
    escalation_by_reason: Dict[str, int] = Field(default_factory=dict, description="Eskalationen nach Grund")
    escalation_by_priority: Dict[str, int] = Field(default_factory=dict, description="Eskalationen nach Priorität")
    customer_satisfaction: float = Field(0.0, description="Kundenzufriedenheit")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten") 