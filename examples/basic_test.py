from cognisgraph.app import CognisGraph

def main():
    # Initialize CognisGraph
    cognis = CognisGraph()

    # Add some knowledge
    knowledge = {
        "entity": "Python",
        "type": "programming_language",
        "properties": {
            "description": "A high-level programming language",
            "creator": "Guido van Rossum",
            "year": 1991
        }
    }

    # Add the entity
    print("Adding knowledge...")
    success = cognis.add_knowledge(knowledge)
    print(f"Knowledge addition {'successful' if success else 'failed'}")

    # Query the knowledge
    query = "What is Python?"
    print(f"\nQuery: {query}")
    result = cognis.query(query)
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence}")

if __name__ == "__main__":
    main()
