"""
E-Mail-Interface für die Verarbeitung von E-Mail-Anfragen.
"""
import re
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..agents.brand_agent import get_agent
from ..models.chat_models import ChatMessage, ChatResponse, MessageRole
from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger
from ..agents.escalation_manager import get_escalation_manager


class EmailProcessor:
    """Verarbeitet eingehende E-Mails."""
    
    def __init__(self):
        self.system_config = get_system_config()
        self.logger = get_logger()
        self.escalation_manager = get_escalation_manager()
    
    def extract_brand_from_email(self, to_email: str) -> Optional[str]:
        """Extrahiert die Marke aus der E-Mail-Adresse."""
        # Mapping von E-Mail-Adressen zu Marken
        email_brand_mapping = {
            "support@heine.com": "heine",
            "support@subbrand1.heine.com": "subbrand1",
            "kundenservice@heine.com": "heine",
            "info@heine.com": "heine"
        }
        
        return email_brand_mapping.get(to_email.lower())
    
    def extract_customer_info(self, email_content: str, from_email: str) -> Dict[str, Any]:
        """Extrahiert Kundeninformationen aus der E-Mail."""
        customer_info = {
            "email": from_email,
            "name": None,
            "phone": None,
            "customer_id": None,
            "order_id": None
        }
        
        # Namen aus E-Mail-Adresse extrahieren
        if "@" in from_email:
            name_part = from_email.split("@")[0]
            if "." in name_part:
                name_parts = name_part.split(".")
                customer_info["name"] = " ".join([part.capitalize() for part in name_parts])
        
        # Telefonnummer suchen
        phone_pattern = r'(\+49|0)[0-9\s\-\(\)]{8,}'
        phone_match = re.search(phone_pattern, email_content)
        if phone_match:
            customer_info["phone"] = phone_match.group(0)
        
        # Kunden-ID suchen
        customer_id_pattern = r'cust[0-9]{6,}'
        customer_id_match = re.search(customer_id_pattern, email_content, re.IGNORECASE)
        if customer_id_match:
            customer_info["customer_id"] = customer_id_match.group(0)
        
        # Bestell-ID suchen
        order_id_pattern = r'ord[0-9]{8,}'
        order_id_match = re.search(order_id_pattern, email_content, re.IGNORECASE)
        if order_id_match:
            customer_info["order_id"] = order_id_match.group(0)
        
        return customer_info
    
    def format_email_response(
        self,
        ai_response: str,
        brand: str,
        original_subject: str,
        customer_name: Optional[str] = None
    ) -> str:
        """Formatiert die E-Mail-Antwort."""
        brand_config = get_brand_config(brand)
        if not brand_config:
            brand_config = get_brand_config("heine")  # Fallback
        
        # E-Mail-Template
        email_template = f"""
{ai_response}

---
Mit freundlichen Grüßen
Ihr {brand_config.name} Team

{brand_config.support_email}
www.{brand_config.name.lower()}.com

Diese E-Mail wurde automatisch generiert. Bei weiteren Fragen kontaktieren Sie uns gerne.
        """
        
        return email_template.strip()
    
    async def process_email(
        self,
        email_content: str,
        from_email: str,
        to_email: str,
        subject: str,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verarbeitet eine eingehende E-Mail."""
        try:
            # Marke bestimmen
            if not brand:
                brand = self.extract_brand_from_email(to_email)
            
            if not brand:
                return {
                    "success": False,
                    "error": "Marke konnte nicht bestimmt werden",
                    "brand": None
                }
            
            # Kundeninformationen extrahieren
            customer_info = self.extract_customer_info(email_content, from_email)
            
            # E-Mail-Inhalt bereinigen
            clean_content = self._clean_email_content(email_content)
            
            # Session-ID generieren
            session_id = str(uuid.uuid4())
            
            # Agent für die Marke holen
            agent = get_agent(brand, use_mock_api=True)
            
            # E-Mail verarbeiten
            response = await agent.process_message(
                message=clean_content,
                session_id=session_id,
                customer_id=customer_info.get("customer_id")
            )
            
            # E-Mail-Antwort formatieren
            formatted_response = self.format_email_response(
                response.message,
                brand,
                subject,
                customer_info.get("name")
            )
            
            # Eskalation verarbeiten
            escalation_info = None
            if response.escalated:
                escalation_info = await self._handle_email_escalation(
                    session_id, brand, clean_content, response, customer_info
                )
            
            result = {
                "success": True,
                "brand": brand,
                "session_id": session_id,
                "response": formatted_response,
                "confidence": response.confidence,
                "escalated": response.escalated,
                "escalation_reason": response.escalation_reason,
                "customer_info": customer_info,
                "escalation_info": escalation_info
            }
            
            # Logging
            self.logger.logger.info(
                f"E-Mail verarbeitet: {from_email} -> {brand}, "
                f"Session: {session_id}, Eskaliert: {response.escalated}"
            )
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {
                "from_email": from_email,
                "to_email": to_email,
                "subject": subject,
                "brand": brand
            })
            
            return {
                "success": False,
                "error": str(e),
                "brand": brand
            }
    
    def _clean_email_content(self, email_content: str) -> str:
        """Bereinigt den E-Mail-Inhalt."""
        # E-Mail-Header entfernen
        if "From:" in email_content:
            parts = email_content.split("From:")
            if len(parts) > 1:
                email_content = parts[0]
        
        # Signaturen entfernen
        signature_patterns = [
            r"--\s*\n.*",
            r"Mit freundlichen Grüßen.*",
            r"Best regards.*",
            r"Kind regards.*"
        ]
        
        for pattern in signature_patterns:
            email_content = re.sub(pattern, "", email_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Mehrfache Leerzeichen entfernen
        email_content = re.sub(r'\s+', ' ', email_content)
        
        return email_content.strip()
    
    async def _handle_email_escalation(
        self,
        session_id: str,
        brand: str,
        email_content: str,
        response: ChatResponse,
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Behandelt eine E-Mail-Eskalation."""
        from ..models.escalation_models import EscalationReason
        
        # Eskalationsgrund bestimmen
        reason_map = {
            "low_confidence": EscalationReason.LOW_CONFIDENCE,
            "complaint": EscalationReason.COMPLAINT,
            "emotional_distress": EscalationReason.EMOTIONAL_DISTRESS,
            "manual_intervention": EscalationReason.MANUAL_INTERVENTION,
            "technical_problem": EscalationReason.TECHNICAL_PROBLEM
        }
        
        reason = reason_map.get(response.escalation_reason, EscalationReason.LOW_CONFIDENCE)
        
        # Konversationshistorie erstellen
        conversation_history = [
            {
                "role": "user",
                "content": email_content,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": response.message,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Eskalationsanfrage erstellen
        escalation_request = self.escalation_manager.create_escalation_request(
            session_id=session_id,
            brand=brand,
            reason=reason,
            trigger_message=email_content,
            customer_id=customer_info.get("customer_id"),
            conversation_history=conversation_history,
            customer_data=customer_info
        )
        
        # Ticket erstellen
        ticket = self.escalation_manager.create_ticket_from_request(escalation_request)
        
        return {
            "ticket_id": ticket.ticket_id,
            "reason": reason.value,
            "priority": ticket.priority.value,
            "department": ticket.department
        }
    
    def create_reply_email(
        self,
        to_email: str,
        subject: str,
        response_content: str,
        brand: str,
        original_message_id: Optional[str] = None
    ) -> MIMEMultipart:
        """Erstellt eine Antwort-E-Mail."""
        brand_config = get_brand_config(brand)
        if not brand_config:
            brand_config = get_brand_config("heine")  # Fallback
        
        # E-Mail erstellen
        msg = MIMEMultipart()
        msg['From'] = brand_config.support_email
        msg['To'] = to_email
        msg['Subject'] = f"Re: {subject}"
        
        if original_message_id:
            msg['In-Reply-To'] = original_message_id
            msg['References'] = original_message_id
        
        # E-Mail-Text hinzufügen
        text_part = MIMEText(response_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        return msg


class EmailInterface:
    """E-Mail-Interface für das Heine-System."""
    
    def __init__(self):
        self.email_processor = EmailProcessor()
        self.logger = get_logger()
    
    async def process_incoming_email(
        self,
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verarbeitet eine eingehende E-Mail."""
        try:
            # E-Mail-Daten extrahieren
            email_content = email_data.get("content", "")
            from_email = email_data.get("from_email", "")
            to_email = email_data.get("to_email", "")
            subject = email_data.get("subject", "")
            brand = email_data.get("brand")
            
            # E-Mail verarbeiten
            result = await self.email_processor.process_email(
                email_content=email_content,
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                brand=brand
            )
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {"email_data": email_data})
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_auto_reply(
        self,
        to_email: str,
        subject: str,
        response_content: str,
        brand: str
    ) -> Dict[str, Any]:
        """Erstellt eine automatische Antwort."""
        try:
            # Antwort-E-Mail erstellen
            reply_email = self.email_processor.create_reply_email(
                to_email=to_email,
                subject=subject,
                response_content=response_content,
                brand=brand
            )
            
            return {
                "success": True,
                "from_email": reply_email['From'],
                "to_email": reply_email['To'],
                "subject": reply_email['Subject'],
                "content": reply_email.as_string()
            }
            
        except Exception as e:
            self.logger.log_error(e, {
                "to_email": to_email,
                "subject": subject,
                "brand": brand
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_email_statistics(self, brand: str, period: str = "daily") -> Dict[str, Any]:
        """Gibt E-Mail-Statistiken zurück."""
        # Hier könnten E-Mail-Metriken implementiert werden
        return {
            "brand": brand,
            "period": period,
            "total_emails": 0,
            "processed_emails": 0,
            "escalated_emails": 0,
            "avg_response_time": 0.0
        }


# Globale E-Mail-Interface-Instanz
email_interface = EmailInterface()


def get_email_interface() -> EmailInterface:
    """Gibt die globale E-Mail-Interface-Instanz zurück."""
    return email_interface 