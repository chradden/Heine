"""
Vector Store für die Wissensdatenbank mit Mandantentrennung.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..utils.config import get_system_config, get_brand_config
from ..utils.logger import get_logger


class MultiTenantVectorStore:
    """Vector Store mit Mandantentrennung."""
    
    def __init__(self):
        self.system_config = get_system_config()
        self.logger = get_logger()
        
        # Initialisiere Embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.system_config.embedding_model,
            openai_api_key=self.system_config.openai_api_key
        )
        
        # Initialisiere ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=self.system_config.vector_store_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Text Splitter für Dokumente
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Cache für Collection-Namen
        self._collection_cache = {}
    
    def _get_collection_name(self, brand: str) -> str:
        """Gibt den Collection-Namen für eine Marke zurück."""
        if brand not in self._collection_cache:
            self._collection_cache[brand] = f"knowledge_{brand}"
        return self._collection_cache[brand]
    
    def _get_or_create_collection(self, brand: str):
        """Erstellt oder lädt eine Collection für eine Marke."""
        collection_name = self._get_collection_name(brand)
        
        try:
            collection = self.chroma_client.get_collection(collection_name)
            self.logger.logger.info(f"Collection {collection_name} geladen")
        except Exception:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"brand": brand, "description": f"Knowledge base for {brand}"}
            )
            self.logger.logger.info(f"Collection {collection_name} erstellt")
        
        return collection
    
    def add_documents(
        self,
        brand: str,
        documents: List[Document],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Fügt Dokumente zur Wissensdatenbank einer Marke hinzu."""
        if not documents:
            return []
        
        collection = self._get_or_create_collection(brand)
        
        # Dokumente in Chunks aufteilen
        all_chunks = []
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            for chunk in chunks:
                # Marken-spezifische Metadaten hinzufügen
                chunk.metadata["brand"] = brand
                if metadata:
                    chunk.metadata.update(metadata)
            all_chunks.extend(chunks)
        
        # Chunks zur Collection hinzufügen
        texts = [chunk.page_content for chunk in all_chunks]
        metadatas = [chunk.metadata for chunk in all_chunks]
        ids = [f"{brand}_{i}_{hash(chunk.page_content) % 1000000}" 
               for i, chunk in enumerate(all_chunks)]
        
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        self.logger.logger.info(
            f"{len(all_chunks)} Chunks für Marke {brand} hinzugefügt"
        )
        
        return ids
    
    def search(
        self,
        brand: str,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Sucht in der Wissensdatenbank einer Marke."""
        collection = self._get_or_create_collection(brand)
        
        # Marken-Filter hinzufügen
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["brand"] = brand
        
        # Suche durchführen
        results = collection.query(
            query_texts=[query],
            n_results=k,
            where=filter_metadata
        )
        
        # Ergebnisse in LangChain-Format konvertieren
        documents = []
        for i, (text, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            doc = Document(
                page_content=text,
                metadata=metadata
            )
            # Konvertiere Distanz zu Ähnlichkeitsscore
            similarity = 1.0 - distance
            documents.append((doc, similarity))
        
        self.logger.logger.info(
            f"Suche für Marke {brand}: {len(documents)} Ergebnisse gefunden"
        )
        
        return documents
    
    def delete_documents(
        self,
        brand: str,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Löscht Dokumente aus der Wissensdatenbank einer Marke."""
        collection = self._get_or_create_collection(brand)
        
        # Marken-Filter hinzufügen
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["brand"] = brand
        
        # Alle IDs für die Marke abrufen
        results = collection.get(where=filter_metadata)
        
        if results["ids"]:
            collection.delete(ids=results["ids"])
            deleted_count = len(results["ids"])
            self.logger.logger.info(
                f"{deleted_count} Dokumente für Marke {brand} gelöscht"
            )
            return deleted_count
        
        return 0
    
    def get_collection_stats(self, brand: str) -> Dict[str, Any]:
        """Gibt Statistiken für eine Collection zurück."""
        collection = self._get_or_create_collection(brand)
        
        try:
            count = collection.count()
            return {
                "brand": brand,
                "document_count": count,
                "collection_name": self._get_collection_name(brand)
            }
        except Exception as e:
            self.logger.log_error(e, {"brand": brand})
            return {
                "brand": brand,
                "document_count": 0,
                "collection_name": self._get_collection_name(brand),
                "error": str(e)
            }
    
    def list_brands(self) -> List[str]:
        """Gibt alle verfügbaren Marken zurück."""
        collections = self.chroma_client.list_collections()
        brands = []
        
        for collection in collections:
            if collection.name.startswith("knowledge_"):
                brand = collection.name.replace("knowledge_", "")
                brands.append(brand)
        
        return brands
    
    def clear_brand_data(self, brand: str) -> bool:
        """Löscht alle Daten einer Marke."""
        try:
            collection_name = self._get_collection_name(brand)
            self.chroma_client.delete_collection(collection_name)
            self.logger.logger.info(f"Alle Daten für Marke {brand} gelöscht")
            return True
        except Exception as e:
            self.logger.log_error(e, {"brand": brand})
            return False
    
    def backup_collection(self, brand: str, backup_path: str) -> bool:
        """Erstellt ein Backup einer Collection."""
        try:
            collection = self._get_or_create_collection(brand)
            backup_file = Path(backup_path) / f"{brand}_backup.json"
            
            # Alle Daten abrufen
            results = collection.get()
            
            # Backup speichern
            backup_data = {
                "brand": brand,
                "timestamp": str(Path().stat().st_mtime),
                "documents": results["documents"],
                "metadatas": results["metadatas"],
                "ids": results["ids"]
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.logger.info(f"Backup für Marke {brand} erstellt: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"brand": brand, "backup_path": backup_path})
            return False
    
    def restore_collection(self, brand: str, backup_path: str) -> bool:
        """Stellt eine Collection aus einem Backup wieder her."""
        try:
            backup_file = Path(backup_path) / f"{brand}_backup.json"
            
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup-Datei nicht gefunden: {backup_file}")
            
            # Backup laden
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Collection löschen und neu erstellen
            self.clear_brand_data(brand)
            collection = self._get_or_create_collection(brand)
            
            # Daten wiederherstellen
            collection.add(
                documents=backup_data["documents"],
                metadatas=backup_data["metadatas"],
                ids=backup_data["ids"]
            )
            
            self.logger.logger.info(f"Backup für Marke {brand} wiederhergestellt")
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"brand": brand, "backup_path": backup_path})
            return False


# Globale Vector Store-Instanz
vector_store = MultiTenantVectorStore()


def get_vector_store() -> MultiTenantVectorStore:
    """Gibt die globale Vector Store-Instanz zurück."""
    return vector_store 