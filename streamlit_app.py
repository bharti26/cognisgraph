import streamlit as st
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.core.query_engine import QueryEngine
from cognisgraph.ui.app import CognisGraphUI

def main():
    # Initialize core components
    knowledge_store = KnowledgeStore()
    query_engine = QueryEngine(knowledge_store)
    
    # Initialize and run the UI
    ui = CognisGraphUI(knowledge_store, query_engine)
    ui.run()

if __name__ == "__main__":
    main() 