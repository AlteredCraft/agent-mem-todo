"""Memory tool implementation for Claude Agent SDK."""

import logging
from pathlib import Path

from anthropic.lib.tools import BetaAbstractMemoryTool

logger = logging.getLogger(__name__)


class LocalFilesystemMemoryTool(BetaAbstractMemoryTool):
    """
    File system backend for Claude's memory tool.

    Implements all memory operations with security restrictions
    to the configured memory directory.
    """

    def __init__(self, memory_dir: Path):
        """Initialize the memory tool with a specific directory.

        Args:
            memory_dir: Absolute path to the memory directory
        """
        super().__init__()
        self.memory_dir = memory_dir.absolute()
        logger.info(f"Initialized memory tool with directory: {self.memory_dir}")

    def _validate_path(self, path: str) -> Path:
        """Validate that a path is within the memory directory.

        Args:
            path: Path to validate (should start with /memories)

        Returns:
            Absolute Path object

        Raises:
            ValueError: If path is outside memory directory
        """
        # Remove /memories prefix if present
        if path.startswith("/memories"):
            path = path[len("/memories"):]
        elif path.startswith("memories/"):
            path = path[len("memories/"):]

        # Construct full path
        full_path = (self.memory_dir / path.lstrip("/")).resolve()

        # Security check: ensure path is within memory directory
        try:
            full_path.relative_to(self.memory_dir)
        except ValueError:
            logger.error(f"Path traversal attempt detected: {path}")
            raise ValueError(f"Path must be within memory directory: {path}")

        return full_path

    def view(self, command) -> str:
        """View directory contents or file content.

        Args:
            command: View command with path attribute

        Returns:
            Directory listing or file contents
        """
        try:
            path = command.path if hasattr(command, 'path') else command
            validated_path = self._validate_path(path)
            logger.debug(f"View: {path} -> {validated_path}")

            if not validated_path.exists():
                result = f"Path does not exist: {path}"
                logger.debug(result)
                return result

            if validated_path.is_dir():
                # List directory contents
                contents = []
                for item in sorted(validated_path.iterdir()):
                    item_type = "DIR" if item.is_dir() else "FILE"
                    rel_path = item.relative_to(self.memory_dir)
                    contents.append(f"{item_type}: /memories/{rel_path}")

                if not contents:
                    result = f"Directory is empty: {path}"
                else:
                    result = "\n".join(contents)

                logger.debug(f"Listed directory with {len(contents)} items")
                return result
            else:
                # Read file contents
                content = validated_path.read_text(encoding="utf-8")
                logger.debug(f"Read file: {len(content)} characters")
                return content

        except Exception as e:
            logger.error(f"View failed: {e}", exc_info=True)
            return f"Error viewing {path}: {str(e)}"

    def create(self, command) -> str:
        """Create or overwrite a file.

        Args:
            command: Create command with path and file_text attributes

        Returns:
            Success message
        """
        try:
            path = command.path
            content = command.file_text
            validated_path = self._validate_path(path)
            logger.debug(f"Create: {path} -> {validated_path}")

            # Create parent directories if needed
            validated_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            validated_path.write_text(content, encoding="utf-8")

            result = f"Created file: {path}"
            logger.info(f"Created file: {validated_path} ({len(content)} characters)")
            return result

        except Exception as e:
            logger.error(f"Create failed: {e}", exc_info=True)
            return f"Error creating {path}: {str(e)}"

    def str_replace(self, command) -> str:
        """Replace a string in a file.

        Args:
            command: StrReplace command with path, old_str, new_str attributes

        Returns:
            Success message
        """
        try:
            path = command.path
            old_str = command.old_str
            new_str = command.new_str
            validated_path = self._validate_path(path)
            logger.debug(f"StrReplace: {path} -> {validated_path}")

            if not validated_path.exists():
                result = f"File does not exist: {path}"
                logger.error(result)
                return result

            # Read current content
            content = validated_path.read_text(encoding="utf-8")

            # Check if old string exists
            if old_str not in content:
                result = f"String not found in file: {old_str}"
                logger.warning(result)
                return result

            # Replace string
            new_content = content.replace(old_str, new_str, 1)

            # Write back
            validated_path.write_text(new_content, encoding="utf-8")

            result = f"Replaced string in {path}"
            logger.info(f"Replaced string in {validated_path}")
            return result

        except Exception as e:
            logger.error(f"StrReplace failed: {e}", exc_info=True)
            return f"Error replacing string in {path}: {str(e)}"

    def insert(self, command) -> str:
        """Insert text at a specific line in a file.

        Args:
            command: Insert command with path, insert_line, new_str attributes

        Returns:
            Success message
        """
        try:
            path = command.path
            insert_line = command.insert_line
            new_str = command.new_str
            validated_path = self._validate_path(path)
            logger.debug(f"Insert: {path} -> {validated_path} at line {insert_line}")

            if not validated_path.exists():
                result = f"File does not exist: {path}"
                logger.error(result)
                return result

            # Read current lines
            lines = validated_path.read_text(encoding="utf-8").splitlines(keepends=True)

            # Insert new content
            if insert_line < 0 or insert_line > len(lines):
                result = f"Invalid line number: {insert_line}"
                logger.error(result)
                return result

            lines.insert(insert_line, new_str + "\n")

            # Write back
            validated_path.write_text("".join(lines), encoding="utf-8")

            result = f"Inserted text at line {insert_line} in {path}"
            logger.info(f"Inserted text at line {insert_line} in {validated_path}")
            return result

        except Exception as e:
            logger.error(f"Insert failed: {e}", exc_info=True)
            return f"Error inserting text in {path}: {str(e)}"

    def delete(self, command) -> str:
        """Delete a file or directory.

        Args:
            command: Delete command with path attribute

        Returns:
            Success message
        """
        try:
            path = command.path
            validated_path = self._validate_path(path)
            logger.debug(f"Delete: {path} -> {validated_path}")

            if not validated_path.exists():
                result = f"Path does not exist: {path}"
                logger.warning(result)
                return result

            if validated_path.is_dir():
                # Delete directory and contents
                import shutil
                shutil.rmtree(validated_path)
                result = f"Deleted directory: {path}"
                logger.info(f"Deleted directory: {validated_path}")
            else:
                # Delete file
                validated_path.unlink()
                result = f"Deleted file: {path}"
                logger.info(f"Deleted file: {validated_path}")

            return result

        except Exception as e:
            logger.error(f"Delete failed: {e}", exc_info=True)
            return f"Error deleting {path}: {str(e)}"

    def rename(self, command) -> str:
        """Rename or move a file/directory.

        Args:
            command: Rename command with old_path, new_path attributes

        Returns:
            Success message
        """
        try:
            old_path = command.old_path
            new_path = command.new_path
            validated_old_path = self._validate_path(old_path)
            validated_new_path = self._validate_path(new_path)
            logger.debug(f"Rename: {old_path} -> {new_path}")

            if not validated_old_path.exists():
                result = f"Source path does not exist: {old_path}"
                logger.error(result)
                return result

            # Create parent directory for new path if needed
            validated_new_path.parent.mkdir(parents=True, exist_ok=True)

            # Rename/move
            validated_old_path.rename(validated_new_path)

            result = f"Renamed {old_path} to {new_path}"
            logger.info(f"Renamed {validated_old_path} to {validated_new_path}")
            return result

        except Exception as e:
            logger.error(f"Rename failed: {e}", exc_info=True)
            return f"Error renaming {old_path}: {str(e)}"
