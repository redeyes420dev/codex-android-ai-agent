"""AI agents management commands."""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from pathlib import Path

agents_app = typer.Typer(help="🤖 AI agents and multi-provider management")
console = Console()

@agents_app.command()
def list_providers(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """List available AI providers and their status."""
    try:
        from cli.config import load_config
        
        config = load_config()
        
        if json_output:
            import json
            providers_data = []
            for provider in config.ai_providers:
                providers_data.append({
                    "name": provider.name,
                    "enabled": provider.enabled,
                    "configured": bool(provider.api_key),
                    "model": provider.model,
                    "base_url": provider.base_url
                })
            console.print(json.dumps(providers_data))
        else:
            table = Table(title="🤖 AI Providers Status")
            table.add_column("Provider", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Model", style="yellow")
            table.add_column("URL", style="blue")
            
            for provider in config.ai_providers:
                status = "✅ Enabled" if provider.enabled and provider.api_key else "❌ Disabled"
                table.add_row(
                    provider.name,
                    status,
                    provider.model or "default",
                    provider.base_url or "default"
                )
            console.print(table)
            
    except Exception as e:
        console.print(f"❌ Error: {e}")

@agents_app.command()
def generate_code(
    prompt: str = typer.Argument(..., help="Code generation prompt"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Save to file"),
    language: Optional[str] = typer.Option("python", "--lang", "-l", help="Programming language")
):
    """Generate code using AI agents."""
    try:
        from agents.code_gen import CodeGenerator
        
        generator = CodeGenerator(provider=provider)
        console.print(f"🤖 Generating {language} code...")
        
        code = generator.generate(prompt, language=language)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(code)
            console.print(f"✅ Code saved to: {output_file}")
        else:
            console.print("📝 Generated Code:")
            console.print(f"```{language}")
            console.print(code)
            console.print("```")
            
    except ImportError as e:
        console.print(f"❌ Required modules not available: {e}")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@agents_app.command()
def fix_code(
    file_path: Path = typer.Argument(..., help="Path to code file to fix"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    backup: bool = typer.Option(True, "--backup", help="Create backup before fixing"),
    preview: bool = typer.Option(False, "--preview", help="Preview changes without applying")
):
    """Fix code issues using AI agents."""
    try:
        from agents.code_fix import CodeFixer
        
        if not file_path.exists():
            console.print(f"❌ File not found: {file_path}")
            return
            
        fixer = CodeFixer(provider=provider)
        console.print(f"🔧 Analyzing code in: {file_path}")
        
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        fixed_code = fixer.fix(original_code, str(file_path))
        
        if preview:
            console.print("📋 Original vs Fixed Code Preview:")
            # TODO: Show diff
            console.print(fixed_code)
        else:
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                with open(backup_path, 'w') as f:
                    f.write(original_code)
                console.print(f"💾 Backup saved: {backup_path}")
            
            with open(file_path, 'w') as f:
                f.write(fixed_code)
            console.print("✅ Code fixed successfully")
            
    except ImportError as e:
        console.print(f"❌ Required modules not available: {e}")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@agents_app.command()
def analyze_logs(
    log_file: Optional[Path] = typer.Argument(None, help="Path to log file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    live: bool = typer.Option(False, "--live", help="Analyze live Android logs"),
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity (error, warning, info)")
):
    """Analyze logs using AI agents."""
    try:
        from agents.log_analyzer import LogAnalyzer
        from android.logcat import LogcatManager
        
        analyzer = LogAnalyzer(provider=provider)
        
        if live:
            console.print("🤖 Starting live log analysis...")
            logcat = LogcatManager()
            logs = logcat.capture(duration=60)  # 1 minute capture
        elif log_file and log_file.exists():
            console.print(f"📄 Analyzing log file: {log_file}")
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            console.print("❌ Please provide --live or valid log file path")
            return
        
        analysis = analyzer.analyze(logs, severity_filter=severity)
        
        console.print("🔍 Log Analysis Results:")
        console.print(analysis)
        
    except ImportError as e:
        console.print(f"❌ Required modules not available: {e}")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@agents_app.command()
def set_provider(
    provider_name: str = typer.Argument(..., help="Provider name (openai, openrouter, gemini)"),
    api_key: str = typer.Argument(..., help="API key for the provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    base_url: Optional[str] = typer.Option(None, "--url", help="Custom base URL")
):
    """Configure AI provider settings."""
    try:
        from cli.config import load_config, save_config
        
        config = load_config()
        
        # Find or create provider
        provider = None
        for p in config.ai_providers:
            if p.name == provider_name:
                provider = p
                break
        
        if not provider:
            console.print(f"❌ Provider '{provider_name}' not found in configuration")
            return
        
        # Update provider settings
        provider.api_key = api_key
        provider.enabled = True
        if model:
            provider.model = model
        if base_url:
            provider.base_url = base_url
        
        save_config(config)
        console.print(f"✅ Provider '{provider_name}' configured successfully")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@agents_app.command()
def test_provider(
    provider_name: str = typer.Argument(..., help="Provider name to test"),
    prompt: str = typer.Option("Hello, world!", "--prompt", help="Test prompt")
):
    """Test AI provider connection and functionality."""
    try:
        from agents.base import get_agent_client
        
        console.print(f"🧪 Testing provider: {provider_name}")
        
        client = get_agent_client(provider_name)
        response = client.complete(prompt)
        
        console.print("✅ Provider test successful!")
        console.print(f"Response: {response}")
        
    except ImportError as e:
        console.print(f"❌ Required modules not available: {e}")
    except Exception as e:
        console.print(f"❌ Provider test failed: {e}")

@agents_app.command()
def agent_stats(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Show AI agent usage statistics."""
    try:
        from agents.base import get_usage_stats
        
        stats = get_usage_stats()
        
        if json_output:
            import json
            console.print(json.dumps(stats))
        else:
            table = Table(title="🤖 Agent Usage Statistics")
            table.add_column("Agent", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Requests", style="yellow")
            table.add_column("Tokens", style="blue")
            
            for agent_name, agent_stats in stats.items():
                table.add_row(
                    agent_name,
                    agent_stats.get("provider", "unknown"),
                    str(agent_stats.get("requests", 0)),
                    str(agent_stats.get("tokens", 0))
                )
            console.print(table)
            
    except Exception as e:
        console.print(f"❌ Error: {e}")