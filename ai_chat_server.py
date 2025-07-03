#!/usr/bin/env python3
"""
Erweiterter Chat-Server mit echter OpenAI API und LangChain Integration.
"""
import json
import uuid
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

# Konfiguration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
MODEL_NAME = "gpt-3.5-turbo"
TEMPERATURE = 0.7

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

class HeineAIAgent:
    """Heine AI Agent mit LangChain und OpenAI."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Marken-spezifische Prompts
        self.brand_prompts = {
            "heine": """Du bist ein freundlicher und professioneller Kundenservice-Mitarbeiter der Heinrich Heine GmbH. 
            
Deine Aufgabe ist es, Kunden bei Fragen zu Heine-Produkten, Bestellungen, Lieferungen und allgemeinen Anfragen zu helfen.

Wichtige Informationen über Heine:
- Traditionsunternehmen mit Sitz in Deutschland
- Herstellung von hochwertigen Produkten
- Fokus auf Kundenzufriedenheit und Qualität
- Mehrsprachiger Support (Deutsch/Englisch)

Antworte immer höflich, professionell und hilfsbereit. Wenn du eine Frage nicht beantworten kannst, biete an, den Kunden an einen menschlichen Mitarbeiter weiterzuleiten.

Antworte auf Deutsch, es sei denn, der Kunde schreibt auf Englisch.""",
            
            "test_brand": """Du bist ein Test-Agent für das Heine AI System. 
            
Antworte freundlich und hilfreich auf alle Fragen. Dies ist eine Test-Umgebung.""",
        }
        
        # Eskalations-Schlüsselwörter
        self.escalation_keywords = [
            "beschwerde", "unzufrieden", "sofort", "mitarbeiter", "manager",
            "complaint", "unhappy", "immediately", "employee", "manager"
        ]
        
        # Konversations-Speicher pro Session
        self.conversations = {}
    
    def _get_brand_prompt(self, brand: str) -> str:
        """Gibt den Prompt für eine bestimmte Marke zurück."""
        return self.brand_prompts.get(brand, self.brand_prompts["heine"])
    
    def _should_escalate(self, message: str) -> tuple[bool, Optional[str]]:
        """Prüft ob eine Nachricht eskaliert werden sollte."""
        message_lower = message.lower()
        
        # Prüfe auf Eskalations-Schlüsselwörter
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True, f"Eskalation wegen Schlüsselwort: {keyword}"
        
        # Prüfe auf emotionale Indikatoren
        emotional_indicators = ["wütend", "verärgert", "frustriert", "angry", "frustrated"]
        for indicator in emotional_indicators:
            if indicator in message_lower:
                return True, f"Eskalation wegen emotionalem Indikator: {indicator}"
        
        return False, None
    
    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        brand: str,
        customer_id: Optional[str] = None
    ) -> Dict:
        """Verarbeitet eine Nachricht mit echter AI."""
        start_time = datetime.now()
        
        try:
            # Eskalation prüfen
            should_escalate, escalation_reason = self._should_escalate(message)
            
            # Konversations-Speicher laden oder erstellen
            if session_id not in self.conversations:
                self.conversations[session_id] = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            
            memory = self.conversations[session_id]
            
            # System-Prompt erstellen
            system_prompt = self._get_brand_prompt(brand)
            
            # Nachrichten für LLM vorbereiten
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ]
            
            # Konversationshistorie hinzufügen
            if memory.chat_memory.messages:
                messages = [SystemMessage(content=system_prompt)] + memory.chat_memory.messages + [HumanMessage(content=message)]
            
            # AI-Antwort generieren
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text.strip()
            
            # Konversation speichern
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(ai_response)
            
            # Antwortzeit berechnen
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Vertrauen basierend auf Eskalation und Antwortlänge
            confidence = 0.9 if not should_escalate else 0.6
            
            return {
                "session_id": session_id,
                "message": ai_response,
                "confidence": confidence,
                "escalated": should_escalate,
                "escalation_reason": escalation_reason,
                "sources": [],  # Für echte RAG-Integration später
                "response_time": response_time
            }
            
        except Exception as e:
            # Fallback bei Fehlern
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                "session_id": session_id,
                "message": f"Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage. Bitte versuchen Sie es später erneut oder kontaktieren Sie unseren Support. (Fehler: {str(e)})",
                "confidence": 0.3,
                "escalated": True,
                "escalation_reason": f"Technischer Fehler: {str(e)}",
                "sources": [],
                "response_time": response_time
            }

# FastAPI App erstellen
app = FastAPI(
    title="Heine AI Chat System",
    description="Mehrmandantenfähiges KI-Kundenkommunikationssystem mit OpenAI",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Agent
ai_agent = HeineAIAgent()

@app.post("/api/v1/chat", response_model=ChatResponseModel)
async def chat_endpoint(request: ChatRequest):
    """Chat-Endpunkt für Nachrichtenverarbeitung mit echter AI."""
    try:
        # Session-ID generieren falls nicht vorhanden
        session_id = request.session_id or str(uuid.uuid4())
        
        # Nachricht mit AI verarbeiten
        response = await ai_agent.process_message(
            message=request.message,
            session_id=session_id,
            brand=request.brand,
            customer_id=request.customer_id
        )
        
        return ChatResponseModel(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Nachrichtenverarbeitung: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Health-Check-Endpunkt."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "system": "Heine AI Chat System mit OpenAI",
        "model": MODEL_NAME,
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here")
    }

@app.get("/api/v1/brands")
async def get_available_brands():
    """Gibt verfügbare Marken zurück."""
    return {
        "brands": ["heine", "test_brand"],
        "default_brand": "heine"
    }

@app.get("/api/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Gibt die Konversationshistorie einer Session zurück."""
    if session_id in ai_agent.conversations:
        memory = ai_agent.conversations[session_id]
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": msg.content
                }
                for i, msg in enumerate(memory.chat_memory.messages)
            ]
        }
    else:
        return {"session_id": session_id, "messages": []}

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """Löscht eine Session und deren Konversationshistorie."""
    if session_id in ai_agent.conversations:
        del ai_agent.conversations[session_id]
        return {"message": f"Session {session_id} gelöscht"}
    else:
        return {"message": f"Session {session_id} nicht gefunden"}

@app.get("/")
async def root():
    """Root-Endpunkt mit System-Informationen."""
    return {
        "message": "Willkommen beim Heine AI Chat System",
        "version": "2.0.0",
        "status": "running",
        "ai_model": MODEL_NAME,
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/api/v1/health",
            "brands": "/api/v1/brands",
            "session_history": "/api/v1/sessions/{session_id}/history",
            "delete_session": "/api/v1/sessions/{session_id}",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Warnung wenn OpenAI API Key nicht gesetzt ist
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
        print("⚠️  WARNUNG: OpenAI API Key nicht gesetzt!")
        print("   Setze die Umgebungsvariable OPENAI_API_KEY oder bearbeite die Konfiguration.")
        print("   Das System wird mit eingeschränkter Funktionalität laufen.")
    
    uvicorn.run(app, host="127.0.0.1", port=8001) 