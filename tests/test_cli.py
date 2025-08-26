"""Tests for CLI functionality."""

import pytest
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Codex-Android-AI-Agent" in result.stdout

def test_status_command():
    """Test status command."""
    result = runner.invoke(app, ["status"])
    # Status command might fail if dependencies aren't available
    # but should not crash
    assert result.exit_code in [0, 1]

def test_config_show():
    """Test config show command."""
    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "Configuration" in result.stdout or "configuration" in result.stdout

def test_android_devices():
    """Test android devices command (may fail if no ADB)."""
    result = runner.invoke(app, ["android", "devices"])
    # Command should not crash even if no devices/ADB
    assert result.exit_code in [0, 1]

def test_agents_list_providers():
    """Test agents list-providers command."""
    result = runner.invoke(app, ["agents", "list-providers"])
    assert result.exit_code == 0
    # Should show configured providers
    assert "Provider" in result.stdout or "openai" in result.stdout

@pytest.mark.parametrize("command", [
    ["--help"],
    ["android", "--help"],
    ["agents", "--help"], 
    ["codex", "--help"],
    ["ci", "--help"]
])
def test_help_commands(command):
    """Test help commands for all subcommands."""
    result = runner.invoke(app, command)
    assert result.exit_code == 0
    assert "help" in result.stdout.lower() or "usage" in result.stdout.lower()

def test_invalid_command():
    """Test invalid command handling."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0