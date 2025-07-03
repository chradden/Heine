"""
Basis-Agent-Klasse mit LangChain-Integration und RAG-Funktionalität.
"""
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent

from ..knowledge.vector_store import get_vector_store
from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger
from ..models.chat_models import ChatMessage, ChatResponse, MessageRole
from ..models.escalation_models import EscalationReason, EscalationRequest


class HeineBaseAgent:
    """Basis-KI-Agent für das Heine-System."""
    
    def __init__(self, brand: str):
        self.brand = brand
        self.system_config = get_system_config()
        self.brand_config = get_brand_config(brand)
        self.logger = get_logger()
        self.vector_store = get_vector_store()
        
        if not self.brand_config:
            raise ValueError(f"Marken-Konfiguration nicht gefunden: {brand}")
        
        # LLM initialisieren
        self.llm = ChatOpenAI(
            model_name=self.system_config.model_name,
            temperature=self.system_config.model_temperature,
            max_tokens=self.system_config.model_max_tokens,
            openai_api_key=self.system_config.openai_api_key
        )
        
        # Memory für Konversationsverlauf
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Tools für den Agenten
        self.tools: List[BaseTool] = []
        
        # Prompt-Template
        self.prompt_template = self._create_prompt_template()
        
        # Retrieval Chain
        self.retrieval_chain = self._create_retrieval_chain()
        
        # Agent Executor
        self.agent_executor = self._create_agent_executor()
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Erstellt das Prompt-Template für den Agenten."""
        system_prompt = f"""Du bist ein KI-Assistent für {self.brand_config.name}. 
        
Deine Aufgabe ist es, Kundenanfragen professionell und hilfreich zu beantworten.

Wichtige Richtlinien:
- Antworte immer freundlich und professionell im Stil von {self.brand_config.brand_voice}
- Verwende nur Informationen aus der Wissensdatenbank von {self.brand_config.name}
- Wenn du eine Information nicht findest, sage das ehrlich
- Bei komplexen Anfragen oder Beschwerden, eskaliere an einen menschlichen Mitarbeiter
- Verwende die verfügbaren Tools, um aktuelle Kundendaten abzurufen

Verfügbare Tools:
{{tools}}

Konversationsverlauf:
{{chat_history}}

Aktuelle Anfrage: {{input}}

Antworte auf Deutsch und sei hilfreich und präzise."""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _create_retrieval_chain(self) -> ConversationalRetrievalChain:
        """Erstellt die Retrieval Chain für RAG."""
        # Retriever mit Marken-Filter
        retriever = self.vector_store.search
        
        # Contextual Compression für bessere Relevanz
        compressor = LLMChainExtractor.from_llm(self.llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=retriever
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=compression_retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Erstellt den Agent Executor."""
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt_template
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True
        )
    
    def _should_escalate(self, message: str, confidence: float) -> Tuple[bool, Optional[EscalationReason]]:
        """Prüft, ob eine Anfrage eskaliert werden sollte."""
        # Niedrige Konfidenz
        if confidence < self.brand_config.escalation_threshold:
            return True, EscalationReason.LOW_CONFIDENCE
        
        # Eskalations-Schlüsselwörter
        escalation_keywords = self.system_config.escalation_keywords
        message_lower = message.lower()
        
        for keyword in escalation_keywords:
            if keyword.lower() in message_lower:
                if keyword in ["beschwerde", "unzufrieden", "sofort"]:
                    return True, EscalationReason.COMPLAINT
                elif keyword == "mitarbeiter":
                    return True, EscalationReason.MANUAL_INTERVENTION
        
        # Emotionale Äußerungen erkennen
        emotional_patterns = [
            r"\b(sehr|extrem|total)\s+(wütend|verärgert|frustriert|unzufrieden)\b",
            r"\b(sofort|sofortig|dringend)\b",
            r"\b(manager|chef|vorgesetzter)\b",
            r"\b(beschwerde|reklamation|beanstandung)\b"
        ]
        
        for pattern in emotional_patterns:
            if re.search(pattern, message_lower):
                return True, EscalationReason.EMOTIONAL_DISTRESS
        
        return False, None
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extrahiert Entitäten aus der Nachricht."""
        entities = {}
        
        # Kunden-ID
        customer_match = re.search(r'cust\d+', message, re.IGNORECASE)
        if customer_match:
            entities['customer_id'] = customer_match.group(0)
        
        # Bestell-ID
        order_match = re.search(r'ord\d+', message, re.IGNORECASE)
        if order_match:
            entities['order_id'] = order_match.group(0)
        
        # Tracking-ID
        tracking_match = re.search(r'TRK\d+', message, re.IGNORECASE)
        if tracking_match:
            entities['tracking_id'] = tracking_match.group(0)
        
        # E-Mail-Adresse
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match:
            entities['email'] = email_match.group(0)
        
        return entities
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        customer_id: Optional[str] = None,
        context_messages: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """Verarbeitet eine Benutzernachricht und gibt eine Antwort zurück."""
        start_time = time.time()
        
        try:
            # Entitäten extrahieren
            entities = self._extract_entities(message)
            if customer_id:
                entities['customer_id'] = customer_id
            
            # Kontext-Nachrichten zum Memory hinzufügen
            if context_messages:
                for msg in context_messages[-5:]:  # Nur die letzten 5 Nachrichten
                    if msg.role == MessageRole.USER:
                        self.memory.chat_memory.add_user_message(msg.content)
                    elif msg.role == MessageRole.ASSISTANT:
                        self.memory.chat_memory.add_ai_message(msg.content)
            
            # RAG-Abfrage durchführen
            retrieval_result = await self.retrieval_chain.ainvoke({
                "question": message,
                "chat_history": self.memory.chat_memory.messages
            })
            
            # Antwort extrahieren
            ai_response = retrieval_result.get("answer", "Entschuldigung, ich konnte keine passende Antwort finden.")
            source_documents = retrieval_result.get("source_documents", [])
            
            # Konfidenz berechnen (basierend auf Anzahl und Relevanz der Quellen)
            confidence = min(1.0, len(source_documents) * 0.2 + 0.3)
            
            # Eskalation prüfen
            should_escalate, escalation_reason = self._should_escalate(message, confidence)
            
            if should_escalate:
                # Eskalationsantwort
                escalation_message = self._create_escalation_message(escalation_reason)
                ai_response = escalation_message
                confidence = 0.0
            
            # Quellen formatieren
            sources = []
            for doc in source_documents[:3]:  # Maximal 3 Quellen
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata
                })
            
            response_time = time.time() - start_time
            
            # Antwort erstellen
            response = ChatResponse(
                session_id=session_id,
                message=ai_response,
                confidence=confidence,
                escalated=should_escalate,
                escalation_reason=escalation_reason.value if escalation_reason else None,
                sources=sources,
                response_time=response_time
            )
            
            # Logging
            self.logger.log_chat_interaction(
                brand=self.brand,
                session_id=session_id,
                user_message=message,
                ai_response=ai_response,
                confidence=confidence,
                escalated=should_escalate,
                metadata={
                    "entities": entities,
                    "sources_count": len(sources),
                    "escalation_reason": escalation_reason.value if escalation_reason else None
                }
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.log_error(e, {
                "brand": self.brand,
                "session_id": session_id,
                "message": message
            })
            
            # Fallback-Antwort
            return ChatResponse(
                session_id=session_id,
                message="Entschuldigung, es gab einen technischen Fehler. Bitte versuchen Sie es später erneut oder kontaktieren Sie unseren Support.",
                confidence=0.0,
                escalated=True,
                escalation_reason=EscalationReason.TECHNICAL_PROBLEM.value,
                response_time=response_time
            )
    
    def _create_escalation_message(self, reason: EscalationReason) -> str:
        """Erstellt eine Eskalationsnachricht."""
        escalation_messages = {
            EscalationReason.LOW_CONFIDENCE: "Ich verstehe Ihre Anfrage, aber ich benötige weitere Informationen, um Ihnen optimal helfen zu können. Ich verbinde Sie mit einem unserer Mitarbeiter.",
            EscalationReason.COMPLAINT: "Ich verstehe, dass Sie unzufrieden sind. Lassen Sie mich Sie mit einem unserer erfahrenen Mitarbeiter verbinden, der sich persönlich um Ihr Anliegen kümmert.",
            EscalationReason.EMOTIONAL_DISTRESS: "Ich spüre, dass Sie frustriert sind. Lassen Sie mich Sie mit einem unserer Mitarbeiter verbinden, der Ihnen persönlich weiterhelfen kann.",
            EscalationReason.MANUAL_INTERVENTION: "Für diese Anfrage benötigen Sie einen persönlichen Kontakt. Ich verbinde Sie gerne mit einem unserer Mitarbeiter.",
            EscalationReason.TECHNICAL_PROBLEM: "Es gab einen technischen Fehler. Lassen Sie mich Sie mit unserem Support verbinden."
        }
        
        return escalation_messages.get(reason, "Ich verbinde Sie mit einem unserer Mitarbeiter.")
    
    def add_tool(self, tool: BaseTool):
        """Fügt ein Tool zum Agenten hinzu."""
        self.tools.append(tool)
        # Agent neu erstellen mit neuen Tools
        self.agent_executor = self._create_agent_executor()
    
    def get_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Gibt den Konversationsverlauf zurück."""
        messages = []
        for msg in self.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                messages.append(ChatMessage(
                    id=str(len(messages)),
                    session_id=session_id,
                    brand=self.brand,
                    role=MessageRole.USER,
                    content=msg.content
                ))
            elif isinstance(msg, AIMessage):
                messages.append(ChatMessage(
                    id=str(len(messages)),
                    session_id=session_id,
                    brand=self.brand,
                    role=MessageRole.ASSISTANT,
                    content=msg.content
                ))
        
        return messages
    
    def clear_memory(self):
        """Löscht das Memory des Agenten."""
        self.memory.clear() 