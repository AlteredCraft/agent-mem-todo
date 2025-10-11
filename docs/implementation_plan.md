# Implementation Plan

## Project Overview

Build a minimal POC CLI todo application that uses Claude's Memory Tool for persistence, allowing the LLM to autonomously decide how to organize and store todo data.

## Core Principle

**Let Claude decide the storage implementation.** We provide no guidance on file structure, naming conventions, or data format. The system prompt focuses on capabilities (remember, update, report) rather than implementation details.

## Architecture

### 1. Memory Tool Backend (`memory_tool.py`)

**Purpose**: Implement the file system backend for Claude's memory operations.

**Implementation**:
- Inherit from `anthropic.lib.tools.BetaAbstractMemoryTool`
- Implement required methods for memory operations:
  - `view`: List directory contents or read file
  - `create`: Create/overwrite files
  - `str_replace`: Replace text in files
  - `insert`: Insert text at specific line
  - `delete`: Remove files/directories
  - `rename`: Move/rename files
- Security: Restrict all operations to configured memory directory
- Logging: DEBUG level logs for every memory operation Claude requests

**Key Design Decisions**:
- Use absolute paths internally, validate all paths
- Prevent directory traversal attacks
- Return detailed error messages to Claude when operations fail
- Log both the operation request and result

### 2. Configuration (`config.py`)

**Purpose**: Centralized configuration with sensible defaults.

**Settings**:
```python
MEMORY_DIR = os.getenv("MEMORY_DIR", "./memories")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"
```

**Features**:
- Environment variable overrides
- Path validation and creation
- Configuration validation on startup

### 3. Main Agent (`todo_agent.py`)

**Purpose**: CLI chat loop integrating Claude API with memory tool.

**Components**:

#### System Prompt
```
You are a helpful assistant helping the user to store and recall the tasks
they need to accomplish. It's important you remember any tasks the user needs
to remember. Ensure you can update the progress on tasks. Ensure you can
report the state of a task to the user.
```

**Key**: No mention of memory implementation, file structures, or storage details.

#### Chat Loop
1. Initialize Anthropic client
2. Initialize memory tool with configured directory
3. Setup context management (from SDK example)
4. Infinite loop:
   - Get user input
   - Handle `/quit` command
   - Append user message to conversation history
   - Call `client.beta.messages.tool_runner()` with:
     - Model: Claude Sonnet 4
     - System prompt
     - Messages array
     - Tools: `[memory_tool]`
     - Context management config
   - Stream/collect response
   - Display assistant response
   - Log all tool uses at DEBUG level

#### Logging Strategy
- INFO: User messages, assistant responses, session start/end
- DEBUG: Tool invocations, memory operations, API calls
- ERROR: API errors, tool failures, validation errors
- Use structured logging with context (conversation turn, tool name, operation type)

#### Error Handling
- API errors: Log and display user-friendly message
- Tool errors: Let Claude see error and retry/adapt
- Keyboard interrupt: Clean exit
- Invalid input: Pass through to Claude (let it handle)

### 4. Evaluation Suite (`eval.py`)

**Purpose**: Simple test suite to validate core functionality.

**Test Cases**:

1. **Add Todo**
   - Prompt: "Add a task to buy milk"
   - Expected: Success confirmation, memory write occurs

2. **List Todos**
   - Prompt: "What tasks do I have?"
   - Expected: Lists the milk task

3. **Update Todo**
   - Prompt: "Actually, make that buy oat milk instead"
   - Expected: Task updated in memory

4. **Mark Complete**
   - Prompt: "Mark the milk task as done"
   - Expected: Status updated, confirmation

5. **List After Completion**
   - Prompt: "Show my tasks"
   - Expected: Shows completed status or filters out

6. **Add Multiple**
   - Prompt: "Add tasks: walk the dog, call dentist, finish report"
   - Expected: Multiple tasks added

7. **Persistence Check**
   - Action: Restart agent, ask "What tasks do I have?"
   - Expected: Previously added tasks still present

**Implementation**:
- Automated test runner that:
  - Spawns agent sessions
  - Sends test prompts
  - Validates responses (using LLM to check if expectations met)
  - Reports pass/fail
  - Checks memory directory contents between sessions

**Output**:
```
Running Todo Agent Evaluation Suite
====================================

Test 1: Add Todo ... PASS (0.8s)
Test 2: List Todos ... PASS (0.6s)
Test 3: Update Todo ... PASS (0.9s)
Test 4: Mark Complete ... PASS (0.7s)
Test 5: List After Completion ... PASS (0.6s)
Test 6: Add Multiple ... PASS (1.2s)
Test 7: Persistence Check ... PASS (1.1s)

Memory Structure Observations:
- Files created: /memories/todos.json
- Format: JSON array with objects
- Fields observed: description, status, created_at

7/7 tests passed
```

## Implementation Steps

1. ✅ Create README.md
2. ✅ Create implementation_plan.md (this file)
3. Initialize uv project:
   - Run `uv init`
   - Add anthropic SDK dependency
   - Configure pyproject.toml for Python 3.13
4. Create `.gitignore`:
   - Ignore `/memories`
   - Standard Python ignores
5. Implement `config.py`:
   - Environment-based configuration
   - Path validation
6. Implement `memory_tool.py`:
   - Extend BetaAbstractMemoryTool
   - Implement all memory operations
   - Add security checks and logging
7. Implement `todo_agent.py`:
   - Setup logging
   - Initialize client and tool
   - Build chat loop
   - Handle streaming responses
8. Implement `eval.py`:
   - Test case definitions
   - Automated runner
   - Result reporting

## Success Criteria

- ✅ User can add, list, update, complete todos via natural language
- ✅ Claude autonomously manages storage (we observe, don't prescribe)
- ✅ Todos persist across sessions
- ✅ All eval tests pass
- ✅ Comprehensive DEBUG logging shows Claude's memory decisions
- ✅ Zero database infrastructure required

## Experimental Observations to Track

During implementation and testing, document:

1. **Storage Patterns**:
   - What file structure does Claude create?
   - Single file vs multiple files?
   - What format? (JSON, plain text, markdown?)
   - How does it name files?

2. **Data Organization**:
   - What fields does Claude track for todos?
   - How does it represent status/completion?
   - Does it add timestamps, IDs, priorities?

3. **Memory Tool Usage**:
   - Which memory operations does Claude use most?
   - Does it read before write?
   - How does it handle updates (replace file vs str_replace)?
   - Does it create backups or version files?

4. **Natural Language Understanding**:
   - How well does it interpret vague commands?
   - Does it ask for clarification when needed?
   - Can it handle bulk operations ("add 5 tasks")?
   - How does it handle ambiguity ("the milk task" when there are multiple)?

5. **Edge Cases**:
   - What happens with empty memory on first run?
   - How does it handle corrupted memory files?
   - Does it recover from failed operations?
   - What's the behavior with conflicting commands?

6. **Performance**:
   - Response time for operations
   - Number of API calls per operation
   - Memory directory size growth

## Future Enhancements (Out of Scope for POC)

- Web interface
- Multi-user support
- Task sharing/collaboration
- Reminders and due dates
- Task prioritization
- Search and filtering
- Export/import functionality
- Memory optimization strategies
- Comparison with traditional DB approach (LOC, complexity, performance)

## Resources

- [Claude Memory Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)
- [Python SDK Memory Example](https://github.com/anthropics/anthropic-sdk-python/blob/main/examples/memory/basic.py)
- [uv Project Guide](https://docs.astral.sh/uv/guides/projects/)
