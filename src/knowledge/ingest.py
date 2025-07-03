"""
Dokument-Ingest-System für die Wissensdatenbank.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import click
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader
)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .vector_store import get_vector_store
from ..utils.config import get_config, get_brand_config
from ..utils.logger import get_logger


class DocumentIngester:
    """Lädt und verarbeitet Dokumente für die Wissensdatenbank."""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.config_manager = get_config()
        self.logger = get_logger()
        
        # Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Unterstützte Dateitypen
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.csv': CSVLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.doc': UnstructuredWordDocumentLoader,
            '.html': UnstructuredHTMLLoader,
            '.htm': UnstructuredHTMLLoader
        }
    
    def load_document(self, file_path: str) -> Optional[Document]:
        """Lädt ein einzelnes Dokument."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.logger.error(f"Datei nicht gefunden: {file_path}")
            return None
        
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_extensions:
            self.logger.logger.warning(f"Nicht unterstützter Dateityp: {extension}")
            return None
        
        try:
            loader_class = self.supported_extensions[extension]
            loader = loader_class(str(file_path))
            documents = loader.load()
            
            if documents:
                # Metadaten hinzufügen
                doc = documents[0]
                doc.metadata.update({
                    "source": str(file_path),
                    "file_type": extension,
                    "file_name": file_path.name
                })
                return doc
            
        except Exception as e:
            self.logger.log_error(e, {"file_path": str(file_path)})
        
        return None
    
    def load_documents_from_directory(
        self,
        directory_path: str,
        recursive: bool = True
    ) -> List[Document]:
        """Lädt alle Dokumente aus einem Verzeichnis."""
        directory = Path(directory_path)
        
        if not directory.exists():
            self.logger.logger.error(f"Verzeichnis nicht gefunden: {directory}")
            return []
        
        documents = []
        
        # Dateien durchsuchen
        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                doc = self.load_document(str(file_path))
                if doc:
                    documents.append(doc)
        
        self.logger.logger.info(f"{len(documents)} Dokumente aus {directory} geladen")
        return documents
    
    def process_documents_for_brand(
        self,
        brand: str,
        documents: List[Document],
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Verarbeitet Dokumente für eine bestimmte Marke."""
        if not documents:
            return []
        
        # Marken-Konfiguration prüfen
        brand_config = get_brand_config(brand)
        if not brand_config:
            self.logger.logger.error(f"Marken-Konfiguration nicht gefunden: {brand}")
            return []
        
        # Zusätzliche Metadaten hinzufügen
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "brand": brand,
            "category": category or "general",
            "processed_at": str(Path().stat().st_mtime)
        })
        
        # Dokumente zur Vector Store hinzufügen
        document_ids = self.vector_store.add_documents(brand, documents, metadata)
        
        self.logger.logger.info(
            f"{len(document_ids)} Dokumente für Marke {brand} verarbeitet"
        )
        
        return document_ids
    
    def ingest_from_directory(
        self,
        brand: str,
        directory_path: str,
        category: Optional[str] = None,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Lädt und verarbeitet alle Dokumente aus einem Verzeichnis für eine Marke."""
        # Dokumente laden
        documents = self.load_documents_from_directory(directory_path, recursive)
        
        if not documents:
            return {
                "success": False,
                "error": "Keine Dokumente gefunden",
                "brand": brand,
                "directory": directory_path
            }
        
        # Dokumente verarbeiten
        document_ids = self.process_documents_for_brand(
            brand, documents, category, metadata
        )
        
        return {
            "success": True,
            "brand": brand,
            "directory": directory_path,
            "documents_processed": len(documents),
            "document_ids": document_ids,
            "category": category
        }
    
    def rebuild_brand_knowledge_base(self, brand: str) -> Dict[str, Any]:
        """Baut die Wissensdatenbank einer Marke komplett neu auf."""
        brand_config = get_brand_config(brand)
        if not brand_config:
            return {
                "success": False,
                "error": f"Marken-Konfiguration nicht gefunden: {brand}"
            }
        
        knowledge_path = Path(brand_config.knowledge_base_path)
        if not knowledge_path.exists():
            return {
                "success": False,
                "error": f"Wissensdatenbank-Pfad nicht gefunden: {knowledge_path}"
            }
        
        # Alte Daten löschen
        self.vector_store.clear_brand_data(brand)
        
        # Alle Kategorien durchgehen
        results = []
        for category_dir in knowledge_path.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                result = self.ingest_from_directory(
                    brand, str(category_dir), category_name
                )
                results.append(result)
        
        # Statistiken sammeln
        total_documents = sum(
            r.get("documents_processed", 0) for r in results if r.get("success")
        )
        
        return {
            "success": True,
            "brand": brand,
            "total_documents": total_documents,
            "categories_processed": len(results),
            "results": results
        }
    
    def get_brand_statistics(self, brand: str) -> Dict[str, Any]:
        """Gibt Statistiken für eine Marke zurück."""
        stats = self.vector_store.get_collection_stats(brand)
        brand_config = get_brand_config(brand)
        
        if brand_config:
            knowledge_path = Path(brand_config.knowledge_base_path)
            if knowledge_path.exists():
                # Dateien zählen
                file_count = 0
                for ext in self.supported_extensions:
                    file_count += len(list(knowledge_path.rglob(f"*{ext}")))
                
                stats["source_files"] = file_count
                stats["knowledge_path"] = str(knowledge_path)
        
        return stats


@click.command()
@click.option('--brand', required=True, help='Marke/Mandant')
@click.option('--path', required=True, help='Pfad zu den Dokumenten')
@click.option('--category', help='Kategorie für die Dokumente')
@click.option('--rebuild', is_flag=True, help='Wissensdatenbank komplett neu aufbauen')
@click.option('--recursive', is_flag=True, default=True, help='Unterverzeichnisse durchsuchen')
@click.option('--stats', is_flag=True, help='Statistiken anzeigen')
def main(brand: str, path: str, category: Optional[str], rebuild: bool, recursive: bool, stats: bool):
    """CLI für Dokument-Ingest."""
    ingester = DocumentIngester()
    
    if stats:
        # Statistiken anzeigen
        stats_data = ingester.get_brand_statistics(brand)
        click.echo(json.dumps(stats_data, indent=2, ensure_ascii=False))
        return
    
    if rebuild:
        # Wissensdatenbank neu aufbauen
        click.echo(f"Baue Wissensdatenbank für Marke {brand} neu auf...")
        result = ingester.rebuild_brand_knowledge_base(brand)
    else:
        # Einzelne Dokumente hinzufügen
        click.echo(f"Lade Dokumente für Marke {brand} aus {path}...")
        result = ingester.ingest_from_directory(
            brand, path, category, recursive
        )
    
    if result.get("success"):
        click.echo("✅ Erfolgreich verarbeitet!")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        click.echo("❌ Fehler beim Verarbeiten!")
        click.echo(result.get("error", "Unbekannter Fehler"))
        exit(1)


if __name__ == "__main__":
    main() 