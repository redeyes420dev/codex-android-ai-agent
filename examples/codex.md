# Codex Instructions for CADX (Codex-Android-AI-Agent)

## Project Overview
CADX is an open-source tool that automates Android development tasks using Codex CLI, multi-agent AI pipelines, and integrations with multiple AI providers (OpenAI, OpenRouter, Gemini).

## Project Structure
```
codex-android-ai-agent/
├── cli/                    # CLI commands and configuration
├── android/               # Android automation (ADB, fastboot, logcat)
├── agents/                # AI agents for code gen, fixing, analysis
│   ├── providers/         # Multi-provider support
│   ├── code_gen.py       # Code generation agent
│   ├── code_fix.py       # Code fixing agent
│   └── log_analyzer.py   # Log analysis agent
├── examples/             # Usage examples and task packs
├── tests/               # Test suite
└── docs/               # Documentation
```

## Code Style Guidelines

### Python Code
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Add comprehensive docstrings with Args/Returns sections
- Use f-strings for string formatting
- Prefer pathlib.Path over os.path
- Use dataclasses for structured data
- Handle exceptions properly with specific exception types

### CLI Development (Typer)
- Use typer.Typer() for command groups
- Add clear help text for all commands and options
- Use rich.Console for formatted output
- Implement --json flags for CI/CD integration
- Add proper error handling and exit codes
- Use typer.Option() with clear help text

### Android Integration
- Always check if ADB/fastboot tools are available before use
- Implement proper device ID handling for multiple devices
- Add timeout parameters for long-running operations
- Use subprocess with proper error handling
- Parse ADB output carefully with regex patterns
- Include device status checks before operations

### AI Agent Development
- Inherit from BaseAgent class
- Implement proper caching for repeated requests
- Add usage statistics tracking
- Use appropriate temperature values (0.1-0.2 for code, 0.3-0.7 for analysis)
- Build comprehensive prompts with context
- Clean AI responses to remove artifacts

## Key Features to Understand

### Multi-Provider AI Support
- OpenAI (GPT-4, GPT-3.5)
- OpenRouter (Claude, Llama, etc.)
- Google Gemini
- Configurable via ~/.cadx/config.yaml
- Automatic failover between providers

### Android Automation
- ADB wrapper for device management
- Fastboot operations for flashing/recovery
- Logcat analysis with crash detection
- Device capability detection
- Automated app installation and testing

### Code Generation & Fixing
- Context-aware code generation
- Language-specific fixing (Python, Kotlin, Java)
- Android-specific optimizations
- Performance and security improvements
- Modernization of legacy code

## Common Development Patterns

### Creating New CLI Commands
```python
@app.command()
def new_command(
    required_param: str = typer.Argument(..., help="Description"),
    optional_flag: bool = typer.Option(False, "--flag", help="Description"),
    json_output: bool = typer.Option(False, "--json", help="JSON output")
):
    """Command description."""
    try:
        # Implementation
        if json_output:
            console.print(json.dumps(result))
        else:
            console.print("✅ Success message")
    except Exception as e:
        console.print(f"❌ Error: {e}")
        sys.exit(1)
```

### Adding New AI Agents
```python
class NewAgent(BaseAgent):
    def process(self, request: AgentRequest) -> AgentResponse:
        # Check cache first
        cached = self._check_cache(request)
        if cached:
            return cached
        
        # Process with AI
        client = self._get_client()
        result = client.complete(request.prompt, ...)
        
        # Build response
        response = AgentResponse(...)
        self._cache_response(request, response)
        return response
```

### Android Operations
```python
def android_operation():
    try:
        adb = ADBManager()
        devices = adb.list_devices()
        
        if not devices:
            raise RuntimeError("No devices found")
        
        result = adb.shell_command("command", device_id)
        if not result.success:
            raise RuntimeError(f"Command failed: {result.error}")
        
        return result.output
    except Exception as e:
        # Handle specific error types
        raise
```

## Testing Guidelines

### Unit Tests
- Use pytest for all tests
- Mock external dependencies (ADB, AI providers)
- Test both success and failure paths
- Use fixtures for common test data
- Aim for >80% code coverage

### Integration Tests  
- Test full command workflows
- Use temporary directories for file operations
- Mock AI provider responses
- Test error handling and edge cases

### CI/CD Integration
- All tests must pass before merge
- Use --quiet --json flags for CI commands
- Set appropriate timeouts for operations
- Include performance benchmarks

## Security Considerations

### API Keys
- Never commit API keys to repository
- Use environment variables or config files
- Implement key validation before use
- Support multiple authentication methods

### Android Operations
- Validate device permissions before operations
- Sanitize shell command inputs
- Check file paths for directory traversal
- Implement operation timeouts

### Code Generation
- Validate generated code before execution
- Sanitize user inputs in prompts
- Avoid generating sensitive information
- Implement rate limiting for AI requests

## Performance Guidelines

### Caching
- Cache AI responses for repeated requests
- Use appropriate cache TTL (5 minutes default)
- Implement cache cleanup for memory management
- Cache expensive Android operations

### Async Operations
- Use asyncio for parallel operations
- Implement proper timeout handling
- Use connection pooling for AI providers
- Batch operations when possible

### Resource Management
- Close file handles and connections
- Implement proper cleanup in exception handlers
- Use context managers for resource management
- Monitor memory usage in long-running operations

## Common Tasks

### Adding New Provider
1. Create provider class in agents/providers/
2. Implement AIClient interface
3. Add provider config to Config class
4. Update get_agent_client() function
5. Add provider tests

### Creating Task Packs
1. Define task workflow in examples/task_packs/
2. Implement task validation and error handling
3. Add progress reporting
4. Include rollback functionality
5. Test with different project types

### Extending Android Support
1. Add new wrapper class in android/
2. Implement proper error handling
3. Add device compatibility checks
4. Include operation logging
5. Test with different Android versions

## Error Handling Patterns

### CLI Commands
- Use try-catch with specific exceptions
- Provide helpful error messages
- Include suggested fixes when possible
- Set appropriate exit codes
- Log errors for debugging

### AI Operations
- Handle API rate limits
- Implement retry logic with exponential backoff
- Graceful degradation for provider failures
- Clear error messages for configuration issues

### Android Operations
- Check device connectivity before operations
- Handle permission denied errors
- Timeout long-running operations
- Provide device-specific error context

## Release and Deployment

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in setup.py and __init__.py
- Tag releases with git tags
- Maintain CHANGELOG.md

### Package Distribution
- Build wheel and source distributions
- Test installation in clean environment
- Validate all dependencies
- Include proper metadata in setup.py

## Documentation Standards

### Code Documentation
- Comprehensive docstrings for all public APIs
- Type hints for all parameters and returns
- Usage examples in docstrings
- Clear parameter descriptions

### User Documentation
- Step-by-step installation guide
- Complete API reference
- Common use cases and examples
- Troubleshooting guide
- FAQ section

When working on this project, always prioritize:
1. **Reliability** - Robust error handling and validation
2. **Usability** - Clear CLI interface and helpful messages
3. **Performance** - Efficient operations with proper caching
4. **Security** - Safe handling of credentials and operations
5. **Compatibility** - Support for different Android versions and devices
6. **Documentation** - Clear documentation for all features

## AI Prompt Engineering Best Practices

### For Code Generation
- Provide clear, specific requirements
- Include language and framework preferences
- Specify architectural patterns to follow
- Request error handling and edge cases
- Ask for production-ready code

### For Code Fixing
- Include the original code with clear issue description
- Specify the target language version
- Request minimal necessary changes
- Ask for explanation of fixes made
- Validate fixes don't break existing functionality

### For Log Analysis
- Provide log context and system information
- Specify the time range and severity levels
- Request prioritized issue identification
- Ask for actionable recommendations
- Include performance and security analysis