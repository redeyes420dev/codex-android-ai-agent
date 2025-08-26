"""Codex CLI integration commands."""

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional, List
from pathlib import Path
import subprocess
import json

codex_app = typer.Typer(help="🔧 Codex CLI integration and automation")
console = Console()

@codex_app.command()
def suggest(
    prompt: str = typer.Argument(..., help="Code suggestion prompt"),
    file_path: Optional[Path] = typer.Option(None, "--file", "-f", help="Target file for suggestion"),
    lang: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language"),
    apply: bool = typer.Option(False, "--apply", help="Auto-apply suggestion")
):
    """Generate code suggestions using Codex CLI."""
    try:
        cmd = ["codex", "suggest", prompt]
        
        if file_path:
            cmd.extend(["--file", str(file_path)])
        if lang:
            cmd.extend(["--language", lang])
        if apply:
            cmd.append("--apply")
        
        console.print(f"🤖 Generating suggestion with Codex CLI...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ Codex suggestion generated:")
            console.print(Panel(result.stdout, title="💡 Suggestion"))
            if apply and file_path:
                console.print(f"✅ Applied to: {file_path}")
        else:
            console.print("❌ Codex CLI error:")
            console.print(result.stderr)
            
    except FileNotFoundError:
        console.print("❌ Codex CLI not found. Please install it first.")
        console.print("Visit: https://docs.anthropic.com/claude/docs/codex-cli")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def auto_edit(
    file_path: Path = typer.Argument(..., help="File to edit"),
    instruction: str = typer.Argument(..., help="Edit instruction"),
    backup: bool = typer.Option(True, "--backup", help="Create backup"),
    preview: bool = typer.Option(False, "--preview", help="Preview changes only")
):
    """Auto-edit files using Codex CLI."""
    try:
        if not file_path.exists():
            console.print(f"❌ File not found: {file_path}")
            return
        
        cmd = ["codex", "edit", str(file_path), instruction]
        
        if backup:
            cmd.append("--backup")
        if preview:
            cmd.append("--preview")
        
        console.print(f"🔧 Auto-editing: {file_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if preview:
                console.print("📋 Preview of changes:")
                console.print(Panel(result.stdout, title="🔍 Changes"))
            else:
                console.print("✅ File edited successfully")
                if result.stdout:
                    console.print(result.stdout)
        else:
            console.print("❌ Edit failed:")
            console.print(result.stderr)
            
    except FileNotFoundError:
        console.print("❌ Codex CLI not found")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def full_auto(
    project_path: Path = typer.Argument(..., help="Project directory"),
    task: str = typer.Argument(..., help="Task description"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Codex config file"),
    quiet: bool = typer.Option(False, "--quiet", help="Quiet mode for CI")
):
    """Full auto mode - let Codex handle complex tasks."""
    try:
        if not project_path.exists():
            console.print(f"❌ Project path not found: {project_path}")
            return
        
        cmd = ["codex", "full-auto", str(project_path), task]
        
        if config_file:
            cmd.extend(["--config", str(config_file)])
        if quiet:
            cmd.append("--quiet")
        
        console.print(f"🚀 Starting full-auto mode...")
        console.print(f"📁 Project: {project_path}")
        console.print(f"📋 Task: {task}")
        
        if quiet:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                console.print("✅ Task completed successfully")
                if result.stdout:
                    try:
                        output_data = json.loads(result.stdout)
                        console.print(json.dumps(output_data, indent=2))
                    except json.JSONDecodeError:
                        console.print(result.stdout)
            else:
                console.print("❌ Task failed:")
                console.print(result.stderr)
        else:
            # Interactive mode
            subprocess.run(cmd)
            
    except FileNotFoundError:
        console.print("❌ Codex CLI not found")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def status():
    """Check Codex CLI installation and status."""
    try:
        result = subprocess.run(["codex", "--version"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ Codex CLI is installed")
            console.print(f"Version: {result.stdout.strip()}")
            
            # Check configuration
            config_result = subprocess.run(["codex", "config", "list"], capture_output=True, text=True)
            if config_result.returncode == 0:
                console.print("\n📝 Current Configuration:")
                console.print(config_result.stdout)
        else:
            console.print("❌ Codex CLI not properly installed")
            
    except FileNotFoundError:
        console.print("❌ Codex CLI not found")
        console.print("\n💡 Install Codex CLI:")
        console.print("1. Visit: https://docs.anthropic.com/claude/docs/codex-cli")
        console.print("2. Follow installation instructions")
        console.print("3. Configure with: codex config set")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def init_project(
    project_path: Path = typer.Argument(..., help="Project directory"),
    android_focused: bool = typer.Option(True, "--android", help="Android-specific setup"),
    create_codex_md: bool = typer.Option(True, "--codex-md", help="Create codex.md instructions")
):
    """Initialize project with Codex CLI integration."""
    try:
        if not project_path.exists():
            console.print(f"❌ Project path not found: {project_path}")
            return
        
        console.print(f"🚀 Initializing Codex integration in: {project_path}")
        
        # Create codex.md with Android-specific instructions
        if create_codex_md:
            codex_md_path = project_path / "codex.md"
            
            codex_instructions = """# Codex Instructions for Android Development

## Project Context
This is an Android development project using CADX (Codex-Android-AI-Agent).

## Code Style Guidelines
- Follow Android Kotlin style guide
- Use meaningful variable and function names  
- Add KDoc comments for public APIs
- Prefer Kotlin coroutines over callbacks

## Android Specific Rules
- Use ViewBinding instead of findViewById
- Implement proper lifecycle management
- Handle configuration changes properly
- Use Android Architecture Components (ViewModel, LiveData, Room)
- Follow Material Design principles

## Build System
- Use Gradle Kotlin DSL when possible
- Keep dependencies up to date
- Use version catalogs for dependency management

## Testing
- Write unit tests with JUnit and Mockk
- Use Espresso for UI tests
- Aim for >80% code coverage

## Common Tasks
- When adding new features, create proper separation of concerns
- Always handle errors gracefully with try-catch or Result types
- Use proper logging with Timber or similar
- Implement offline-first architecture when applicable

## CADX Integration
- Use `cadx android logcat-analyze` for log analysis
- Use `cadx agents fix-code` for automated code fixes
- Use `cadx codex suggest` for code suggestions
"""
            
            if android_focused:
                with open(codex_md_path, 'w') as f:
                    f.write(codex_instructions)
                console.print(f"✅ Created: {codex_md_path}")
        
        # Initialize Codex CLI in project
        cmd = ["codex", "init", str(project_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ Codex CLI initialized successfully")
            console.print("\n💡 Next steps:")
            console.print("1. Configure API keys: codex config set")
            console.print("2. Test integration: cadx codex status")
            console.print("3. Start using: cadx codex suggest 'your prompt'")
        else:
            console.print("❌ Codex init failed:")
            console.print(result.stderr)
            
    except FileNotFoundError:
        console.print("❌ Codex CLI not found")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def task_pack(
    pack_name: str = typer.Argument(..., help="Task pack name"),
    project_path: Optional[Path] = typer.Option(None, "--project", help="Project directory"),
    list_packs: bool = typer.Option(False, "--list", help="List available task packs")
):
    """Execute predefined task packs."""
    try:
        if list_packs:
            from examples.task_packs import list_available_packs
            packs = list_available_packs()
            
            console.print("📦 Available Task Packs:")
            for pack in packs:
                console.print(f"  • {pack['name']}: {pack['description']}")
            return
        
        from examples.task_packs import execute_task_pack
        
        console.print(f"📦 Executing task pack: {pack_name}")
        if project_path:
            console.print(f"📁 Project: {project_path}")
        
        result = execute_task_pack(pack_name, project_path)
        
        if result["success"]:
            console.print("✅ Task pack completed successfully")
            if result.get("output"):
                console.print(result["output"])
        else:
            console.print(f"❌ Task pack failed: {result.get('error')}")
            
    except ImportError as e:
        console.print(f"❌ Task packs module not available: {e}")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@codex_app.command()
def quiet_mode(
    command: str = typer.Argument(..., help="Codex command to run in quiet mode"),
    json_output: bool = typer.Option(True, "--json", help="JSON output format"),
    timeout: Optional[int] = typer.Option(300, "--timeout", help="Command timeout in seconds")
):
    """Run Codex CLI commands in quiet mode for CI/CD."""
    try:
        cmd = ["codex", "--quiet"]
        if json_output:
            cmd.append("--json")
        
        cmd.extend(command.split())
        
        console.print(f"🤫 Running in quiet mode: {command}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            if json_output:
                try:
                    output_data = json.loads(result.stdout)
                    console.print(json.dumps(output_data, indent=2))
                except json.JSONDecodeError:
                    console.print(result.stdout)
            else:
                console.print(result.stdout)
        else:
            console.print(f"❌ Command failed (exit code {result.returncode})")
            if result.stderr:
                console.print(result.stderr)
                
    except subprocess.TimeoutExpired:
        console.print(f"❌ Command timed out after {timeout} seconds")
    except FileNotFoundError:
        console.print("❌ Codex CLI not found")
    except Exception as e:
        console.print(f"❌ Error: {e}")