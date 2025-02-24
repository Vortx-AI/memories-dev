# Memories Agents Framework

## Overview
The Memories Agents Framework provides a collection of specialized agents that work together . Each agent is designed with specific capabilities and can use various tools to achieve its goals.

## Architecture

### Base Agent
All agents inherit from `BaseAgent`, which provides:
- Tool management and execution
- State management
- Planning capabilities
- Goal-oriented processing
- Memory of actions and results

### Agent State
Each agent maintains its state using `AgentState`:
```python
@dataclass
class AgentState:
    status: str              # idle, planning, executing, completed, error
    current_goal: str        # Current goal being processed
    current_plan: List[str]  # List of tool names to execute
    memory: Dict[str, Any]   # Memory of past actions and results
    last_action: str         # Last tool used
    last_result: Any         # Result of last tool execution
    error: str              # Error message if any
```

### Tools
Agents use tools to perform specific tasks:
```python
class Tool:
    name: str               # Tool identifier
    func: Callable         # The actual function to execute
    description: str       # What the tool does
    required_args: Set[str] # Required arguments
```

## Available Agents

### 1. Query Understanding Agent
- **Purpose**: Understands and classifies user queries
- **Capabilities**:
  - Query classification (N, L0, L1_2)
  - Location extraction
  - Query context analysis

### 2. Location Processing Agent
- **Purpose**: Handles location-based operations
- **Capabilities**:
  - Distance-based filtering
  - Location type filtering
  - Distance sorting
  - Bounding box calculation
  - Location clustering
  - Geocoding/reverse geocoding

### 3. Spatial Analysis Agent
- **Purpose**: Performs spatial analysis on location data
- **Capabilities**:
  - Geometry operations
  - Spatial relationships
  - Area calculations
  - Distance measurements

### 4. Code Generation Agent
- **Purpose**: Generates code for data processing
- **Capabilities**:
  - SQL query generation
  - Data transformation code
  - Analysis script generation

### 5. Code Execution Agent
- **Purpose**: Safely executes generated code
- **Capabilities**:
  - Code validation
  - Sandboxed execution
  - Result formatting

### 6. Response Generation Agent
- **Purpose**: Generates human-readable responses
- **Capabilities**:
  - Result summarization
  - Natural language generation
  - Context-aware responses

## Usage Example

```python
# Initialize an agent
agent = LocationProcessingAgent(model)

# Check capabilities
capabilities = agent.get_capabilities()

# Process a goal
result = await agent.process(
    goal="find coffee shops within 5km of current location",
    locations=locations,
    center=(lat, lon),
    radius_km=5
)

# Check agent state
state = agent.get_state()
print(f"Status: {state.status}")
print(f"Last action: {state.last_action}")
print(f"Memory: {state.memory}")
```

## Tool Development
To add new tools to an agent:

1. Create tool function in appropriate utils module
2. Register tool with agent:
```python
self.register_tool(
    name="tool_name",
    func=tool_function,
    description="What the tool does",
    required_args={"arg1", "arg2"}
)
```

## Testing
Tests are available in the `tests/agents` directory:
- Unit tests for each agent
- Integration tests for agent interactions
- Tool validation tests
- State management tests

## Error Handling
Agents provide comprehensive error handling:
- Tool validation errors
- Execution errors
- State management errors
- Memory management errors

## Best Practices
1. Always check agent capabilities before use
2. Provide all required arguments for tools
3. Handle agent states appropriately
4. Clean up resources after use
5. Monitor agent memory for large datasets 