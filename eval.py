"""Evaluation suite for the Agent Memory Todo app.

This module provides automated testing for the todo agent, validating core
functionality and observing Claude's autonomous decisions about data organization.

Test Coverage:
The suite includes 7 test cases covering:
1. Adding single todos
2. Listing todos
3. Updating existing todos
4. Marking todos as complete
5. Listing after completion
6. Adding multiple todos in bulk
7. Persistence across sessions

Validation Approach:
Rather than using rigid assertions, tests use LLM-based validation to check if
Claude's responses demonstrate the expected behavior. This allows for natural
language variation while ensuring functional correctness.

Memory Structure Analysis:
After running tests, the suite analyzes the memory directory to observe:
- File structure Claude chose (single file vs. multiple files)
- Data format (JSON, plain text, markdown, etc.)
- Field organization (what metadata Claude tracks)
- Naming conventions

This analysis provides insights into how Claude naturally organizes data when
given autonomy, which is a key aspect of the experiment.

Usage:
    python eval.py

    The suite will:
    - Run all test cases sequentially
    - Display pass/fail for each test
    - Analyze memory structure
    - Report observations and statistics
    - Exit with code 0 if all tests pass, 1 otherwise

Environment:
- Uses a separate ./memories_test directory (cleaned before each run)
- Requires ANTHROPIC_API_KEY in environment or .env file
- Can set EVAL_DEBUG=1 for verbose logging during tests
"""

import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

from anthropic import Anthropic

import config
from memory_tool import LocalFilesystemMemoryTool

# Disable verbose logging during eval unless DEBUG is set
if os.getenv("EVAL_DEBUG"):
    config.setup_logging()
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)


class EvalTestCase:
    """Represents a single evaluation test case."""

    def __init__(
        self,
        name: str,
        prompt: str,
        expected_behavior: str,
        validation_fn=None
    ):
        """Initialize a test case.

        Args:
            name: Test case name
            prompt: User prompt to send to the agent
            expected_behavior: Description of expected behavior
            validation_fn: Optional function to validate the response
        """
        self.name = name
        self.prompt = prompt
        self.expected_behavior = expected_behavior
        self.validation_fn = validation_fn


class TodoEvaluator:
    """Evaluator for the todo agent."""

    def __init__(self, test_memory_dir: str = "./memories_test"):
        """Initialize the evaluator.

        Args:
            test_memory_dir: Directory for test memory (will be cleaned)
        """
        self.test_memory_dir = Path(test_memory_dir)
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.memory_tool = None
        self.messages = []

        # Clean test directory
        if self.test_memory_dir.exists():
            shutil.rmtree(self.test_memory_dir)
        self.test_memory_dir.mkdir(parents=True, exist_ok=True)

    def reset_session(self):
        """Reset the agent session (new conversation)."""
        self.messages = []
        self.memory_tool = LocalFilesystemMemoryTool(self.test_memory_dir)

    def send_message(self, prompt: str) -> str:
        """Send a message to the agent and get response.

        Args:
            prompt: User prompt

        Returns:
            Agent response text
        """
        self.messages.append({"role": "user", "content": prompt})

        runner = self.client.beta.messages.tool_runner(
            model=config.MODEL,
            system=config.SYSTEM_PROMPT,
            messages=self.messages,
            tools=[self.memory_tool],
            context_management=config.CONTEXT_MANAGEMENT,
            max_tokens=4096,
            betas=[config.BETA_HEADER],
        )

        message = runner.get()

        # Extract text
        response_parts = []
        for block in message.content:
            if block.type == "text":
                response_parts.append(block.text)

        self.messages.append({"role": "assistant", "content": message.content})

        return "\n".join(response_parts)

    def validate_with_llm(self, response: str, expected: str) -> bool:
        """Use an LLM to validate if response meets expectations.

        Args:
            response: Agent's response
            expected: Expected behavior description

        Returns:
            True if validation passes
        """
        validation_prompt = f"""You are evaluating a todo app agent's response.

Expected behavior: {expected}

Agent's response: {response}

Does the response demonstrate the expected behavior? Consider the intent and meaning, not exact wording.
Answer with just "YES" or "NO"."""

        result = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": validation_prompt}]
        )

        answer = result.content[0].text.strip().upper()
        return answer == "YES"

    def run_test(self, test: EvalTestCase) -> Dict[str, Any]:
        """Run a single test case.

        Args:
            test: Test case to run

        Returns:
            Test result dictionary
        """
        start_time = time.time()

        try:
            # Send prompt
            response = self.send_message(test.prompt)

            # Validate
            if test.validation_fn:
                passed = test.validation_fn(self, response)
            else:
                # Use LLM validation
                passed = self.validate_with_llm(response, test.expected_behavior)

            duration = time.time() - start_time

            return {
                "name": test.name,
                "passed": passed,
                "duration": duration,
                "response": response,
                "error": None
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Test failed with exception: {e}", exc_info=True)
            return {
                "name": test.name,
                "passed": False,
                "duration": duration,
                "response": None,
                "error": str(e)
            }


def create_test_suite() -> List[EvalTestCase]:
    """Create the evaluation test suite.

    Returns:
        List of test cases
    """
    return [
        EvalTestCase(
            name="Add Todo",
            prompt="Add a task to buy milk",
            expected_behavior="Agent confirms adding a task about buying milk"
        ),
        EvalTestCase(
            name="List Todos",
            prompt="What tasks do I have?",
            expected_behavior="Agent lists the milk task that was previously added"
        ),
        EvalTestCase(
            name="Update Todo",
            prompt="Actually, make that buy oat milk instead",
            expected_behavior="Agent updates the task to specify oat milk"
        ),
        EvalTestCase(
            name="Mark Complete",
            prompt="Mark the milk task as done",
            expected_behavior="Agent marks the task as complete or done"
        ),
        EvalTestCase(
            name="List After Completion",
            prompt="Show my tasks",
            expected_behavior="Agent shows tasks with completion status or filters completed ones"
        ),
        EvalTestCase(
            name="Add Multiple",
            prompt="Add tasks: walk the dog, call dentist, finish report",
            expected_behavior="Agent adds three separate tasks"
        ),
    ]


def run_persistence_test(evaluator: TodoEvaluator) -> Dict[str, Any]:
    """Test persistence across sessions.

    Args:
        evaluator: The evaluator instance

    Returns:
        Test result dictionary
    """
    start_time = time.time()

    try:
        # First session: add a task
        evaluator.reset_session()
        evaluator.send_message("Add a task to review code")

        # Second session: check if it persists
        evaluator.reset_session()
        response = evaluator.send_message("What tasks do I have?")

        # Validate that the task persists
        passed = evaluator.validate_with_llm(
            response,
            "Agent shows the 'review code' task that was added in a previous session"
        )

        duration = time.time() - start_time

        return {
            "name": "Persistence Check",
            "passed": passed,
            "duration": duration,
            "response": response,
            "error": None
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Persistence test failed: {e}", exc_info=True)
        return {
            "name": "Persistence Check",
            "passed": False,
            "duration": duration,
            "response": None,
            "error": str(e)
        }


def analyze_memory_structure(test_memory_dir: Path) -> Dict[str, Any]:
    """Analyze the memory structure created by Claude.

    Args:
        test_memory_dir: Test memory directory

    Returns:
        Analysis dictionary
    """
    analysis = {
        "files": [],
        "total_files": 0,
        "total_dirs": 0,
        "file_formats": set(),
        "observations": []
    }

    for item in test_memory_dir.rglob("*"):
        rel_path = item.relative_to(test_memory_dir)

        if item.is_file():
            analysis["total_files"] += 1

            # Detect format
            suffix = item.suffix.lower()
            if suffix:
                analysis["file_formats"].add(suffix)

            # Read preview
            try:
                content = item.read_text(encoding="utf-8")
                preview = content[:200] + "..." if len(content) > 200 else content

                analysis["files"].append({
                    "path": str(rel_path),
                    "size": len(content),
                    "format": suffix or "no extension",
                    "preview": preview
                })
            except Exception as e:
                analysis["files"].append({
                    "path": str(rel_path),
                    "error": str(e)
                })

        elif item.is_dir():
            analysis["total_dirs"] += 1

    # Generate observations
    if ".json" in analysis["file_formats"]:
        analysis["observations"].append("Uses JSON format")
    if ".txt" in analysis["file_formats"]:
        analysis["observations"].append("Uses plain text format")
    if analysis["total_files"] == 1:
        analysis["observations"].append("Single file storage")
    elif analysis["total_files"] > 1:
        analysis["observations"].append("Multiple file storage")

    return analysis


def main():
    """Run the evaluation suite."""
    print("=" * 60)
    print("Agent Memory Todo - Evaluation Suite")
    print("=" * 60)
    print()

    # Check API key
    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    evaluator = TodoEvaluator()
    test_suite = create_test_suite()

    results = []

    # Run sequential tests (build on each other)
    print("Running sequential tests...")
    evaluator.reset_session()

    for i, test in enumerate(test_suite, 1):
        print(f"  [{i}/{len(test_suite)}] {test.name}...", end=" ", flush=True)
        result = evaluator.run_test(test)
        results.append(result)

        if result["passed"]:
            print(f"✓ PASS ({result['duration']:.1f}s)")
        else:
            print(f"✗ FAIL ({result['duration']:.1f}s)")
            if result["error"]:
                print(f"      Error: {result['error']}")

    # Run persistence test
    print("\nRunning persistence test...")
    print(f"  [*] Persistence Check...", end=" ", flush=True)
    persist_result = run_persistence_test(evaluator)
    results.append(persist_result)

    if persist_result["passed"]:
        print(f"✓ PASS ({persist_result['duration']:.1f}s)")
    else:
        print(f"✗ FAIL ({persist_result['duration']:.1f}s)")
        if persist_result["error"]:
            print(f"      Error: {persist_result['error']}")

    # Analyze memory structure
    print("\n" + "=" * 60)
    print("Memory Structure Analysis")
    print("=" * 60)

    analysis = analyze_memory_structure(evaluator.test_memory_dir)

    print(f"\nFiles created: {analysis['total_files']}")
    print(f"Directories: {analysis['total_dirs']}")
    print(f"Formats: {', '.join(analysis['file_formats']) if analysis['file_formats'] else 'none'}")

    if analysis["files"]:
        print("\nFile details:")
        for file_info in analysis["files"]:
            if "error" in file_info:
                print(f"  - {file_info['path']}: ERROR - {file_info['error']}")
            else:
                print(f"  - {file_info['path']} ({file_info['size']} bytes, {file_info['format']})")
                print(f"    Preview: {file_info['preview'][:100]}...")

    if analysis["observations"]:
        print("\nObservations:")
        for obs in analysis["observations"]:
            print(f"  - {obs}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n{passed}/{total} tests passed ({pass_rate:.0f}%)")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in results:
            if not result["passed"]:
                print(f"  - {result['name']}")
                if result["error"]:
                    print(f"    Error: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
