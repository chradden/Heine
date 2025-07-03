#!/usr/bin/env python3
"""
Streamlit Dashboard für das Heine AI Chat System.
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Konfiguration
API_BASE_URL = "http://127.0.0.1:8001"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/v1/health"
BRANDS_ENDPOINT = f"{API_BASE_URL}/api/v1/brands"
SESSION_HISTORY_ENDPOINT = f"{API_BASE_URL}/api/v1/sessions"

def check_api_health() -> bool:
    """Prüft ob die API erreichbar ist."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_brands() -> List[str]:
    """Holt verfügbare Marken von der API."""
    try:
        response = requests.get(BRANDS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("brands", ["heine"])
        return ["heine"]
    except:
        return ["heine"]

def send_chat_message(brand: str, message: str, session_id: Optional[str] = None) -> Dict:
    """Sendet eine Chat-Nachricht an die API."""
    payload = {
        "brand": brand,
        "message": message,
        "session_id": session_id
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API-Fehler: {response.status_code}"}
    except Exception as e:
        return {"error": f"Verbindungsfehler: {str(e)}"}

def main():
    st.set_page_config(
        page_title="Heine AI Chat System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar
    st.sidebar.title("🤖 Heine AI System")
    st.sidebar.markdown("---")
    
    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.sidebar.success("✅ API erreichbar")
        # Zusätzliche API-Info
        try:
            health_response = requests.get(HEALTH_ENDPOINT, timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.sidebar.info(f"Version: {health_data.get('version', 'N/A')}")
                st.sidebar.info(f"Model: {health_data.get('model', 'N/A')}")
                if health_data.get('openai_configured'):
                    st.sidebar.success("🤖 OpenAI API konfiguriert")
                else:
                    st.sidebar.warning("⚠️ OpenAI API nicht konfiguriert")
        except:
            pass
    else:
        st.sidebar.error("❌ API nicht erreichbar")
        st.sidebar.info("Stelle sicher, dass der AI-Chat-Server läuft:")
        st.sidebar.code("py -3.12 ai_chat_server.py")
        return
    
    # Marken-Auswahl
    brands = get_available_brands()
    selected_brand = st.sidebar.selectbox(
        "Marke auswählen:",
        brands,
        index=0
    )
    
    # Session-Management
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Neue Session
    if st.sidebar.button("🔄 Neue Session"):
        st.session_state.session_id = None
        st.session_state.chat_history = []
        st.rerun()
    
    # Session-ID anzeigen
    if st.session_state.session_id:
        st.sidebar.info(f"Session: {st.session_state.session_id[:8]}...")
    
    st.sidebar.markdown("---")
    
    # Hauptbereich
    st.title("💬 Heine AI Chat System")
    st.markdown(f"**Aktuelle Marke:** {selected_brand}")
    
    # Chat-Bereich
    chat_container = st.container()
    
    with chat_container:
        # Chat-Historie anzeigen
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    if message.get("confidence"):
                        st.caption(f"Vertrauen: {message['confidence']:.1%}")
                    if message.get("response_time"):
                        st.caption(f"Antwortzeit: {message['response_time']:.2f}s")
    
    # Eingabebereich
    if prompt := st.chat_input("Deine Nachricht..."):
        # Benutzernachricht hinzufügen
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Nachricht an API senden
        with st.spinner("AI verarbeitet Nachricht..."):
            response = send_chat_message(
                brand=selected_brand,
                message=prompt,
                session_id=st.session_state.session_id
            )
        
        if "error" in response:
            st.error(f"Fehler: {response['error']}")
        else:
            # Session-ID speichern
            if not st.session_state.session_id:
                st.session_state.session_id = response["session_id"]
            
            # AI-Antwort hinzufügen
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["message"],
                "confidence": response["confidence"],
                "response_time": response["response_time"],
                "escalated": response["escalated"],
                "timestamp": datetime.now()
            })
            
            # Chat neu laden
            st.rerun()
    
    # Info-Bereich
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Nachrichten", len(st.session_state.chat_history))
    
    with col2:
        if st.session_state.chat_history:
            avg_confidence = sum(
                msg.get("confidence", 0) for msg in st.session_state.chat_history 
                if msg["role"] == "assistant"
            ) / len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
            st.metric("Ø Vertrauen", f"{avg_confidence:.1%}")
        else:
            st.metric("Ø Vertrauen", "0%")
    
    with col3:
        escalated_count = sum(
            1 for msg in st.session_state.chat_history 
            if msg.get("escalated", False)
        )
        st.metric("Eskalationen", escalated_count)
    
    # Debug-Informationen
    with st.expander("🔧 Debug-Informationen"):
        st.json({
            "api_url": API_BASE_URL,
            "session_id": st.session_state.session_id,
            "selected_brand": selected_brand,
            "available_brands": brands,
            "chat_history_length": len(st.session_state.chat_history)
        })

if __name__ == "__main__":
    main() 