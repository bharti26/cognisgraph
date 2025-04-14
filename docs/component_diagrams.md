# Component Diagrams

## System Architecture

```mermaid
graph TD
    A[User Interface] --> B[State Graph]
    B --> C[Orchestrator]
    C --> D[Query Engine]
    C --> E[Knowledge Store]
    D --> E
    E --> D
```

## State Management

```mermaid
graph TD
    A[State Graph] --> B[Input Handler]
    A --> C[State Manager]
    A --> D[Output Handler]
    B --> C
    C --> D
```

## Knowledge Flow

```mermaid
graph LR
    A[User Input] --> B[State Graph]
    B --> C[Orchestrator]
    C --> D[Query Engine]
    D --> E[Knowledge Store]
    E --> F[Results]
    F --> G[User Output]
```

## Component Responsibilities

1. **State Graph**
   - Manages state transitions
   - Routes input to appropriate handlers
   - Maintains workflow state

2. **Orchestrator**
   - Coordinates between components
   - Manages agent interactions
   - Handles error cases

3. **Query Engine**
   - Processes natural language queries
   - Retrieves relevant knowledge
   - Generates responses

4. **Knowledge Store**
   - Stores and retrieves knowledge
   - Maintains entity relationships
   - Provides query interface

## Knowledge Store Architecture

```mermaid
classDiagram
    class KnowledgeStore {
        +graph: nx.DiGraph
        +add_entity(entity: Entity)
        +add_relationship(relationship: Relationship)
        +get_entities() List[Entity]
        +get_relationships() List[Relationship]
        +get_entity_by_id(id: str) Entity
        +get_relationships_for_entity(entity_id: str) List[Relationship]
    }

    class Entity {
        +id: str
        +type: str
        +attributes: Dict
        +metadata: Dict
    }

    class Relationship {
        +id: str
        +source_id: str
        +target_id: str
        +type: str
        +attributes: Dict
        +metadata: Dict
    }

    KnowledgeStore "1" *-- "many" Entity
    KnowledgeStore "1" *-- "many" Relationship
    Entity "1" -- "many" Relationship
```

## PDF Processing Flow

```mermaid
flowchart TD
    A[PDF Document] --> B[PDF Parser]
    B --> C[Text Extraction]
    C --> D[Entity Recognition]
    D --> E[Relationship Extraction]
    E --> F[Knowledge Store]
    F --> G[Graph Construction]
    
    subgraph Processing Steps
        C
        D
        E
    end
    
    subgraph Storage
        F
        G
    end
```

## Query Engine Architecture

```mermaid
classDiagram
    class QueryEngine {
        +knowledge_store: KnowledgeStore
        +process_query(query: str) QueryResult
        +_parse_query(query: str) Query
        +_execute_query(query: Query) QueryResult
        +_rank_results(results: List) List
    }

    class Query {
        +text: str
        +entities: List[str]
        +relationships: List[str]
        +filters: Dict
    }

    class QueryResult {
        +entities: List[Entity]
        +relationships: List[Relationship]
        +score: float
        +explanation: str
    }

    QueryEngine "1" *-- "1" KnowledgeStore
    QueryEngine "1" *-- "many" Query
    QueryEngine "1" *-- "many" QueryResult
```

## XAI Module Architecture

```mermaid
classDiagram
    class GraphExplainer {
        +knowledge_store: KnowledgeStore
        +explain_query_result(result: QueryResult) Explanation
        +_analyze_feature_importance() Dict
        +_calculate_saliency() Dict
        +_generate_counterfactuals() List
    }

    class FeatureImportanceAnalyzer {
        +analyze() Dict
        +_calculate_importance_scores() Dict
    }

    class SaliencyAnalyzer {
        +analyze() Dict
        +_calculate_centrality() Dict
    }

    class CounterfactualAnalyzer {
        +analyze() List
        +_generate_alternatives() List
    }

    GraphExplainer "1" *-- "1" KnowledgeStore
    GraphExplainer "1" *-- "1" FeatureImportanceAnalyzer
    GraphExplainer "1" *-- "1" SaliencyAnalyzer
    GraphExplainer "1" *-- "1" CounterfactualAnalyzer
```

## Visualization Pipeline

```mermaid
flowchart LR
    A[Knowledge Graph] --> B[Layout Selection]
    B --> C[Node Positioning]
    C --> D[Edge Routing]
    D --> E[Styling]
    E --> F[Interactive Elements]
    F --> G[Final Visualization]
    
    subgraph Layout Options
        B1[Force-directed]
        B2[Hierarchical]
        B3[Spring]
        B4[Circular]
    end
    
    B --> B1
    B --> B2
    B --> B3
    B --> B4
```

## Diagram Explanations

### Knowledge Store Architecture
- Shows the core classes and their relationships
- Illustrates how entities and relationships are stored and connected
- Demonstrates the hierarchical structure of the knowledge graph

### PDF Processing Flow
- Visualizes the step-by-step process of PDF document processing
- Shows how raw PDFs are transformed into structured knowledge
- Highlights the main processing steps and their relationships

### Query Engine Architecture
- Depicts the components involved in query processing
- Shows how queries are parsed and executed
- Illustrates the relationship between queries and results

### XAI Module Architecture
- Shows the components of the explainable AI system
- Illustrates how different analyzers work together
- Demonstrates the relationship between the explainer and the knowledge store

### Visualization Pipeline
- Shows the steps involved in creating visualizations
- Illustrates the different layout options available
- Demonstrates how the final interactive visualization is created 