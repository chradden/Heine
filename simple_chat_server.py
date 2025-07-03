#!/usr/bin/env python3
"""
Vereinfachter Chat-Server für das Heine AI-System.
"""
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Mock-Implementierung für Entwicklung
class MockAgent:
    """Mock-Agent für Entwicklung ohne ChromaDB."""
    
    async def process_message(self, message: str, session_id: str, customer_id: Optional[str] = None, context_messages: List[Dict] = None) -> Dict:
        """Verarbeitet eine Nachricht und gibt eine Mock-Antwort zurück."""
        return {
            "session_id": session_id,
            "message": f"Mock-Antwort auf: '{message}'. Dies ist eine Test-Antwort des Heine AI-Systems.",
            "confidence": 0.85,
            "escalated": False,
            "escalation_reason": None,
            "sources": [],
            "response_time": 0.5
        }

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

# FastAPI App erstellen
app = FastAPI(
    title="Heine AI Chat System",
    description="Mehrmandantenfähiges KI-Kundenkommunikationssystem",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock-Agent
mock_agent = MockAgent()

@app.post("/api/v1/chat", response_model=ChatResponseModel)
async def chat_endpoint(request: ChatRequest):
    """Chat-Endpunkt für Nachrichtenverarbeitung."""
    try:
        # Session-ID generieren falls nicht vorhanden
        session_id = request.session_id or str(uuid.uuid4())
        
        # Nachricht verarbeiten
        response = await mock_agent.process_message(
            message=request.message,
            session_id=session_id,
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
        "version": "1.0.0",
        "system": "Heine AI Chat System"
    }

@app.get("/api/v1/brands")
async def get_available_brands():
    """Gibt verfügbare Marken zurück."""
    return {
        "brands": ["heine", "test_brand"],
        "default_brand": "heine"
    }

@app.get("/")
async def root():
    """Root-Endpunkt mit System-Informationen."""
    return {
        "message": "Willkommen beim Heine AI Chat System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/api/v1/health",
            "brands": "/api/v1/brands",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001) 