# Agent System Sequence Diagram

## Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant QueryAgent
    participant QueryEngine
    participant LLM
    participant KnowledgeStore
    participant GraphExplainer

    User->>QueryAgent: process(query)
    Note over QueryAgent: Validate Query
    QueryAgent->>QueryEngine: execute_query(query)
    
    QueryEngine->>KnowledgeStore: get_entities()
    KnowledgeStore-->>QueryEngine: entities
    QueryEngine->>KnowledgeStore: get_relationships()
    KnowledgeStore-->>QueryEngine: relationships
    
    Note over QueryEngine: Format Graph Data
    QueryEngine->>QueryEngine: _format_graph_data()
    QueryEngine->>QueryEngine: _chunk_graph_data()
    
    QueryEngine->>LLM: invoke(prompt)
    LLM-->>QueryEngine: response
    
    Note over QueryEngine: Validate Response
    QueryEngine->>QueryEngine: _validate_response()
    
    QueryEngine->>QueryEngine: process_query()
    Note over QueryEngine: Extract Relevant Entities
    
    QueryEngine->>GraphExplainer: calculate_centrality()
    GraphExplainer-->>QueryEngine: centrality_scores
    
    QueryEngine-->>QueryAgent: query_result
    Note over QueryAgent: Transform Result
    QueryAgent-->>User: response
```

## PDF Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant PDFAgent
    participant PDFParser
    participant EntityExtractor
    participant KnowledgeStore
    participant GraphExplainer

    User->>PDFAgent: process(file_path)
    Note over PDFAgent: Validate File
    
    PDFAgent->>PDFParser: parse_pdf(file_path)
    PDFParser->>PDFParser: extract_text()
    PDFParser->>EntityExtractor: extract_entities()
    EntityExtractor-->>PDFParser: entities
    
    PDFParser->>EntityExtractor: extract_relationships()
    EntityExtractor-->>PDFParser: relationships
    
    PDFParser-->>PDFAgent: parsed_data
    
    PDFAgent->>KnowledgeStore: add_entities(entities)
    PDFAgent->>KnowledgeStore: add_relationships(relationships)
    
    PDFAgent->>GraphExplainer: analyze_graph()
    GraphExplainer-->>PDFAgent: analysis_results
    
    PDFAgent-->>User: success_response
```

## Agent State Management

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    IDLE --> VALIDATING: Input Received
    VALIDATING --> PROCESSING: Valid Input
    VALIDATING --> ERROR: Invalid Input
    
    PROCESSING --> ANALYZING: Initial Processing Complete
    ANALYZING --> GENERATING_RESPONSE: Analysis Complete
    
    GENERATING_RESPONSE --> SUCCESS: Response Generated
    GENERATING_RESPONSE --> ERROR: Generation Failed
    
    ERROR --> IDLE: Reset
    SUCCESS --> IDLE: Complete
```

## Component Interactions

```mermaid
sequenceDiagram
    participant User
    participant BaseAgent
    participant SpecializedAgent
    participant QueryEngine
    participant KnowledgeStore
    participant XAIModule

    User->>BaseAgent: process(input)
    Note over BaseAgent: Input Validation
    
    BaseAgent->>SpecializedAgent: handle_input(validated_input)
    
    SpecializedAgent->>QueryEngine: execute_operation()
    QueryEngine->>KnowledgeStore: retrieve_data()
    KnowledgeStore-->>QueryEngine: data
    
    QueryEngine->>XAIModule: explain_operation()
    XAIModule-->>QueryEngine: explanation
    
    QueryEngine-->>SpecializedAgent: operation_result
    SpecializedAgent-->>BaseAgent: processed_result
    
    Note over BaseAgent: Result Validation
    BaseAgent-->>User: final_response
```

## Error Handling Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant ErrorHandler
    participant Logger
    participant StateManager

    User->>Agent: process(input)
    
    alt Input Validation Error
        Agent->>ErrorHandler: handle_validation_error()
        ErrorHandler->>Logger: log_error()
        ErrorHandler-->>Agent: error_response
    else Processing Error
        Agent->>ErrorHandler: handle_processing_error()
        ErrorHandler->>StateManager: rollback_state()
        ErrorHandler->>Logger: log_error()
        ErrorHandler-->>Agent: error_response
    else System Error
        Agent->>ErrorHandler: handle_system_error()
        ErrorHandler->>Logger: log_critical()
        ErrorHandler->>StateManager: reset_state()
        ErrorHandler-->>Agent: error_response
    end
    
    Agent-->>User: error_response
```

## Diagram Explanation

The updated sequence diagrams illustrate the enhanced interaction flows in the CognisGraph system:

1. **Query Processing Flow**:
   - Improved query validation
   - LLM integration for natural language processing
   - Graph data chunking and caching
   - Response validation and transformation
   - Centrality metrics calculation
   - Enhanced error handling

2. **PDF Processing Flow**:
   - Robust file validation
   - Parallel entity and relationship extraction
   - Graph analysis with XAI features
   - Structured response generation

3. **State Management**:
   - More granular state transitions
   - Better error recovery
   - Clear success/failure paths

4. **Component Interactions**:
   - Clear separation of concerns
   - Standardized communication patterns
   - XAI integration at multiple levels

5. **Error Handling**:
   - Comprehensive error categorization
   - State management during errors
   - Detailed logging and recovery

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant StateGraph
    participant QueryEngine
    participant KnowledgeStore
    participant Orchestrator

    User->>UI: Submit Query
    UI->>StateGraph: Process Input
    StateGraph->>Orchestrator: Route to Handler
    Orchestrator->>QueryEngine: Execute Query
    QueryEngine->>KnowledgeStore: Retrieve Knowledge
    KnowledgeStore-->>QueryEngine: Return Results
    QueryEngine-->>Orchestrator: Process Results
    Orchestrator-->>StateGraph: Update State
    StateGraph-->>UI: Return Response
    UI-->>User: Display Results
```

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PROCESSING: Process Input
    PROCESSING --> IDLE: Complete
    PROCESSING --> ERROR: Error
    ERROR --> IDLE: Reset
```

## Component Descriptions

1. **User Interface (UI)**
   - Handles user input and output
   - Manages file uploads
   - Displays query results and visualizations

2. **State Graph**
   - Manages workflow state
   - Routes input to appropriate handlers
   - Maintains state transitions

3. **Orchestrator**
   - Coordinates between components
   - Manages agent interactions
   - Handles error cases

4. **Query Engine**
   - Processes natural language queries
   - Retrieves relevant knowledge
   - Generates responses

5. **Knowledge Store**
   - Stores and retrieves knowledge
   - Maintains entity relationships
   - Provides query interface

## Workflow Steps

1. **Input Processing**
   - User submits query through UI
   - UI sends input to State Graph
   - State Graph routes to appropriate handler

2. **Query Execution**
   - Orchestrator receives input
   - Query Engine processes query
   - Knowledge Store retrieves relevant information

3. **Result Processing**
   - Query Engine processes results
   - Orchestrator updates state
   - State Graph returns response

4. **Output Generation**
   - UI receives response
   - Results are displayed to user
   - State is updated accordingly

```mermaid
sequenceDiagram
    participant User
    participant BaseAgent
    participant PDFParser
    participant QueryEngine
    participant KnowledgeStore
    participant Visualizer

    %% PDF Processing Flow
    User->>BaseAgent: process_pdf(file_path)
    Note over BaseAgent: State: PROCESSING
    BaseAgent->>PDFParser: parse_document(file_path)
    PDFParser->>KnowledgeStore: store_entities(entities)
    PDFParser->>KnowledgeStore: store_relationships(relationships)
    PDFParser-->>BaseAgent: Parsing complete
    BaseAgent->>Visualizer: visualize_graph()
    Note over BaseAgent: State: VISUALIZING
    Visualizer-->>BaseAgent: Visualization data
    BaseAgent-->>User: Success response

    %% Query Processing Flow
    User->>BaseAgent: process_query(query_text)
    Note over BaseAgent: State: PROCESSING
    BaseAgent->>QueryEngine: execute_query(query_text)
    QueryEngine->>KnowledgeStore: get_entities()
    QueryEngine->>KnowledgeStore: get_relationships()
    QueryEngine-->>BaseAgent: Query results
    BaseAgent->>Visualizer: visualize_results()
    Note over BaseAgent: State: VISUALIZING
    Visualizer-->>BaseAgent: Visualization data
    BaseAgent-->>User: Query response

    %% Reset Flow
    User->>BaseAgent: reset()
    Note over BaseAgent: State: IDLE
    BaseAgent-->>User: Reset complete
```

## Diagram Explanation

This sequence diagram illustrates the interaction flow in the CognisGraph agent system:

1. **PDF Processing Flow**:
   - User calls `process_pdf()` with a file path
   - Agent transitions to PROCESSING state
   - PDFParser extracts knowledge
   - Knowledge is stored in KnowledgeStore
   - Visualization is generated
   - Agent transitions through states appropriately

2. **Query Processing Flow**:
   - User calls `process_query()` with query text
   - Agent transitions to PROCESSING state
   - QueryEngine processes the query
   - Results are retrieved from KnowledgeStore
   - Visualization is generated
   - Agent transitions through states appropriately

3. **Reset Flow**:
   - User can reset the agent
   - Agent returns to IDLE state
   - Context is cleared

The diagram shows how the BaseAgent manages state transitions and coordinates between different components while maintaining a clean separation of concerns. 