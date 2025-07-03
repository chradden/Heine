"""
Tests für die Agenten-Logik.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agents.base_agent import HeineBaseAgent
from src.agents.brand_agent import HeineBrandAgent, get_agent, AgentFactory
from src.models.chat_models import ChatMessage, ChatResponse, MessageRole
from src.models.escalation_models import EscalationReason


class TestHeineBaseAgent:
    """Tests für HeineBaseAgent."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock-Konfiguration für Tests."""
        with patch('src.agents.base_agent.get_system_config') as mock_system:
            with patch('src.agents.base_agent.get_brand_config') as mock_brand:
                mock_system.return_value = Mock(
                    model_name="gpt-3.5-turbo",
                    model_temperature=0.7,
                    model_max_tokens=1000,
                    openai_api_key="test-key",
                    escalation_keywords=["beschwerde", "unzufrieden"]
                )
                mock_brand.return_value = Mock(
                    name="Test Brand",
                    brand_voice="Friendly",
                    escalation_threshold=0.5
                )
                yield mock_system, mock_brand
    
    @pytest.fixture
    def agent(self, mock_config):
        """Agent-Instanz für Tests."""
        with patch('src.agents.base_agent.get_vector_store'):
            with patch('src.agents.base_agent.ChatOpenAI'):
                with patch('src.agents.base_agent.ConversationalRetrievalChain'):
                    agent = HeineBaseAgent("test_brand")
                    return agent
    
    def test_agent_initialization(self, agent):
        """Testet die Initialisierung des Agenten."""
        assert agent.brand == "test_brand"
        assert agent.tools == []
        assert agent.memory is not None
    
    def test_should_escalate_low_confidence(self, agent):
        """Testet Eskalation bei niedriger Konfidenz."""
        should_escalate, reason = agent._should_escalate("Test message", 0.3)
        assert should_escalate is True
        assert reason == EscalationReason.LOW_CONFIDENCE
    
    def test_should_escalate_complaint_keyword(self, agent):
        """Testet Eskalation bei Beschwerde-Schlüsselwort."""
        should_escalate, reason = agent._should_escalate("Ich habe eine beschwerde", 0.8)
        assert should_escalate is True
        assert reason == EscalationReason.COMPLAINT
    
    def test_should_not_escalate_normal_message(self, agent):
        """Testet, dass normale Nachrichten nicht eskaliert werden."""
        should_escalate, reason = agent._should_escalate("Hallo, wie geht es Ihnen?", 0.8)
        assert should_escalate is False
        assert reason is None
    
    def test_extract_entities(self, agent):
        """Testet die Extraktion von Entitäten."""
        message = "Hallo, ich bin Kunde cust123456 und habe Bestellung ord87654321"
        entities = agent._extract_entities(message)
        
        assert entities["customer_id"] == "cust123456"
        assert entities["order_id"] == "ord87654321"
    
    def test_extract_entities_email(self, agent):
        """Testet die Extraktion von E-Mail-Adressen."""
        message = "Kontaktieren Sie mich unter test@example.com"
        entities = agent._extract_entities(message)
        
        assert entities["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, agent):
        """Testet erfolgreiche Nachrichtenverarbeitung."""
        # Mock für retrieval_chain
        agent.retrieval_chain.ainvoke = AsyncMock(return_value={
            "answer": "Das ist eine Test-Antwort",
            "source_documents": [Mock(page_content="Test content", metadata={})]
        })
        
        response = await agent.process_message(
            message="Test message",
            session_id="test_session"
        )
        
        assert isinstance(response, ChatResponse)
        assert response.session_id == "test_session"
        assert "Test-Antwort" in response.message
        assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_process_message_escalation(self, agent):
        """Testet Nachrichtenverarbeitung mit Eskalation."""
        # Mock für retrieval_chain mit niedriger Konfidenz
        agent.retrieval_chain.ainvoke = AsyncMock(return_value={
            "answer": "Das ist eine Test-Antwort",
            "source_documents": []
        })
        
        response = await agent.process_message(
            message="Ich bin sehr unzufrieden!",
            session_id="test_session"
        )
        
        assert response.escalated is True
        assert response.escalation_reason is not None
    
    def test_create_escalation_message(self, agent):
        """Testet die Erstellung von Eskalationsnachrichten."""
        message = agent._create_escalation_message(EscalationReason.COMPLAINT)
        assert "Mitarbeiter" in message
        assert "verbinden" in message
    
    def test_get_conversation_history(self, agent):
        """Testet das Abrufen der Konversationshistorie."""
        # Mock-Nachrichten hinzufügen
        agent.memory.chat_memory.add_user_message("Hallo")
        agent.memory.chat_memory.add_ai_message("Guten Tag!")
        
        history = agent.get_conversation_history("test_session")
        
        assert len(history) == 2
        assert history[0].role == MessageRole.USER
        assert history[1].role == MessageRole.ASSISTANT


class TestHeineBrandAgent:
    """Tests für HeineBrandAgent."""
    
    @pytest.fixture
    def brand_agent(self):
        """Brand-Agent-Instanz für Tests."""
        with patch('src.agents.brand_agent.get_system_config'):
            with patch('src.agents.brand_agent.get_brand_config'):
                with patch('src.agents.brand_agent.get_vector_store'):
                    with patch('src.agents.brand_agent.ChatOpenAI'):
                        with patch('src.agents.brand_agent.ConversationalRetrievalChain'):
                            with patch('src.agents.brand_agent.get_mock_api_client'):
                                agent = HeineBrandAgent("test_brand", use_mock_api=True)
                                return agent
    
    def test_brand_agent_initialization(self, brand_agent):
        """Testet die Initialisierung des Brand-Agenten."""
        assert brand_agent.brand == "test_brand"
        assert len(brand_agent.tools) == 4  # 4 API-Tools
    
    def test_brand_agent_has_api_tools(self, brand_agent):
        """Testet, dass der Brand-Agent API-Tools hat."""
        tool_names = [tool.name for tool in brand_agent.tools]
        
        assert "get_customer_info" in tool_names
        assert "get_order_info" in tool_names
        assert "get_shipping_info" in tool_names
        assert "search_products" in tool_names
    
    def test_get_brand_specific_prompt(self, brand_agent):
        """Testet das markenspezifische Prompt."""
        prompt = brand_agent.get_brand_specific_prompt()
        
        assert "KI-Assistent" in prompt
        assert "Tools" in prompt
        assert "Kundendaten" in prompt


class TestAgentFactory:
    """Tests für AgentFactory."""
    
    def test_create_agent_heine(self):
        """Testet die Erstellung eines Heine-Agenten."""
        with patch('src.agents.brand_agent.HeineBrandAgent'):
            agent = AgentFactory.create_agent("heine")
            assert agent is not None
    
    def test_create_agent_subbrand1(self):
        """Testet die Erstellung eines SubBrand1-Agenten."""
        with patch('src.agents.brand_agent.SubBrand1Agent'):
            agent = AgentFactory.create_agent("subbrand1")
            assert agent is not None
    
    def test_create_agent_unknown_brand(self):
        """Testet die Erstellung eines Agenten für unbekannte Marke."""
        with patch('src.agents.brand_agent.HeineBrandAgent'):
            agent = AgentFactory.create_agent("unknown_brand")
            assert agent is not None
    
    def test_get_available_brands(self):
        """Testet das Abrufen verfügbarer Marken."""
        brands = AgentFactory.get_available_brands()
        
        assert "heine" in brands
        assert "subbrand1" in brands
        assert len(brands) == 2


class TestAgentCaching:
    """Tests für Agent-Caching."""
    
    def test_get_agent_caching(self):
        """Testet das Caching von Agenten."""
        with patch('src.agents.brand_agent.AgentFactory.create_agent') as mock_create:
            mock_create.return_value = Mock()
            
            # Erster Aufruf
            agent1 = get_agent("test_brand")
            
            # Zweiter Aufruf (sollte gecacht sein)
            agent2 = get_agent("test_brand")
            
            # Dritter Aufruf mit anderem Parameter
            agent3 = get_agent("test_brand", use_mock_api=True)
            
            # create_agent sollte nur zweimal aufgerufen werden
            assert mock_create.call_count == 2
            assert agent1 == agent2  # Gleiche Instanz
            assert agent1 != agent3  # Verschiedene Instanzen
    
    def test_clear_agent_cache(self):
        """Testet das Löschen des Agent-Caches."""
        with patch('src.agents.brand_agent.AgentFactory.create_agent') as mock_create:
            mock_create.return_value = Mock()
            
            # Agent erstellen
            agent1 = get_agent("test_brand")
            
            # Cache löschen
            from src.agents.brand_agent import clear_agent_cache
            clear_agent_cache()
            
            # Neuer Agent erstellen
            agent2 = get_agent("test_brand")
            
            # Sollten verschiedene Instanzen sein
            assert agent1 != agent2


class TestAPITools:
    """Tests für API-Tools."""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock-API-Client für Tests."""
        client = Mock()
        client.get_customer_info = AsyncMock(return_value=Mock(
            first_name="Max",
            last_name="Mustermann",
            email="max@example.com",
            total_orders=5,
            total_spent=150.0
        ))
        client.get_order_info = AsyncMock(return_value=Mock(
            status="shipped",
            total_amount=50.0,
            items=[Mock(quantity=2, product_name="Test Product")]
        ))
        client.get_shipping_info = AsyncMock(return_value=Mock(
            status="in_transit",
            estimated_delivery="2024-01-15",
            carrier="DHL"
        ))
        client.search_products = AsyncMock(return_value=[
            Mock(name="Test Product", price=25.0, description="Test Description")
        ])
        return client
    
    @pytest.mark.asyncio
    async def test_customer_info_tool(self, mock_api_client):
        """Testet das CustomerInfoTool."""
        from src.agents.brand_agent import CustomerInfoTool
        
        tool = CustomerInfoTool("test_brand", mock_api_client)
        result = await tool._arun("cust123456")
        
        assert "Max Mustermann" in result
        assert "max@example.com" in result
        assert "5" in result  # total_orders
        assert "150" in result  # total_spent
    
    @pytest.mark.asyncio
    async def test_order_info_tool(self, mock_api_client):
        """Testet das OrderInfoTool."""
        from src.agents.brand_agent import OrderInfoTool
        
        tool = OrderInfoTool("test_brand", mock_api_client)
        result = await tool._arun("ord12345678")
        
        assert "shipped" in result
        assert "50" in result  # total_amount
        assert "Test Product" in result
    
    @pytest.mark.asyncio
    async def test_shipping_info_tool(self, mock_api_client):
        """Testet das ShippingInfoTool."""
        from src.agents.brand_agent import ShippingInfoTool
        
        tool = ShippingInfoTool("test_brand", mock_api_client)
        result = await tool._arun("TRK123456789")
        
        assert "in_transit" in result
        assert "2024-01-15" in result
        assert "DHL" in result
    
    @pytest.mark.asyncio
    async def test_product_search_tool(self, mock_api_client):
        """Testet das ProductSearchTool."""
        from src.agents.brand_agent import ProductSearchTool
        
        tool = ProductSearchTool("test_brand", mock_api_client)
        result = await tool._arun("test product")
        
        assert "Test Product" in result
        assert "25" in result  # price
        assert "Test Description" in result


if __name__ == "__main__":
    pytest.main([__file__]) 