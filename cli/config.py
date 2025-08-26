"""Configuration management for CADX."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv

load_dotenv()

class AIProvider(BaseModel):
    """AI provider configuration."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True

class AndroidConfig(BaseModel):
    """Android development configuration."""
    adb_path: Optional[str] = None
    fastboot_path: Optional[str] = None
    default_device: Optional[str] = None
    logcat_buffer_size: int = 1000

class CodexConfig(BaseModel):
    """Codex CLI integration settings."""
    auto_mode: bool = False
    suggest_mode: bool = True
    quiet_mode: bool = False
    codex_path: Optional[str] = None

class CIConfig(BaseModel):
    """CI/CD configuration."""
    quiet_mode: bool = True
    json_output: bool = True
    github_token: Optional[str] = None
    webhook_url: Optional[str] = None

class Config(BaseModel):
    """Main configuration model."""
    
    # AI Providers
    ai_providers: List[AIProvider] = Field(default_factory=lambda: [
        AIProvider(
            name="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4"
        ),
        AIProvider(
            name="openrouter", 
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3.5-sonnet"
        ),
        AIProvider(
            name="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-pro"
        )
    ])
    
    # Component configurations
    android: AndroidConfig = Field(default_factory=AndroidConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig) 
    ci: CIConfig = Field(default_factory=CIConfig)
    
    # General settings
    log_level: str = "INFO"
    output_format: str = "rich"  # rich, json, plain
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cadx" / "cache")
    
class ConfigManager:
    """Configuration manager."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cadx"
        self.config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(exist_ok=True)
        
    def load(self) -> Config:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f)
                return Config.model_validate(data)
        return Config()
    
    def save(self, config: Config) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
            
    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get AI provider by name."""
        config = self.load()
        for provider in config.ai_providers:
            if provider.name == name and provider.enabled:
                return provider
        return None

_config_manager = ConfigManager()

def load_config() -> Config:
    """Load the current configuration."""
    return _config_manager.load()

def save_config(config: Config) -> None:
    """Save configuration."""
    _config_manager.save(config)

def get_ai_provider(name: str) -> Optional[AIProvider]:
    """Get AI provider configuration."""
    return _config_manager.get_provider(name)