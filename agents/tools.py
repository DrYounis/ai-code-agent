"""
Custom tools for the Coder and Reviewer agents
"""
import os
import subprocess
from pathlib import Path
from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class WriteFileInput(BaseModel):
    """Input schema for WriteFileTool"""
    filepath: str = Field(..., description="Path to the file to write (relative to output directory)")
    content: str = Field(..., description="Content to write to the file")


class WriteFileTool(BaseTool):
    name: str = "Write File"
    description: str = "Write content to a file in the output directory. Creates parent directories if needed."
    args_schema: Type[BaseModel] = WriteFileInput
    
    def _run(self, filepath: str, content: str) -> str:
        """Write content to a file"""
        try:
            # Ensure we're writing to the output directory
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            full_path = output_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"✅ Successfully wrote {len(content)} characters to {full_path}"
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"


class ReadFileInput(BaseModel):
    """Input schema for ReadFileTool"""
    filepath: str = Field(..., description="Path to the file to read (relative to output directory)")


class ReadFileTool(BaseTool):
    name: str = "Read File"
    description: str = "Read content from a file in the output directory."
    args_schema: Type[BaseModel] = ReadFileInput
    
    def _run(self, filepath: str) -> str:
        """Read content from a file"""
        try:
            output_dir = Path("output")
            full_path = output_dir / filepath
            
            if not full_path.exists():
                return f"❌ File not found: {full_path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"


# ── Security: allowed commands for RunCommandTool ─────────────────────────────
# shell=True with arbitrary input is a command injection risk.
# We use an allowlist of safe prefixes and validate working_dir to prevent traversal.
_ALLOWED_COMMAND_PREFIXES = (
    "python", "python3", "pip", "pip3",
    "pylint", "flake8", "black", "isort", "mypy", "ruff",
    "pytest", "unittest",
    "node", "npm", "npx", "eslint", "tsc",
    "git diff", "git log", "git status",
    "ls", "cat", "head", "tail", "wc",
)

_BLOCKED_PATTERNS = (
    "rm ", "rmdir", "mv ", "cp ", "chmod", "chown",
    "curl", "wget", "ssh", "scp", "nc ", "netcat",
    "sudo", "su ", ">", ">>", "|", "&", ";",
    "$(", "`", "eval", "exec",
)


class RunCommandInput(BaseModel):
    """Input schema for RunCommandTool"""
    command: str = Field(..., description="Shell command to execute (linting, testing only)")
    working_dir: str = Field(default="output", description="Working directory (must be inside output/)")


class RunCommandTool(BaseTool):
    name: str = "Run Command"
    description: str = (
        "Execute safe shell commands: linting (pylint, flake8, black, ruff), "
        "testing (pytest), or git read-only (git diff, git log). "
        "Destructive commands (rm, curl, sudo, etc.) are blocked."
    )
    args_schema: Type[BaseModel] = RunCommandInput

    def _validate_command(self, command: str) -> str | None:
        """Return error string if command is not allowed, else None."""
        cmd_lower = command.strip().lower()
        # Check blocked patterns first
        for blocked in _BLOCKED_PATTERNS:
            if blocked in cmd_lower:
                return f"Command blocked: contains forbidden pattern '{blocked}'"
        # Check allowlist
        if not any(cmd_lower.startswith(prefix) for prefix in _ALLOWED_COMMAND_PREFIXES):
            return f"Command not in allowlist. Permitted: {', '.join(_ALLOWED_COMMAND_PREFIXES)}"
        return None

    def _validate_working_dir(self, working_dir: str) -> tuple[Path, str | None]:
        """Validate working_dir is inside output/. Returns (path, error_or_None)."""
        output_root = Path("output").resolve()
        try:
            target = (output_root / working_dir).resolve()
            # Prevent path traversal
            target.relative_to(output_root)
            return target, None
        except ValueError:
            return output_root, f"Path traversal blocked: '{working_dir}' must be inside output/"

    def _run(self, command: str, working_dir: str = "output") -> str:
        """Execute a sandboxed shell command"""
        # Validate command
        cmd_error = self._validate_command(command)
        if cmd_error:
            return f"❌ Security block: {cmd_error}"

        # Validate working directory
        cwd, dir_error = self._validate_working_dir(working_dir)
        if dir_error:
            return f"❌ Security block: {dir_error}"

        if not cwd.exists():
            cwd.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                command.split(),  # NO shell=True — avoids shell injection
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            status = "✅ Success" if result.returncode == 0 else f"⚠️ Exit code: {result.returncode}"
            return f"{status}\n\nOutput:\n{output[:4000]}"  # Truncate large output
        except subprocess.TimeoutExpired:
            return "❌ Command timed out after 30 seconds"
        except FileNotFoundError:
            return f"❌ Command not found: {command.split()[0]}"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"


class ListFilesInput(BaseModel):
    """Input schema for ListFilesTool"""
    directory: str = Field(default=".", description="Directory to list (relative to output)")


class ListFilesTool(BaseTool):
    name: str = "List Files"
    description: str = "List all files in a directory within the output folder."
    args_schema: Type[BaseModel] = ListFilesInput
    
    def _run(self, directory: str = ".") -> str:
        """List files in a directory"""
        try:
            output_dir = Path("output")
            target_dir = output_dir / directory
            
            if not target_dir.exists():
                return f"❌ Directory not found: {target_dir}"
            
            files = []
            for item in target_dir.rglob("*"):
                if item.is_file():
                    relative_path = item.relative_to(output_dir)
                    size = item.stat().st_size
                    files.append(f"  • {relative_path} ({size} bytes)")
            
            if not files:
                return "📁 Directory is empty"
            
            return "📁 Files:\n" + "\n".join(files)
        except Exception as e:
            return f"❌ Error listing files: {str(e)}"


# Export all tools
def get_coder_tools():
    """Get tools for the Coder agent"""
    return [
        WriteFileTool(),
        ReadFileTool(),
        ListFilesTool(),
    ]


def get_reviewer_tools():
    """Get tools for the Reviewer agent"""
    return [
        ReadFileTool(),
        RunCommandTool(),
        ListFilesTool(),
    ]
