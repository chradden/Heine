#!/usr/bin/env python3
"""
Test-Skript für die Hauptpakete des Heine AI-Systems.
"""

def test_imports():
    """Testet die Importierung der Hauptpakete."""
    try:
        print("Testing imports...")
        
        # Test LangChain
        import langchain
        print("✅ LangChain imported successfully")
        
        # Test OpenAI
        import openai
        print("✅ OpenAI imported successfully")
        
        # Test FastAPI
        import fastapi
        print("✅ FastAPI imported successfully")
        
        # Test Streamlit
        import streamlit
        print("✅ Streamlit imported successfully")
        
        # Test ChromaDB (ohne ONNX Runtime)
        import chromadb
        from chromadb.config import Settings
        
        # Erstelle eine einfache ChromaDB-Instanz ohne ONNX Runtime
        # Verwende eine minimale Konfiguration
        client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_db_impl="duckdb+parquet"
            )
        )
        print("✅ ChromaDB imported and initialized successfully")
        
        # Test andere wichtige Pakete
        import pandas
        print("✅ Pandas imported successfully")
        
        import pydantic
        print("✅ Pydantic imported successfully")
        
        import yaml
        print("✅ PyYAML imported successfully")
        
        print("\n🎉 All main packages imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    test_imports() 