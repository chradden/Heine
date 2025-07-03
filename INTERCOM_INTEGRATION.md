# 🔗 Intercom-Integration für Heine AI-System

## Übersicht

Die Intercom-Integration ermöglicht es dem Heine AI-System, direkt mit dem Intercom-Ticketsystem zu kommunizieren. Dadurch können Kundenanfragen automatisch verarbeitet und bei Bedarf an menschliche Mitarbeiter weitergeleitet werden.

---

## Funktionen der Intercom-Integration

### 🤖 Automatische Ticket-Verarbeitung
- **Eingehende Tickets** werden automatisch vom AI-System analysiert
- **Intelligente Antworten** werden basierend auf Heine-Wissen generiert
- **Automatische Kategorisierung** von Tickets nach Thema und Priorität
- **Eskalation** komplexer Anfragen an menschliche Mitarbeiter

### 📊 Ticket-Management
- **Status-Updates** werden automatisch gesetzt (Offen → In Bearbeitung → Geschlossen)
- **Prioritätsbestimmung** basierend auf Schlüsselwörtern und Kundenhistorie
- **Tagging** von Tickets für bessere Organisation
- **Automatische Follow-ups** bei ungelösten Tickets

### 🔄 Bidirektionale Kommunikation
- **Chat-Integration** zwischen AI-System und Intercom
- **E-Mail-Integration** für automatische Antworten
- **Webhook-Support** für Echtzeit-Updates
- **API-Synchronisation** für Datenabgleich

---

## Technische Implementation

### Intercom API-Client

```python
# src/integrations/intercom_client.py
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

class IntercomClient:
    def __init__(self, access_token: str, workspace_id: str):
        self.access_token = access_token
        self.workspace_id = workspace_id
        self.base_url = "https://api.intercom.io"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def get_tickets(self, status: str = "open") -> List[Dict]:
        """Holt alle Tickets mit einem bestimmten Status."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tickets"
            params = {"status": status}
            
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tickets", [])
                else:
                    raise Exception(f"Fehler beim Abrufen der Tickets: {response.status}")
    
    async def create_ticket(self, ticket_data: Dict) -> Dict:
        """Erstellt ein neues Ticket."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tickets"
            
            async with session.post(url, headers=self.headers, json=ticket_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Fehler beim Erstellen des Tickets: {response.status}")
    
    async def update_ticket(self, ticket_id: str, updates: Dict) -> Dict:
        """Aktualisiert ein bestehendes Ticket."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tickets/{ticket_id}"
            
            async with session.put(url, headers=self.headers, json=updates) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Fehler beim Aktualisieren des Tickets: {response.status}")
    
    async def add_conversation_part(self, ticket_id: str, message: str, author_type: str = "admin") -> Dict:
        """Fügt eine Nachricht zu einem Ticket hinzu."""
        conversation_data = {
            "body": message,
            "author": {
                "type": author_type
            }
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tickets/{ticket_id}/conversation_parts"
            
            async with session.post(url, headers=self.headers, json=conversation_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Fehler beim Hinzufügen der Nachricht: {response.status}")
    
    async def assign_ticket(self, ticket_id: str, admin_id: str) -> Dict:
        """Weist ein Ticket einem Admin zu."""
        assignment_data = {
            "admin_id": admin_id
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/tickets/{ticket_id}/assign"
            
            async with session.post(url, headers=self.headers, json=assignment_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Fehler beim Zuweisen des Tickets: {response.status}")
```

### AI-Integration mit Intercom

```python
# src/integrations/intercom_ai_handler.py
import asyncio
from typing import Dict, List
from src.agents.customer_service_agent import CustomerServiceAgent
from src.integrations.intercom_client import IntercomClient

class IntercomAIHandler:
    def __init__(self, intercom_client: IntercomClient, ai_agent: CustomerServiceAgent):
        self.intercom = intercom_client
        self.ai_agent = ai_agent
        self.brand_config = ai_agent.brand_config
    
    async def process_new_tickets(self):
        """Verarbeitet alle neuen Tickets automatisch."""
        try:
            # Neue Tickets abrufen
            new_tickets = await self.intercom.get_tickets(status="open")
            
            for ticket in new_tickets:
                await self.process_single_ticket(ticket)
                
        except Exception as e:
            logger.error(f"Fehler bei der Ticket-Verarbeitung: {e}")
    
    async def process_single_ticket(self, ticket: Dict):
        """Verarbeitet ein einzelnes Ticket."""
        ticket_id = ticket["id"]
        subject = ticket.get("subject", "")
        body = ticket.get("body", "")
        
        # Vollständige Nachricht zusammenstellen
        full_message = f"Betreff: {subject}\n\nNachricht: {body}"
        
        try:
            # AI-Antwort generieren
            ai_response = await self.ai_agent.process_message(
                message=full_message,
                session_id=f"intercom_{ticket_id}"
            )
            
            # Eskalation prüfen
            if ai_response.escalation_required:
                await self.escalate_ticket(ticket_id, ai_response.content)
            else:
                # Automatische Antwort hinzufügen
                await self.intercom.add_conversation_part(
                    ticket_id=ticket_id,
                    message=ai_response.content,
                    author_type="admin"
                )
                
                # Ticket als beantwortet markieren
                await self.intercom.update_ticket(ticket_id, {
                    "status": "answered"
                })
                
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Ticket {ticket_id}: {e}")
            # Bei Fehlern Ticket eskalieren
            await self.escalate_ticket(ticket_id, "Automatische Verarbeitung fehlgeschlagen")
    
    async def escalate_ticket(self, ticket_id: str, reason: str):
        """Eskaliert ein Ticket an einen menschlichen Mitarbeiter."""
        try:
            # Ticket als eskalationsbedürftig markieren
            await self.intercom.update_ticket(ticket_id, {
                "status": "pending",
                "tags": ["ai_escalation", "human_required"]
            })
            
            # Eskalationsnotiz hinzufügen
            escalation_message = f"⚠️ **Automatische Eskalation**\n\nGrund: {reason}\n\nDieses Ticket wurde automatisch an einen menschlichen Mitarbeiter weitergeleitet."
            
            await self.intercom.add_conversation_part(
                ticket_id=ticket_id,
                message=escalation_message,
                author_type="admin"
            )
            
            # Benachrichtigung an Support-Team senden
            await self.notify_support_team(ticket_id, reason)
            
        except Exception as e:
            logger.error(f"Fehler bei der Eskalation von Ticket {ticket_id}: {e}")
    
    async def notify_support_team(self, ticket_id: str, reason: str):
        """Benachrichtigt das Support-Team über eine Eskalation."""
        # Hier könnte eine E-Mail-Benachrichtigung oder Slack-Integration implementiert werden
        notification = {
            "ticket_id": ticket_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        
        # Beispiel: Slack-Webhook oder E-Mail-Service
        logger.info(f"Support-Team benachrichtigt: {notification}")
    
    async def handle_webhook(self, webhook_data: Dict):
        """Verarbeitet Intercom-Webhooks für Echtzeit-Updates."""
        event_type = webhook_data.get("type")
        
        if event_type == "ticket.created":
            ticket = webhook_data.get("data", {})
            await self.process_single_ticket(ticket)
        
        elif event_type == "ticket.updated":
            # Ticket-Updates verarbeiten
            ticket = webhook_data.get("data", {})
            await self.handle_ticket_update(ticket)
    
    async def handle_ticket_update(self, ticket: Dict):
        """Verarbeitet Ticket-Updates."""
        ticket_id = ticket["id"]
        status = ticket.get("status")
        
        if status == "reopened":
            # Ticket wurde wiedereröffnet - erneut verarbeiten
            await self.process_single_ticket(ticket)
```

### Webhook-Handler für Echtzeit-Updates

```python
# src/channels/intercom_webhook.py
from fastapi import APIRouter, Request, HTTPException
from src.integrations.intercom_ai_handler import IntercomAIHandler
import hmac
import hashlib

router = APIRouter()

@router.post("/webhook/intercom")
async def intercom_webhook(request: Request):
    """Empfängt Intercom-Webhooks für Echtzeit-Updates."""
    
    # Webhook-Signatur verifizieren
    signature = request.headers.get("X-Intercom-Signature")
    if not verify_webhook_signature(request.body(), signature):
        raise HTTPException(status_code=401, detail="Ungültige Signatur")
    
    # Webhook-Daten verarbeiten
    webhook_data = await request.json()
    
    # AI-Handler initialisieren
    ai_handler = IntercomAIHandler(
        intercom_client=intercom_client,
        ai_agent=customer_service_agent
    )
    
    # Webhook verarbeiten
    await ai_handler.handle_webhook(webhook_data)
    
    return {"status": "success"}

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verifiziert die Intercom-Webhook-Signatur."""
    secret = os.getenv("INTERCOM_WEBHOOK_SECRET")
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

---

## Konfiguration

### Umgebungsvariablen

```bash
# Intercom API-Konfiguration
INTERCOM_ACCESS_TOKEN=your-access-token-here
INTERCOM_WORKSPACE_ID=your-workspace-id
INTERCOM_WEBHOOK_SECRET=your-webhook-secret

# AI-Integration
AI_ESCALATION_THRESHOLD=0.7
AI_MAX_RESPONSE_TIME=30
AUTO_ASSIGN_TICKETS=true
```

### Konfigurationsdatei

```yaml
# config/intercom.yaml
intercom:
  api:
    access_token: ${INTERCOM_ACCESS_TOKEN}
    workspace_id: ${INTERCOM_WORKSPACE_ID}
    webhook_secret: ${INTERCOM_WEBHOOK_SECRET}
  
  ai_integration:
    auto_process_tickets: true
    escalation_threshold: 0.7
    max_response_time: 30
    auto_assign: true
    
  ticket_categories:
    - name: "Bestellungen"
      keywords: ["bestellung", "order", "versand", "shipping"]
      priority: "medium"
    
    - name: "Reklamationen"
      keywords: ["reklamation", "beschwerde", "complaint", "problem"]
      priority: "high"
    
    - name: "Allgemeine Anfragen"
      keywords: ["frage", "info", "information"]
      priority: "low"
  
  escalation_rules:
    - condition: "contains_complaint_keywords"
      action: "escalate_to_senior_support"
    
    - condition: "customer_vip"
      action: "escalate_to_account_manager"
    
    - condition: "technical_issue"
      action: "escalate_to_tech_support"
```

---

## Installation & Setup

### 1. Intercom API-Zugriff einrichten

1. **Intercom Admin-Panel öffnen**
2. **API-Keys generieren** unter Settings → Integrations → API Keys
3. **Workspace ID notieren** aus den Account-Einstellungen
4. **Webhook-Secret erstellen** für sichere Kommunikation

### 2. Abhängigkeiten installieren

```bash
pip install aiohttp
pip install cryptography
```

### 3. Konfiguration testen

```python
# test_intercom_connection.py
import asyncio
from src.integrations.intercom_client import IntercomClient

async def test_connection():
    client = IntercomClient(
        access_token="your-token",
        workspace_id="your-workspace"
    )
    
    try:
        tickets = await client.get_tickets()
        print(f"Verbindung erfolgreich! {len(tickets)} Tickets gefunden.")
    except Exception as e:
        print(f"Verbindungsfehler: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

---

## Workflow-Beispiele

### Automatische Ticket-Verarbeitung

1. **Kunde erstellt Ticket** in Intercom
2. **Webhook wird ausgelöst** und an Heine AI-System gesendet
3. **AI analysiert Ticket** und generiert Antwort
4. **Automatische Antwort** wird in Intercom gepostet
5. **Ticket wird geschlossen** oder eskaliert

### Eskalations-Workflow

1. **AI erkennt komplexes Problem** (Beschwerde, technisches Problem)
2. **Ticket wird automatisch eskaliert** mit Begründung
3. **Support-Team wird benachrichtigt** (E-Mail, Slack)
4. **Menschlicher Mitarbeiter übernimmt** das Ticket
5. **AI lernt aus der Lösung** für zukünftige Fälle

---

## Monitoring & Analytics

### Metriken

- **Automatisierungsrate:** Wie viele Tickets automatisch gelöst werden
- **Eskalationsrate:** Wie oft menschliche Hilfe benötigt wird
- **Antwortzeiten:** Durchschnittliche Zeit bis zur ersten Antwort
- **Kundenzufriedenheit:** Bewertungen nach Ticket-Lösung

### Dashboard

```python
# src/monitoring/intercom_analytics.py
class IntercomAnalytics:
    def __init__(self, intercom_client: IntercomClient):
        self.client = intercom_client
    
    async def get_automation_stats(self) -> Dict:
        """Berechnet Automatisierungsstatistiken."""
        all_tickets = await self.client.get_tickets()
        
        automated = len([t for t in all_tickets if "ai_processed" in t.get("tags", [])])
        escalated = len([t for t in all_tickets if "ai_escalation" in t.get("tags", [])])
        
        return {
            "total_tickets": len(all_tickets),
            "automated_tickets": automated,
            "escalated_tickets": escalated,
            "automation_rate": automated / len(all_tickets) if all_tickets else 0,
            "escalation_rate": escalated / len(all_tickets) if all_tickets else 0
        }
```

---

## Vorteile der Intercom-Integration

### Für das Unternehmen
- **Reduzierte Antwortzeiten** durch automatische Verarbeitung
- **Entlastung des Support-Teams** bei Standardanfragen
- **24/7 Verfügbarkeit** für Kundenanfragen
- **Konsistente Antwortqualität** durch AI-Standards

### Für Kunden
- **Sofortige Antworten** auf Standardfragen
- **Bessere Verfügbarkeit** rund um die Uhr
- **Konsistente Kommunikation** unabhängig vom Mitarbeiter
- **Schnelle Eskalation** bei komplexen Problemen

### Für Support-Mitarbeiter
- **Fokus auf komplexe Fälle** statt Standardanfragen
- **Automatische Kategorisierung** und Priorisierung
- **Bessere Workload-Verteilung** durch intelligente Zuweisung
- **Lernmöglichkeiten** durch AI-gestützte Lösungsvorschläge

---

## Nächste Schritte

1. **Intercom API-Zugriff einrichten**
2. **Integration implementieren** (Code-Beispiele oben)
3. **Testphase starten** mit begrenztem Ticket-Volumen
4. **Monitoring einrichten** für Performance-Tracking
5. **Schulung des Support-Teams** für neue Workflows
6. **Rollout in Produktion** mit schrittweiser Ausweitung

---

*Intercom-Integration erstellt: [Datum]*  
*Version: 1.0.0* 