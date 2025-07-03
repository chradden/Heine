"""
Chat-Interface mit FastAPI und WebSocket-Support.
"""
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..agents.brand_agent import get_agent
from ..models.chat_models import ChatMessage, ChatResponse, MessageRole, ChatSession
from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger
from ..agents.escalation_manager import get_escalation_manager


class ChatRequest(BaseModel):
    """Anfrage für Chat-Antwort."""
    brand: str
    message: str
    session_id: Optional[str] = None
    customer_id: Optional[str] = None


class ChatResponseModel(BaseModel):
    """Antwort-Modell für Chat."""
    session_id: str
    message: str
    confidence: float
    escalated: bool
    escalation_reason: Optional[str] = None
    sources: List[Dict[str, Any]]
    response_time: float


class WebSocketManager:
    """Verwaltet WebSocket-Verbindungen."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Verbindet einen WebSocket."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.session_connections[session_id] = connection_id
    
    def disconnect(self, session_id: str):
        """Trennt eine WebSocket-Verbindung."""
        connection_id = self.session_connections.get(session_id)
        if connection_id:
            del self.active_connections[connection_id]
            del self.session_connections[session_id]
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Sendet eine Nachricht an einen spezifischen Client."""
        connection_id = self.session_connections.get(session_id)
        if connection_id:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    # Verbindung ist unterbrochen
                    self.disconnect(session_id)


class ChatInterface:
    """Chat-Interface für das Heine-System."""
    
    def __init__(self):
        self.system_config = get_system_config()
        self.logger = get_logger()
        self.websocket_manager = WebSocketManager()
        self.escalation_manager = get_escalation_manager()
        
        # Aktive Sessions
        self.active_sessions: Dict[str, ChatSession] = {}
    
    async def process_chat_message(
        self,
        brand: str,
        message: str,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> ChatResponseModel:
        """Verarbeitet eine Chat-Nachricht."""
        # Session-ID generieren falls nicht vorhanden
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Session laden oder erstellen
        session = self._get_or_create_session(session_id, brand, customer_id)
        
        # Agent für die Marke holen
        agent = get_agent(brand, use_mock_api=True)  # Mock-API für Entwicklung
        
        # Kontext-Nachrichten laden
        context_messages = session.get_context_messages()
        
        # Nachricht verarbeiten
        response = await agent.process_message(
            message=message,
            session_id=session_id,
            customer_id=customer_id,
            context_messages=context_messages
        )
        
        # Session aktualisieren
        self._update_session(session, message, response.message)
        
        # Eskalation verarbeiten
        if response.escalated:
            await self._handle_escalation(session, response)
        
        return ChatResponseModel(
            session_id=response.session_id,
            message=response.message,
            confidence=response.confidence,
            escalated=response.escalated,
            escalation_reason=response.escalation_reason,
            sources=response.sources,
            response_time=response.response_time
        )
    
    def _get_or_create_session(
        self,
        session_id: str,
        brand: str,
        customer_id: Optional[str] = None
    ) -> ChatSession:
        """Lädt oder erstellt eine Chat-Session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            return session
        
        # Neue Session erstellen
        session = ChatSession(
            session_id=session_id,
            brand=brand,
            customer_id=customer_id,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def _update_session(self, session: ChatSession, user_message: str, ai_response: str):
        """Aktualisiert eine Session mit neuen Nachrichten."""
        # Benutzernachricht hinzufügen
        user_msg = ChatMessage(
            id=str(len(session.messages)),
            session_id=session.session_id,
            brand=session.brand,
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.now()
        )
        session.add_message(user_msg)
        
        # AI-Antwort hinzufügen
        ai_msg = ChatMessage(
            id=str(len(session.messages)),
            session_id=session.session_id,
            brand=session.brand,
            role=MessageRole.ASSISTANT,
            content=ai_response,
            timestamp=datetime.now()
        )
        session.add_message(ai_msg)
    
    async def _handle_escalation(self, session: ChatSession, response: ChatResponse):
        """Behandelt eine Eskalation."""
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
        
        # Konversationshistorie formatieren
        conversation_history = []
        for msg in session.messages[-10:]:  # Letzte 10 Nachrichten
            conversation_history.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        # Eskalationsanfrage erstellen
        escalation_request = self.escalation_manager.create_escalation_request(
            session_id=session.session_id,
            brand=session.brand,
            reason=reason,
            trigger_message=session.messages[-2].content if len(session.messages) >= 2 else "",
            customer_id=session.customer_id,
            conversation_history=conversation_history
        )
        
        # Ticket erstellen
        ticket = self.escalation_manager.create_ticket_from_request(escalation_request)
        
        self.logger.logger.info(
            f"Eskalation erstellt: Ticket {ticket.ticket_id} für Session {session.session_id}"
        )
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Gibt den Verlauf einer Session zurück."""
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        return [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """Bereinigt inaktive Sessions."""
        current_time = datetime.now()
        inactive_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if not session.is_active(timeout_minutes):
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.active_sessions[session_id]
        
        if inactive_sessions:
            self.logger.logger.info(f"{len(inactive_sessions)} inaktive Sessions bereinigt")


# FastAPI-App erstellen
app = FastAPI(
    title="Heine AI Chat Interface",
    description="Chat-Interface für das Heine KI-Kundenkommunikationssystem",
    version="1.0.0"
)

# CORS-Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat-Interface-Instanz
chat_interface = ChatInterface()


@app.post("/api/v1/chat", response_model=ChatResponseModel)
async def chat_endpoint(request: ChatRequest):
    """HTTP-Endpunkt für Chat-Nachrichten."""
    try:
        # Marken-Konfiguration prüfen
        brand_config = get_brand_config(request.brand)
        if not brand_config:
            raise HTTPException(status_code=400, detail=f"Marke '{request.brand}' nicht gefunden")
        
        # Nachricht verarbeiten
        response = await chat_interface.process_chat_message(
            brand=request.brand,
            message=request.message,
            session_id=request.session_id,
            customer_id=request.customer_id
        )
        
        return response
        
    except Exception as e:
        chat_interface.logger.log_error(e, {
            "brand": request.brand,
            "session_id": request.session_id,
            "message": request.message
        })
        raise HTTPException(status_code=500, detail="Interner Server-Fehler")


@app.get("/api/v1/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Gibt den Chat-Verlauf einer Session zurück."""
    try:
        history = chat_interface.get_session_history(session_id)
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        chat_interface.logger.log_error(e, {"session_id": session_id})
        raise HTTPException(status_code=500, detail="Interner Server-Fehler")


@app.websocket("/ws/chat/{brand}")
async def websocket_endpoint(websocket: WebSocket, brand: str):
    """WebSocket-Endpunkt für Echtzeit-Chat."""
    session_id = str(uuid.uuid4())
    
    try:
        # Verbindung akzeptieren
        await chat_interface.websocket_manager.connect(websocket, session_id)
        
        # Willkommensnachricht
        welcome_message = {
            "type": "welcome",
            "session_id": session_id,
            "brand": brand,
            "message": f"Willkommen beim {brand} Chat-Support!"
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Nachrichten verarbeiten
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Chat-Nachricht verarbeiten
            response = await chat_interface.process_chat_message(
                brand=brand,
                message=message_data.get("message", ""),
                session_id=session_id,
                customer_id=message_data.get("customer_id")
            )
            
            # Antwort senden
            response_message = {
                "type": "response",
                "session_id": response.session_id,
                "message": response.message,
                "confidence": response.confidence,
                "escalated": response.escalated,
                "escalation_reason": response.escalation_reason,
                "sources": response.sources,
                "response_time": response.response_time
            }
            
            await websocket.send_text(json.dumps(response_message))
            
    except WebSocketDisconnect:
        chat_interface.websocket_manager.disconnect(session_id)
        chat_interface.logger.logger.info(f"WebSocket-Verbindung getrennt: {session_id}")
    except Exception as e:
        chat_interface.logger.log_error(e, {"session_id": session_id, "brand": brand})
        chat_interface.websocket_manager.disconnect(session_id)


@app.get("/api/v1/health")
async def health_check():
    """Health-Check-Endpunkt."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(chat_interface.active_sessions)
    }


@app.get("/api/v1/brands")
async def get_available_brands():
    """Gibt alle verfügbaren Marken zurück."""
    from ..agents.brand_agent import AgentFactory
    brands = AgentFactory.get_available_brands()
    
    brand_info = []
    for brand in brands:
        brand_config = get_brand_config(brand)
        if brand_config:
            brand_info.append({
                "id": brand,
                "name": brand_config.name,
                "description": brand_config.description,
                "support_email": brand_config.support_email
            })
    
    return {"brands": brand_info}


# Cleanup-Task für inaktive Sessions
@app.on_event("startup")
async def startup_event():
    """Startup-Event."""
    chat_interface.logger.logger.info("Chat-Interface gestartet")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown-Event."""
    chat_interface.logger.logger.info("Chat-Interface beendet")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 