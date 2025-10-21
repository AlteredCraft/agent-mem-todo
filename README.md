# Agent Memory Todo App

An experimental CLI todo application that uses [Claude's Memory Tool](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool) for persistence instead of a traditional database.
This goals here is strictly to explore, see how Claude aproaches the problem, and learn from the experience.
We give Claude a minimal system prompt and let it figure out how to organize and store todo data on its own.
We leverage the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview) to facilitate this process.
We want to see if we can reduce code by offloading more responsibility to the LLM (and aligning with the system prompt).


## The Experiment

**Traditional Approach:**
- Database (PostgreSQL, SQLite, etc.)
- Schema design
- ORM/query layer
- Migration management

**Memory Tool Approach:**
- Claude's memory tool for storage
- LLM decides data organization
- Natural language interface
- Zero schema management

## Features

- **Natural Language Interface**: Add, view, update, and complete todos using conversational commands
- **Autonomous Storage**: Claude decides how to structure and store todo data in memory
- **Zero Infrastructure**: No database setup or management required
- **Configurable Memory**: Customizable storage location (defaults to `./memories`)

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Configure API key
cp dist.env .env
# Edit .env and add your Anthropic API key from https://console.anthropic.com/

# 3. Run the app
./run.sh
```

## Usage

Simply chat with the agent using natural language. Type `/quit` to exit.

### Example Session

```
You: Add a task to buy groceries
Agent: I've added "buy groceries" to your tasks.

You: Add tasks to call mom and finish the report
Agent: I've added both tasks for you.

You: What do I need to do?
Agent: You have 3 tasks: buy groceries, call mom, and finish the report.

You: Mark the groceries task as done
Agent: Done! I've marked "buy groceries" as complete.

You: Show my remaining tasks
Agent: You have 2 pending tasks: call mom and finish the report.

You: /quit
Goodbye!
```

### Tips

- **Be natural**: Talk to the agent like you would a human assistant
- **Be specific**: "Mark the first task as done" works better than "mark it done"
- **Inspect memory**: Look at `./memories/` to see how Claude organized your todos
- **Adjust logging**: Set `LOG_LEVEL=INFO` in `.env` for less verbose output

### Experiment Ideas

Try asking:
- "Add 5 tasks for tomorrow"
- "What's the most urgent task?"
- "Organize my tasks by priority"
- "Delete all completed tasks"
- "Export my todos"

See how Claude interprets and handles these requests!

## Configuration

Edit your `.env` file to customize settings:

```bash
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=your-api-key-here

# Optional: Memory storage directory (default: ./memories)
MEMORY_DIR=./memories

# Optional: Log level (default: DEBUG)
# Options: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=DEBUG
```

You can also use environment variables which will override `.env` settings.

See [dist.env](dist.env) for the template and [config.py](config.py) for all available options.

## Testing

Run the evaluation suite to test core functionality:

```bash
uv run python eval.py
```

The eval suite runs 7 automated tests:
- Adding todos
- Listing todos
- Updating todo status
- Marking todos complete
- Adding multiple tasks at once
- Memory persistence across sessions

It also analyzes how Claude organized the data in memory.

## Project Structure

```
agent-mem-todo/
├── README.md              # This file
├── dist.env               # Configuration template
├── run.sh                 # Quick start script
├── config.py              # Configuration module
├── memory_tool.py         # Memory tool implementation
├── todo_agent.py          # Main CLI application
├── eval.py                # Evaluation suite
└── docs/
    ├── implementation_plan.md
    └── build_summary.md
```

## How It Works

1. **User Input**: Natural language commands via CLI
2. **Claude Processing**: Agent interprets intent and decides actions
3. **Memory Operations**: Claude autonomously uses memory tool (create, view, update files)
4. **Backend Execution**: Our implementation handles actual file I/O
5. **Response**: Agent reports results to user

**The magic**: We never told Claude *how* to store todos. It figures out the organization on its own!

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Make sure you created `.env` file: `cp dist.env .env`
- Edit `.env` and add your API key
- Alternatively, export it: `export ANTHROPIC_API_KEY="your-key"`

**"Module not found"**
- Run `uv sync` to install dependencies

**"Permission denied: ./run.sh"**
- Make it executable: `chmod +x run.sh`

## Observations & Learnings

This section will document interesting behaviors observed during the experiment:
- How Claude organizes todo data (file structure, format)
- Natural language understanding effectiveness
- Memory tool usage patterns
- Edge cases and limitations

## Further Reading

- [docs/implementation_plan.md](docs/implementation_plan.md) - Detailed architecture and design
- [docs/build_summary.md](docs/build_summary.md) - What we built and why
- [dist.env](dist.env) - Configuration template

## License

MIT

## Resources

- [Claude Memory Tool Documentation](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Memory Tool Example](https://github.com/anthropics/anthropic-sdk-python/blob/main/examples/memory/basic.py)
