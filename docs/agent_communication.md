# Agent Communication System

This document describes the communication mechanisms between agents in the CognisGraph system.

## Overview

The CognisGraph system employs a multi-agent architecture where specialized agents work together to process, analyze, and visualize knowledge graphs. The communication between these agents is facilitated through multiple mechanisms:

1. Direct Method Calls
2. Shared Knowledge Store
3. Message Passing
4. State Transitions
5. Context Sharing

## 1. Direct Method Calls

Direct method calls are the most straightforward form of communication between agents. This mechanism is primarily used by the Orchestrator to coordinate the workflow.

### Implementation Details:
- The Orchestrator maintains direct references to specialized agents:
  ```python
  self.pdf_agent = PDFProcessingAgent(knowledge_store=knowledge_store, llm=query_engine.llm)
  self.query_agent = QueryAgent(knowledge_store, query_engine)
  self.visualization_agent = VisualizationAgent(knowledge_store)
  ```

- Method calls are typically asynchronous:
  ```python
  async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
      # Process input and coordinate with other agents
      pdf_result = await self.pdf_agent.process(input_data)
      viz_result = await self.visualization_agent.process(pdf_result)
      return viz_result
  ```

### Use Cases:
- Initializing agents
- Triggering specific processing tasks
- Error handling and recovery
- State management

## 2. Shared Knowledge Store

The Knowledge Store serves as a central repository for all graph data and acts as the primary data exchange mechanism between agents.

### Implementation Details:
- All agents share the same KnowledgeStore instance:
  ```python
  self.knowledge_store = KnowledgeStore()
  ```

- Agents can read and write entities and relationships:
  ```python
  # Writing to knowledge store
  self.knowledge_store.add_entity(entity)
  self.knowledge_store.add_relationship(relationship)
  
  # Reading from knowledge store
  entities = self.knowledge_store.get_entities()
  relationships = self.knowledge_store.get_relationships()
  ```

### Use Cases:
- Storing extracted knowledge from PDFs
- Retrieving data for query processing
- Maintaining graph consistency
- Caching frequently accessed data

## 3. Message Passing

The system uses a structured message format for communication between agents.

### Implementation Details:
- Messages are represented by the AIMessage class:
  ```python
  class AIMessage:
      def __init__(self, 
                   status: str,
                   message: str,
                   entities: Optional[List[Dict[str, Any]]] = None,
                   relationships: Optional[List[Dict[str, Any]]] = None,
                   data: Optional[Dict[str, Any]] = None):
          self.status = status
          self.message = message
          self.entities = entities or []
          self.relationships = relationships or []
          self.data = data or {}
  ```

- Messages can be converted to dictionary format:
  ```python
  def to_dict(self) -> Dict[str, Any]:
      return {
          "status": self.status,
          "message": self.message,
          "entities": self.entities,
          "relationships": self.relationships,
          "data": self.data
      }
  ```

### Use Cases:
- Query results
- Error notifications
- Processing status updates
- Data validation results

## 4. State Transitions

The system uses LangGraph's StateGraph for managing state transitions between agents.

### Implementation Details:
- Each agent maintains its own state graph:
  ```python
  self.state_graph = StateGraph(dict)
  ```

- State transitions are managed through the orchestrator:
  ```python
  class OrchestratorAgent(BaseAgent):
      def __init__(self, knowledge_store: KnowledgeStore, query_engine: QueryEngine):
          super().__init__(knowledge_store)
          self.state_graph = StateGraph(dict)
  ```

### Use Cases:
- Workflow management
- Error state handling
- Processing state tracking
- Resource management

## 5. Context Sharing

Agents maintain and share context information through a shared context dictionary.

### Implementation Details:
- Each agent has a context dictionary:
  ```python
  self.context: Dict[str, Any] = {}
  ```

- Context can be updated and shared:
  ```python
  def update_context(self, key: str, value: Any) -> None:
      self.context[key] = value
      logger.debug(f"{self.__class__.__name__} context updated with {key}")
  ```

- The orchestrator can access all agent contexts:
  ```python
  def get_agent_status(self) -> Dict[str, Any]:
      return {
          "pdf_agent": {
              "context": self.pdf_agent.get_context(),
              "status": "active"
          },
          "query_agent": {
              "context": self.query_agent.get_context(),
              "status": "active"
          },
          "visualization_agent": {
              "context": self.visualization_agent.get_context(),
              "status": "active"
          }
      }
  ```

### Use Cases:
- Maintaining processing state
- Sharing configuration
- Tracking performance metrics
- Debugging and monitoring

## Communication Flow Examples

### PDF Processing Flow:
```
User -> Orchestrator -> PDFProcessingAgent -> KnowledgeStore -> VisualizationAgent -> User
```

1. User submits PDF
2. Orchestrator receives request
3. PDFProcessingAgent extracts knowledge
4. Knowledge is stored in KnowledgeStore
5. VisualizationAgent creates visualization
6. Results are returned to user

### Query Processing Flow:
```
User -> Orchestrator -> QueryAgent -> KnowledgeStore -> VisualizationAgent -> User
```

1. User submits query
2. Orchestrator receives request
3. QueryAgent processes query
4. KnowledgeStore provides relevant data
5. VisualizationAgent creates visualization
6. Results are returned to user

## Error Handling

The system implements comprehensive error handling at multiple levels:

1. **Agent Level**:
   - Each agent implements its own error handling
   - Errors are logged and propagated up

2. **Orchestrator Level**:
   - Centralized error handling
   - State recovery
   - Fallback mechanisms

3. **System Level**:
   - Global error logging
   - Performance monitoring
   - Resource cleanup

## Performance Considerations

1. **Async Architecture**:
   - All communication is async-first
   - Non-blocking operations
   - Efficient resource utilization

2. **Caching**:
   - Knowledge store caching
   - Context caching
   - Result caching

3. **Resource Management**:
   - Memory usage optimization
   - Connection pooling
   - Resource cleanup

## Conclusion

The CognisGraph agent communication system provides a robust and flexible framework for inter-agent communication. By combining multiple communication mechanisms, the system achieves:

- Efficient data exchange
- Clear separation of concerns
- Scalable architecture
- Maintainable codebase
- Robust error handling 