# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

review what skills you have acces to in order to fulfill user requests

## Project Overview

Agent Memory Todo is an experimental CLI application that uses Claude's Memory Tool for persistence instead of a traditional database. This is a research project exploring how Claude autonomously organizes todo data when given minimal constraints.

**Key Insight**: The system prompt in config.py is intentionally capability-focused rather than prescriptive. Claude decides the data organization structure, file formats, and storage patterns on its own. This autonomy is a core feature of the experiment.

## Development Commands

### Setup
```bash
# Install dependencies
uv sync

# Configure environment
cp dist.env .env
# Edit .env and add ANTHROPIC_API_KEY from https://console.anthropic.com/
```

### Running the Application
```bash
# Quick start (checks for .env file)
./run.sh

# Direct execution
uv run python todo_agent.py
```

### Testing
```bash
# Run full evaluation suite (7 automated tests)
uv run python eval.py

# Run with debug logging
EVAL_DEBUG=1 uv run python eval.py
```

### Running Individual Files
```bash
# Run any Python file directly
uv run python <filename>.py
```

## Architecture

### Core Components

**todo_agent.py** - Main CLI application
- `TodoAgent` class manages the conversation loop
- Uses Anthropic's `beta.messages.tool_runner` for automatic tool execution
- Maintains conversation history as `List[MessageParam]`
- Pure natural language interface (no rigid commands except `/quit`)

**memory_tool.py** - Memory tool implementation
- `LocalFilesystemMemoryTool` implements `BetaAbstractMemoryTool` interface
- Handles 6 operations: `view`, `create`, `str_replace`, `insert`, `delete`, `rename`
- All paths restricted to memory directory with traversal protection (`_validate_path`)
- Claude's commands (with attributes like `path`, `file_text`) are transformed into filesystem operations

**config.py** - Configuration management
- Environment variables loaded from `.env` via python-dotenv
- `get_system_prompt()` dynamically injects current date into SYSTEM_PROMPT_TEMPLATE
- Context management config: clears old tool uses at 30k input tokens, keeps last 3
- Uses model: `claude-sonnet-4-20250514` with beta header `context-management-2025-06-27`

**eval.py** - Automated evaluation
- 7 test cases: add, list, update, complete, multi-add, persistence
- LLM-based validation (`validate_with_llm`) checks intent rather than exact wording
- Memory structure analysis observing Claude's autonomous organization choices
- Uses separate `./memories_test` directory (cleaned before each run)

### Data Flow

1. User inputs natural language → `TodoAgent._process_message()`
2. Message added to conversation history → sent to Claude API
3. Claude interprets intent → decides memory operations
4. `tool_runner` automatically executes tool calls → `LocalFilesystemMemoryTool` methods
5. Tool results added to conversation → Claude formulates response
6. Response displayed to user

### Memory Tool Operations

Claude receives command objects from the SDK with specific attributes:
- `view(command)`: command.path
- `create(command)`: command.path, command.file_text
- `str_replace(command)`: command.path, command.old_str, command.new_str
- `insert(command)`: command.path, command.insert_line, command.new_str
- `delete(command)`: command.path
- `rename(command)`: command.old_path, command.new_path

Path handling: Paths like `/memories/todos.json` are normalized to `{MEMORY_DIR}/todos.json`

## Configuration

Environment variables (in `.env`):
- `ANTHROPIC_API_KEY` - **Required** API key
- `MEMORY_DIR` - Storage directory (default: `./memories`)
- `LOG_LEVEL` - Logging verbosity: DEBUG, INFO, WARNING, ERROR (default: DEBUG)

## System Prompt Philosophy

The system prompt in config.py:SYSTEM_PROMPT_TEMPLATE is deliberately minimal:
- Describes capability ("store and recall tasks")
- Emphasizes memory tool usage
- Provides current date
- **Does NOT** specify file formats, schemas, or data structures

This allows Claude to make autonomous decisions about organization. When modifying the system prompt, preserve this autonomy-oriented approach.

## Testing Philosophy

The eval suite validates behavior through LLM-based validation rather than rigid assertions. This accommodates natural language variation while ensuring functional correctness.

Tests are sequential and build on each other within a single session, then a separate persistence test validates cross-session memory.

After tests, `analyze_memory_structure()` inspects the memory directory to observe Claude's organizational choices (file structure, formats, naming conventions).

## Logging

All modules use Python's logging with comprehensive DEBUG statements:
- DEBUG: Tool operations, message processing, detailed flow
- INFO: Major events (initialization, file creation)
- WARNING: Recoverable issues (string not found in str_replace)
- ERROR: Failures with stack traces

Set `LOG_LEVEL=INFO` in `.env` for less verbose output during normal usage.

## Key Design Decisions

**Why tool_runner?** Automatic tool execution with streaming support, handles the tool use loop internally.

**Why beta.messages?** Required for memory tool access and context management features.

**Why LocalFilesystemMemoryTool?** Custom implementation allows inspection of Claude's data organization choices for research purposes.

**Why minimal system prompt?** Core experiment: observe how Claude organizes data with autonomy vs. following prescriptive schemas.

## Common Modifications

**Changing the model**: Update `config.MODEL` (requires compatible beta features)

**Adjusting context management**: Modify `config.CONTEXT_MANAGEMENT` triggers and keep values

**Adding logging**: Import logger via `logger = logging.getLogger(__name__)` and use standard levels

**Modifying memory directory**: Set `MEMORY_DIR` in `.env` or update `config.MEMORY_DIR` default
