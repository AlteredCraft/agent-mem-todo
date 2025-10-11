"""Main CLI application for the Agent Memory Todo app.

This module provides an interactive command-line interface for managing todos
through natural language conversations with Claude. The agent uses the memory
tool to persist todo data across sessions.

Architecture:
- TodoAgent class manages the conversation loop and API interactions
- Uses Anthropic's beta tool_runner for automatic tool execution
- Maintains conversation history for context
- Processes user input as natural language (no rigid commands)

The application demonstrates an experimental approach to data persistence where:
1. User expresses intent in natural language ("add task to buy milk")
2. Claude interprets the intent and decides appropriate memory operations
3. Memory tool executes filesystem operations
4. Claude responds with confirmation

Key Features:
- Pure natural language interface (no commands except /quit)
- Autonomous data organization by Claude
- Real-time conversation with tool use
- Comprehensive DEBUG logging for observability
- Graceful error handling and user feedback

Usage:
    python todo_agent.py

    Then interact naturally:
    You: I need to clean the house today
    Agent: [stores task and confirms]
    You: What tasks do I have?
    Agent: [lists tasks from memory]
    You: /quit
"""

import logging
import sys
from typing import List

from anthropic import Anthropic
from anthropic.types import MessageParam

import config
from memory_tool import LocalFilesystemMemoryTool

logger = logging.getLogger(__name__)


class TodoAgent:
    """CLI chat interface for the todo agent."""

    def __init__(self):
        """Initialize the todo agent."""
        # Setup logging
        config.setup_logging()

        # Validate configuration
        config.validate_config()

        # Initialize Anthropic client
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("Initialized Anthropic client")

        # Initialize memory tool
        self.memory_tool = LocalFilesystemMemoryTool(config.get_memory_path())

        # Conversation history
        self.messages: List[MessageParam] = []

        logger.info("Todo agent initialized successfully")

    def run(self):
        """Run the main chat loop."""
        logger.info("Starting todo agent CLI")
        print("=== Agent Memory Todo App ===")
        print("Type your requests in natural language.")
        print("Type '/quit' to exit.\n")

        try:
            while True:
                # Get user input
                try:
                    user_input = input("You: ").strip()
                except EOFError:
                    # Handle Ctrl+D
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                # Check for quit command
                if user_input == "/quit":
                    logger.info("User requested quit")
                    print("Goodbye!")
                    break

                # Log user message
                logger.info(f"User: {user_input}")

                # Add user message to conversation
                self.messages.append({
                    "role": "user",
                    "content": user_input
                })

                # Process with Claude
                try:
                    response_text = self._process_message()
                    print(f"\nAgent: {response_text}\n")
                    logger.info(f"Agent: {response_text}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    print(f"\nError: {e}\n")
                    # Remove the failed message from history
                    self.messages.pop()

        except KeyboardInterrupt:
            logger.info("Interrupted by user (Ctrl+C)")
            print("\n\nGoodbye!")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            print(f"\nUnexpected error: {e}")
            sys.exit(1)
        finally:
            logger.info("Todo agent session ended")

    def _process_message(self) -> str:
        """Process the current message with Claude.

        Returns:
            The agent's response text
        """
        logger.debug(f"Processing message with {len(self.messages)} messages in history")

        # Create tool runner for streaming response with tool use
        runner = self.client.beta.messages.tool_runner(
            model=config.MODEL,
            system=config.get_system_prompt(),
            messages=self.messages,
            tools=[self.memory_tool],
            context_management=config.CONTEXT_MANAGEMENT,
            max_tokens=4096,
            betas=[config.BETA_HEADER],
        )

        # Collect response
        response_text_parts = []

        logger.debug("Starting message processing")

        # Process the message - the runner handles tool execution automatically
        final_message = None
        for message in runner:
            final_message = message

            # Log tool uses
            for block in message.content:
                if block.type == "tool_use":
                    logger.debug(
                        f"Tool use: {block.name} with input: {block.input}"
                    )

        # Extract text content from final message
        if final_message:
            for block in final_message.content:
                if block.type == "text":
                    response_text_parts.append(block.text)

            # Add the final assistant message to conversation history
            self.messages.append({
                "role": "assistant",
                "content": final_message.content
            })

        response_text = "\n".join(response_text_parts)

        if not response_text:
            response_text = "(Agent performed actions without a text response)"

        logger.debug(f"Response collected: {len(response_text)} characters")

        return response_text


def main():
    """Entry point for the application."""
    agent = TodoAgent()
    agent.run()


if __name__ == "__main__":
    main()
