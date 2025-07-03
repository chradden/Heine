"""
Beispiel für die grundlegende Verwendung des Heine KI-Systems.
"""
import asyncio
import os
from datetime import datetime

# Umgebungsvariablen setzen (für Entwicklung)
os.environ.setdefault('OPENAI_API_KEY', 'your-openai-api-key-here')
os.environ.setdefault('MODEL_NAME', 'gpt-3.5-turbo')
os.environ.setdefault('MODEL_TEMPERATURE', '0.7')

from src.agents.brand_agent import get_agent
from src.knowledge.ingest import ingest_documents
from src.utils.logger import get_logger


async def example_chat_conversation():
    """Beispiel für eine Chat-Konversation."""
    print("=== Heine KI-System - Chat-Beispiel ===\n")
    
    # Agent für Heine-Marke erstellen
    agent = get_agent("heine", use_mock_api=True)
    
    # Beispiel-Konversation
    conversation = [
        "Hallo, ich habe eine Frage zu meiner Bestellung.",
        "Meine Bestellnummer ist ord12345678. Kann ich den Status erfahren?",
        "Wann wird meine Bestellung geliefert?",
        "Ich bin sehr unzufrieden mit dem Service!",
        "Können Sie mir helfen, ein Produkt zu finden?"
    ]
    
    session_id = "example_session_001"
    
    for i, message in enumerate(conversation, 1):
        print(f"Kunde: {message}")
        
        # Nachricht verarbeiten
        response = await agent.process_message(
            message=message,
            session_id=session_id
        )
        
        print(f"KI-Assistent: {response.message}")
        print(f"Konfidenz: {response.confidence:.2f}")
        print(f"Eskaliert: {response.escalated}")
        if response.escalation_reason:
            print(f"Eskalationsgrund: {response.escalation_reason}")
        print(f"Antwortzeit: {response.response_time:.2f}s")
        print("-" * 50)
    
    # Konversationshistorie anzeigen
    print("\n=== Konversationshistorie ===")
    history = agent.get_conversation_history(session_id)
    for msg in history:
        role = "Kunde" if msg.role.value == "user" else "KI-Assistent"
        print(f"{role}: {msg.content}")


async def example_email_processing():
    """Beispiel für E-Mail-Verarbeitung."""
    print("\n=== Heine KI-System - E-Mail-Beispiel ===\n")
    
    from src.channels.email_interface import get_email_interface
    
    email_interface = get_email_interface()
    
    # Beispiel-E-Mail
    email_data = {
        "content": """
        Sehr geehrtes Heine-Team,
        
        ich habe eine Frage zu meiner Bestellung ord87654321.
        Mein Kundenkonto ist cust123456.
        
        Wann wird meine Bestellung geliefert? Ich benötige sie dringend.
        
        Mit freundlichen Grüßen
        Max Mustermann
        max.mustermann@example.com
        """,
        "from_email": "max.mustermann@example.com",
        "to_email": "support@heine.com",
        "subject": "Frage zu Bestellung ord87654321"
    }
    
    # E-Mail verarbeiten
    result = await email_interface.process_incoming_email(email_data)
    
    if result["success"]:
        print("E-Mail erfolgreich verarbeitet!")
        print(f"Marke: {result['brand']}")
        print(f"Session-ID: {result['session_id']}")
        print(f"Konfidenz: {result['confidence']:.2f}")
        print(f"Eskaliert: {result['escalated']}")
        
        print("\n=== Automatische Antwort ===")
        print(result["response"])
        
        if result["customer_info"]:
            print(f"\nKundeninformationen:")
            for key, value in result["customer_info"].items():
                if value:
                    print(f"  {key}: {value}")
    else:
        print(f"Fehler bei der E-Mail-Verarbeitung: {result['error']}")


async def example_document_ingestion():
    """Beispiel für Dokumenten-Ingestion."""
    print("\n=== Heine KI-System - Dokumenten-Ingestion ===\n")
    
    # Beispiel-Dokument erstellen
    example_content = """
    Heine GmbH - Häufig gestellte Fragen
    
    Versand:
    - Standardversand: 3-5 Werktage
    - Expressversand: 1-2 Werktage
    - Kosten: Standard 4,99€, Express 9,99€
    
    Rückgabe:
    - 30 Tage Rückgaberecht
    - Kostenlose Rücksendung
    - Rückerstattung innerhalb von 14 Tagen
    
    Kontakt:
    - E-Mail: support@heine.com
    - Telefon: +49 123 456789
    - Geschäftszeiten: Mo-Fr 9-18 Uhr
    
    Produktinformationen:
    - Alle Produkte sind original verpackt
    - 2 Jahre Garantie auf alle Artikel
    - Kostenloser Kundenservice
    """
    
    # Temporäre Datei erstellen
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(example_content)
        temp_file = f.name
    
    try:
        # Dokument ingestieren
        print("Dokument wird ingestiert...")
        result = await ingest_documents(
            brand="heine",
            file_paths=[temp_file],
            chunk_size=500,
            chunk_overlap=50
        )
        
        print(f"Ingestion abgeschlossen!")
        print(f"Verarbeitete Dateien: {result['processed_files']}")
        print(f"Erstellte Chunks: {result['total_chunks']}")
        print(f"Fehler: {result['errors']}")
        
    finally:
        # Temporäre Datei löschen
        os.unlink(temp_file)


async def example_api_usage():
    """Beispiel für API-Verwendung."""
    print("\n=== Heine KI-System - API-Beispiel ===\n")
    
    from src.api.client import get_mock_api_client
    
    api_client = get_mock_api_client()
    
    # Kundeninformationen abrufen
    print("Kundeninformationen abrufen...")
    customer = await api_client.get_customer_info("heine", "cust123456")
    if customer:
        print(f"Kunde: {customer.first_name} {customer.last_name}")
        print(f"E-Mail: {customer.email}")
        print(f"Bestellungen: {customer.total_orders}")
        print(f"Gesamtausgaben: {customer.total_spent}€")
    
    # Bestellinformationen abrufen
    print("\nBestellinformationen abrufen...")
    order = await api_client.get_order_info("heine", "ord12345678")
    if order:
        print(f"Bestellung: {order.order_id}")
        print(f"Status: {order.status}")
        print(f"Betrag: {order.total_amount}€")
        print(f"Artikel: {len(order.items)}")
    
    # Versandinformationen abrufen
    print("\nVersandinformationen abrufen...")
    shipping = await api_client.get_shipping_info("heine", "TRK123456789")
    if shipping:
        print(f"Tracking-ID: {shipping.tracking_id}")
        print(f"Status: {shipping.status}")
        print(f"Versandunternehmen: {shipping.carrier}")
        if shipping.estimated_delivery:
            print(f"Geschätzte Lieferung: {shipping.estimated_delivery}")
    
    # Produktsuche
    print("\nProduktsuche...")
    products = await api_client.search_products("heine", "Bier", max_results=3)
    if products:
        print(f"Gefundene Produkte: {len(products)}")
        for product in products:
            print(f"- {product.name}: {product.price}€")


async def example_escalation():
    """Beispiel für Eskalation."""
    print("\n=== Heine KI-System - Eskalations-Beispiel ===\n")
    
    from src.agents.escalation_manager import get_escalation_manager
    
    escalation_manager = get_escalation_manager()
    
    # Eskalationsanfrage erstellen
    escalation_request = escalation_manager.create_escalation_request(
        session_id="escalation_example_001",
        brand="heine",
        reason="complaint",
        trigger_message="Ich bin sehr unzufrieden mit dem Service!",
        customer_id="cust123456",
        conversation_history=[
            {"role": "user", "content": "Meine Bestellung ist nicht angekommen", "timestamp": "2024-01-10T10:00:00"},
            {"role": "assistant", "content": "Ich schaue das für Sie nach", "timestamp": "2024-01-10T10:01:00"},
            {"role": "user", "content": "Ich bin sehr unzufrieden!", "timestamp": "2024-01-10T10:02:00"}
        ],
        customer_data={"email": "max@example.com", "name": "Max Mustermann"}
    )
    
    # Ticket erstellen
    ticket = escalation_manager.create_ticket_from_request(escalation_request)
    
    print(f"Eskalationsticket erstellt:")
    print(f"Ticket-ID: {ticket.ticket_id}")
    print(f"Grund: {ticket.reason.value}")
    print(f"Priorität: {ticket.priority.value}")
    print(f"Abteilung: {ticket.department}")
    print(f"Status: {ticket.status.value}")
    
    # Ausstehende Tickets anzeigen
    pending_tickets = escalation_manager.get_pending_tickets("heine")
    print(f"\nAusstehende Tickets für Heine: {len(pending_tickets)}")


async def main():
    """Hauptfunktion für alle Beispiele."""
    logger = get_logger()
    logger.logger.info("Heine KI-System Beispiele gestartet")
    
    try:
        # Chat-Konversation
        await example_chat_conversation()
        
        # E-Mail-Verarbeitung
        await example_email_processing()
        
        # Dokumenten-Ingestion
        await example_document_ingestion()
        
        # API-Verwendung
        await example_api_usage()
        
        # Eskalation
        await example_escalation()
        
        print("\n=== Alle Beispiele abgeschlossen ===")
        
    except Exception as e:
        logger.log_error(e, {"example": "basic_usage"})
        print(f"Fehler beim Ausführen der Beispiele: {e}")


if __name__ == "__main__":
    # Asyncio-Event-Loop ausführen
    asyncio.run(main()) 