"""
Eskalationsmanager für die Übergabe an menschliche Mitarbeiter.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from ..models.escalation_models import (
    EscalationRequest, EscalationTicket, EscalationReason,
    EscalationPriority, EscalationStatus, EscalationRule
)
from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger


class EscalationManager:
    """Verwaltet Eskalationen und Tickets."""
    
    def __init__(self, tickets_dir: str = "./data/escalation_tickets"):
        self.tickets_dir = Path(tickets_dir)
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
        
        self.system_config = get_system_config()
        self.logger = get_logger()
        
        # Eskalationsregeln laden
        self.escalation_rules = self._load_escalation_rules()
    
    def _load_escalation_rules(self) -> Dict[str, List[EscalationRule]]:
        """Lädt Eskalationsregeln für alle Marken."""
        rules = {}
        
        for brand in ["heine", "subbrand1"]:
            brand_config = get_brand_config(brand)
            if brand_config:
                brand_rules = []
                
                # Standard-Regeln basierend auf Marken-Konfiguration
                for rule_config in brand_config.escalation_rules:
                    rule = EscalationRule(
                        rule_id=f"{brand}_{rule_config['trigger']}",
                        brand=brand,
                        name=f"Eskalation bei {rule_config['trigger']}",
                        description=f"Automatische Eskalation bei {rule_config['trigger']}",
                        triggers=[],
                        conditions={"trigger": rule_config['trigger']},
                        actions=["create_ticket", "notify_department"],
                        enabled=True,
                        priority=1 if rule_config['priority'] == 'high' else 2
                    )
                    brand_rules.append(rule)
                
                rules[brand] = brand_rules
        
        return rules
    
    def create_escalation_request(
        self,
        session_id: str,
        brand: str,
        reason: EscalationReason,
        trigger_message: str,
        customer_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        customer_data: Optional[Dict[str, Any]] = None
    ) -> EscalationRequest:
        """Erstellt eine Eskalationsanfrage."""
        # Priorität basierend auf Grund bestimmen
        priority_map = {
            EscalationReason.LOW_CONFIDENCE: EscalationPriority.LOW,
            EscalationReason.REPEATED_QUESTIONS: EscalationPriority.MEDIUM,
            EscalationReason.EMOTIONAL_DISTRESS: EscalationPriority.HIGH,
            EscalationReason.VIP_CUSTOMER: EscalationPriority.HIGH,
            EscalationReason.CRITICAL_ISSUE: EscalationPriority.URGENT,
            EscalationReason.TECHNICAL_PROBLEM: EscalationPriority.MEDIUM,
            EscalationReason.COMPLAINT: EscalationPriority.HIGH,
            EscalationReason.COMPLEX_REQUEST: EscalationPriority.MEDIUM,
            EscalationReason.MANUAL_INTERVENTION: EscalationPriority.HIGH
        }
        
        priority = priority_map.get(reason, EscalationPriority.MEDIUM)
        
        # VIP-Kunden prüfen
        if customer_data and customer_data.get("is_vip", False):
            priority = EscalationPriority.HIGH
            reason = EscalationReason.VIP_CUSTOMER
        
        request = EscalationRequest(
            session_id=session_id,
            brand=brand,
            customer_id=customer_id,
            reason=reason,
            priority=priority,
            trigger_message=trigger_message,
            conversation_history=conversation_history or [],
            customer_data=customer_data or {},
            timestamp=datetime.now()
        )
        
        return request
    
    def create_ticket_from_request(self, request: EscalationRequest) -> EscalationTicket:
        """Erstellt ein Ticket aus einer Eskalationsanfrage."""
        ticket_id = str(uuid.uuid4())
        
        # Abteilung basierend auf Grund und Marken-Konfiguration
        department = self._get_department_for_reason(request.reason, request.brand)
        
        # Konversationszusammenfassung erstellen
        conversation_summary = self._create_conversation_summary(
            request.conversation_history
        )
        
        ticket = EscalationTicket(
            ticket_id=ticket_id,
            session_id=request.session_id,
            brand=request.brand,
            customer_id=request.customer_id,
            reason=request.reason,
            priority=request.priority,
            status=EscalationStatus.PENDING,
            department=department,
            trigger_message=request.trigger_message,
            conversation_summary=conversation_summary,
            customer_data=request.customer_data,
            created_at=request.timestamp,
            updated_at=request.timestamp
        )
        
        # Ticket speichern
        self._save_ticket(ticket)
        
        # Logging
        self.logger.log_escalation(
            brand=request.brand,
            session_id=request.session_id,
            reason=request.reason.value,
            trigger_message=request.trigger_message
        )
        
        return ticket
    
    def _get_department_for_reason(self, reason: EscalationReason, brand: str) -> str:
        """Bestimmt die zuständige Abteilung basierend auf dem Grund."""
        brand_config = get_brand_config(brand)
        
        if brand_config and brand_config.escalation_rules:
            for rule in brand_config.escalation_rules:
                if rule.get("trigger") in reason.value:
                    return rule.get("department", "kundenservice")
        
        # Standard-Zuordnung
        department_map = {
            EscalationReason.LOW_CONFIDENCE: "kundenservice",
            EscalationReason.REPEATED_QUESTIONS: "kundenservice",
            EscalationReason.EMOTIONAL_DISTRESS: "kundenservice",
            EscalationReason.VIP_CUSTOMER: "vip-support",
            EscalationReason.CRITICAL_ISSUE: "management",
            EscalationReason.TECHNICAL_PROBLEM: "technik",
            EscalationReason.COMPLAINT: "beschwerdemanagement",
            EscalationReason.COMPLEX_REQUEST: "kundenservice",
            EscalationReason.MANUAL_INTERVENTION: "kundenservice"
        }
        
        return department_map.get(reason, "kundenservice")
    
    def _create_conversation_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Erstellt eine Zusammenfassung der Konversation."""
        if not conversation_history:
            return "Keine Konversationshistorie verfügbar."
        
        summary_parts = []
        for i, msg in enumerate(conversation_history[-5:], 1):  # Letzte 5 Nachrichten
            role = "Kunde" if msg.get("role") == "user" else "Assistent"
            content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            summary_parts.append(f"{i}. {role}: {content}")
        
        return "\n".join(summary_parts)
    
    def _save_ticket(self, ticket: EscalationTicket):
        """Speichert ein Ticket in einer JSON-Datei."""
        ticket_file = self.tickets_dir / f"{ticket.ticket_id}.json"
        
        with open(ticket_file, 'w', encoding='utf-8') as f:
            json.dump(ticket.dict(), f, ensure_ascii=False, indent=2, default=str)
    
    def get_ticket(self, ticket_id: str) -> Optional[EscalationTicket]:
        """Lädt ein Ticket aus der Datei."""
        ticket_file = self.tickets_dir / f"{ticket_id}.json"
        
        if not ticket_file.exists():
            return None
        
        try:
            with open(ticket_file, 'r', encoding='utf-8') as f:
                ticket_data = json.load(f)
                return EscalationTicket(**ticket_data)
        except Exception as e:
            self.logger.log_error(e, {"ticket_id": ticket_id})
            return None
    
    def update_ticket(self, ticket: EscalationTicket):
        """Aktualisiert ein Ticket."""
        ticket.updated_at = datetime.now()
        self._save_ticket(ticket)
    
    def get_pending_tickets(self, brand: Optional[str] = None) -> List[EscalationTicket]:
        """Gibt alle ausstehenden Tickets zurück."""
        tickets = []
        
        for ticket_file in self.tickets_dir.glob("*.json"):
            try:
                with open(ticket_file, 'r', encoding='utf-8') as f:
                    ticket_data = json.load(f)
                    ticket = EscalationTicket(**ticket_data)
                    
                    if ticket.status == EscalationStatus.PENDING:
                        if brand is None or ticket.brand == brand:
                            tickets.append(ticket)
            except Exception as e:
                self.logger.log_error(e, {"ticket_file": str(ticket_file)})
        
        # Nach Priorität und Erstellungszeit sortieren
        tickets.sort(key=lambda t: (t.priority.value, t.created_at))
        
        return tickets
    
    def assign_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """Weist ein Ticket einem Mitarbeiter zu."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False
        
        ticket.assign_to(agent_id)
        self.update_ticket(ticket)
        
        self.logger.logger.info(
            f"Ticket {ticket_id} an {agent_id} zugewiesen"
        )
        
        return True
    
    def resolve_ticket(self, ticket_id: str, resolution_notes: str = "") -> bool:
        """Markiert ein Ticket als gelöst."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False
        
        ticket.resolve(resolution_notes)
        self.update_ticket(ticket)
        
        self.logger.logger.info(
            f"Ticket {ticket_id} als gelöst markiert"
        )
        
        return True
    
    def get_escalation_metrics(self, brand: str, period: str = "daily") -> Dict[str, Any]:
        """Berechnet Metriken für Eskalationen."""
        tickets = []
        
        # Alle Tickets für die Marke laden
        for ticket_file in self.tickets_dir.glob("*.json"):
            try:
                with open(ticket_file, 'r', encoding='utf-8') as f:
                    ticket_data = json.load(f)
                    ticket = EscalationTicket(**ticket_data)
                    
                    if ticket.brand == brand:
                        tickets.append(ticket)
            except Exception:
                continue
        
        # Metriken berechnen
        total_tickets = len(tickets)
        resolved_tickets = len([t for t in tickets if t.status == EscalationStatus.RESOLVED])
        
        escalation_by_reason = {}
        escalation_by_priority = {}
        
        for ticket in tickets:
            reason = ticket.reason.value
            priority = ticket.priority.value
            
            escalation_by_reason[reason] = escalation_by_reason.get(reason, 0) + 1
            escalation_by_priority[priority] = escalation_by_priority.get(priority, 0) + 1
        
        # Durchschnittliche Lösungszeit
        resolution_times = []
        for ticket in tickets:
            if ticket.resolved_at and ticket.created_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # Stunden
                resolution_times.append(resolution_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        return {
            "brand": brand,
            "period": period,
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "escalation_rate": resolved_tickets / total_tickets if total_tickets > 0 else 0,
            "avg_resolution_time": avg_resolution_time,
            "escalation_by_reason": escalation_by_reason,
            "escalation_by_priority": escalation_by_priority
        }
    
    def cleanup_old_tickets(self, days: int = 30):
        """Löscht alte Tickets."""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for ticket_file in self.tickets_dir.glob("*.json"):
            try:
                with open(ticket_file, 'r', encoding='utf-8') as f:
                    ticket_data = json.load(f)
                    ticket = EscalationTicket(**ticket_data)
                    
                    if ticket.created_at < cutoff_date:
                        ticket_file.unlink()
                        deleted_count += 1
            except Exception:
                continue
        
        self.logger.logger.info(f"{deleted_count} alte Tickets gelöscht")


# Globale Eskalationsmanager-Instanz
escalation_manager = EscalationManager()


def get_escalation_manager() -> EscalationManager:
    """Gibt die globale Eskalationsmanager-Instanz zurück."""
    return escalation_manager 