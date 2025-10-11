"""Configuration module for the Agent Memory Todo application.

This module provides centralized configuration management for the todo app,
including environment variable loading, logging setup, and system prompts.

The configuration prioritizes environment variables from a .env file, with
sensible defaults for development. Key settings include:
- ANTHROPIC_API_KEY: Required API key for Claude
- MEMORY_DIR: Directory for storing todo data (default: ./memories)
- LOG_LEVEL: Logging verbosity (default: DEBUG)
- MODEL: Claude model to use (default: claude-sonnet-4-20250514)

The system prompt is intentionally capability-focused rather than prescriptive,
allowing Claude to autonomously decide how to organize todo data in memory.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Memory storage directory
MEMORY_DIR = os.getenv("MEMORY_DIR", "./memories")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model to use
MODEL = "claude-sonnet-4-20250514"

# Beta header for memory tool
BETA_HEADER = "context-management-2025-06-27"

# System prompt template - focused on capabilities, not implementation
SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant helping the user to store and recall the tasks they need to accomplish.

Today's date is {current_date}.

When the user mentions tasks they need to do, USE THE MEMORY TOOL to store them persistently. This is critical - always use memory to save tasks.

It's important you remember any tasks the user needs to remember. Ensure you can update the progress on tasks. Ensure you can report the state of a task to the user."""


def get_system_prompt() -> str:
    """Get the system prompt with current date injected.

    Returns:
        System prompt string with today's date
    """
    from datetime import datetime
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return SYSTEM_PROMPT_TEMPLATE.format(current_date=current_date)

# Context management configuration (from SDK example)
CONTEXT_MANAGEMENT = {
    "edits": [{
        "type": "clear_tool_uses_20250919",
        "trigger": {"type": "input_tokens", "value": 30000},
        "keep": {"type": "tool_uses", "value": 3}
    }]
}


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_config():
    """Validate configuration and setup required directories."""
    logger = logging.getLogger(__name__)

    # Check API key
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        raise ValueError(
            "ANTHROPIC_API_KEY must be set in .env file or environment variable.\n"
            "Copy dist.env to .env and add your API key.\n"
            "Get your key at https://console.anthropic.com/"
        )

    # Create memory directory if it doesn't exist
    memory_path = Path(MEMORY_DIR)
    if not memory_path.exists():
        logger.info(f"Creating memory directory: {memory_path.absolute()}")
        memory_path.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Using existing memory directory: {memory_path.absolute()}")

    logger.info(f"Configuration validated successfully")
    logger.debug(f"Memory directory: {memory_path.absolute()}")
    logger.debug(f"Model: {MODEL}")
    logger.debug(f"Log level: {LOG_LEVEL}")


def get_memory_path() -> Path:
    """Get the absolute path to the memory directory."""
    return Path(MEMORY_DIR).absolute()
