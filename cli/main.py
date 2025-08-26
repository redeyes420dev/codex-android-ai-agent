#!/usr/bin/env python3
"""
Codex-Android-AI-Agent main CLI entry point.

This is an open source tool for Android development automation
using Codex CLI, multi-agent pipelines, and various AI providers.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.commands.android import android_app
from cli.commands.agents import agents_app
from cli.commands.codex import codex_app
from cli.commands.ci import ci_app
from cli.config import Config, load_config

app = typer.Typer(
    name="cadx",
    help="🤖 Codex-Android-AI-Agent: Open source Android development automation",
    add_completion=False,
)

console = Console()

# Add subcommands
app.add_typer(android_app, name="android", help="Android development tools (ADB, fastboot, logcat)")
app.add_typer(agents_app, name="agents", help="AI agents management and multi-provider support")  
app.add_typer(codex_app, name="codex", help="Codex CLI integration and automation")
app.add_typer(ci_app, name="ci", help="CI/CD integration and quiet mode")

@app.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        "🤖 Codex-Android-AI-Agent v0.1.0\n"
        "Open source Android dev automation\n"
        "Codex CLI + Multi-agent pipelines",
        title="Version"
    ))

@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", help="Edit configuration file"),
):
    """Manage configuration."""
    config_obj = load_config()
    
    if show:
        console.print("📝 Current Configuration:")
        console.print(config_obj.model_dump_json(indent=2))
    elif edit:
        config_file = Path.home() / ".cadx" / "config.yaml"
        console.print(f"Edit config file: {config_file}")
        # TODO: Open editor
    else:
        console.print("Use --show or --edit options")

@app.command()  
def status():
    """Show system status and diagnostics."""
    console.print("🔍 System Status:")
    
    # Check dependencies
    try:
        import adb_shell
        console.print("✅ ADB tools available")
    except ImportError:
        console.print("❌ ADB tools not available")
        
    # Check AI providers
    config_obj = load_config()
    for provider in config_obj.ai_providers:
        if provider.api_key:
            console.print(f"✅ {provider.name} configured")
        else:
            console.print(f"❌ {provider.name} not configured")

def main():
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()