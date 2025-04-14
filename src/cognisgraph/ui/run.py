"""Run module for the UI application."""
import asyncio
import sys
import streamlit as st
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from streamlit_app import StreamlitApp

def main():
    # Create a new event loop if one doesn't exist
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Initialize knowledge store and query engine
    knowledge_store = KnowledgeStore()
    query_engine = QueryEngine(knowledge_store)
    
    # Initialize and run the UI
    ui = StreamlitApp(knowledge_store, query_engine)
    ui.run()

if __name__ == "__main__":
    main() 