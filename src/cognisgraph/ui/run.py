import streamlit as st
from cognisgraph.ui.app import CognisGraphUI
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.core.query_engine import QueryEngine

def main():
    """Run the CognisGraph UI."""
    # Initialize knowledge store and query engine
    knowledge_store = KnowledgeStore()
    query_engine = QueryEngine(knowledge_store)
    
    # Create and run UI
    ui = CognisGraphUI(knowledge_store, query_engine)
    ui.run()

if __name__ == "__main__":
    main() 