# Contributing to CADX (Codex-Android-AI-Agent)

🎉 Thank you for your interest in contributing to CADX! This document provides guidelines and instructions for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Android SDK (optional, for Android-specific features)
- API keys for AI providers (for testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/codex-android-ai-agent.git
   cd codex-android-ai-agent
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Verify Setup**
   ```bash
   cadx --version
   pytest tests/
   ```

## 🏗️ Development Workflow

### Branch Strategy

- `main` - Stable release branch
- `develop` - Development branch
- `feature/feature-name` - Feature branches
- `fix/bug-description` - Bug fix branches

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow the coding standards (see below)
   - Add/update tests
   - Update documentation

3. **Test Your Changes**
   ```bash
   pytest tests/
   black --check .
   ruff check .
   mypy cli/ android/ agents/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Coding Standards

### Python Style Guide

- **PEP 8**: Follow Python Enhancement Proposal 8
- **Black**: Use Black formatter for consistent code style
- **Type Hints**: Add type hints to all functions and methods
- **Docstrings**: Use Google-style docstrings

Example:
```python
def process_android_log(
    log_content: str, 
    severity_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Process Android log content with optional filtering.
    
    Args:
        log_content: Raw log content to process
        severity_filter: Filter by log severity level
        
    Returns:
        Dictionary containing processed log information
        
    Raises:
        ValueError: If log content is invalid
    """
    # Implementation here
    pass
```

### CLI Development

- Use **Typer** for command-line interfaces
- Add helpful descriptions to all commands and options
- Implement proper error handling with meaningful messages
- Support both human-readable and JSON output formats

Example:
```python
@app.command()
def analyze_logs(
    log_file: Path = typer.Argument(..., help="Path to log file"),
    provider: Optional[str] = typer.Option(None, "--provider", help="AI provider"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Analyze Android logs using AI."""
    try:
        # Implementation
        if json_output:
            console.print(json.dumps(result))
        else:
            console.print("✅ Analysis complete")
    except Exception as e:
        console.print(f"❌ Error: {e}")
        raise typer.Exit(1)
```

### AI Agent Development

- Inherit from `BaseAgent` class
- Implement proper caching
- Add comprehensive error handling
- Use appropriate temperature values
- Clean AI responses

Example:
```python
class MyAgent(BaseAgent):
    """Custom AI agent for specific tasks."""
    
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request."""
        # Check cache first
        cached = self._check_cache(request)
        if cached:
            return cached
        
        try:
            client = self._get_client()
            result = client.complete(request.prompt, ...)
            
            response = AgentResponse(
                content=result,
                success=True,
                # ... other fields
            )
            
            self._cache_response(request, response)
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                # ... other fields
            )
```

### Testing Standards

- **Pytest**: Use pytest for all tests
- **Coverage**: Aim for >80% code coverage
- **Mocking**: Mock external dependencies
- **Test Structure**: Use Arrange-Act-Assert pattern

Example:
```python
import pytest
from unittest.mock import Mock, patch

def test_android_device_listing():
    """Test ADB device listing functionality."""
    # Arrange
    mock_adb_output = "emulator-5554\tdevice\nphone-123\tdevice"
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_adb_output
        
        # Act
        from android.adb import ADBManager
        adb = ADBManager()
        devices = adb.list_devices()
        
        # Assert
        assert len(devices) == 2
        assert devices[0].id == "emulator-5554"
        assert devices[0].status == "device"
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=cadx --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m android
```

### Test Categories

Use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.android` - Android-specific tests
- `@pytest.mark.ai` - AI provider tests

### Writing New Tests

1. **Test File Naming**: `test_<module_name>.py`
2. **Test Function Naming**: `test_<functionality>`
3. **Fixtures**: Use fixtures for common test data
4. **Parameterization**: Use `@pytest.mark.parametrize` for multiple test cases

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and methods
- Use type hints consistently
- Include usage examples in docstrings
- Document complex algorithms and business logic

### User Documentation

- Update README.md for new features
- Add examples to `examples/` directory
- Update CLI help text
- Create task packs for common workflows

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Python version
   - Operating system
   - CADX version
   - Android SDK version (if applicable)

2. **Steps to Reproduce**
   - Clear, step-by-step instructions
   - Sample code or commands
   - Expected vs actual behavior

3. **Additional Context**
   - Error messages and stack traces
   - Log files
   - Screenshots (if applicable)

### Bug Report Template

```markdown
## Bug Report

**Environment:**
- CADX Version: 0.1.0
- Python Version: 3.11
- OS: Ubuntu 22.04
- Android SDK: 34

**Description:**
Brief description of the bug.

**Steps to Reproduce:**
1. Run `cadx command`
2. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```
Paste error messages here
```

**Additional Context:**
Any other relevant information
```

## 🌟 Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Describe the use case clearly
3. Explain how it fits with CADX's goals
4. Provide mockups or examples if applicable

### Feature Request Template

```markdown
## Feature Request

**Use Case:**
Describe the problem this feature would solve.

**Proposed Solution:**
Describe your proposed solution.

**Alternative Solutions:**
Describe alternatives you've considered.

**Additional Context:**
Any other relevant information.
```

## 🔧 Adding New Features

### New CLI Commands

1. Add command in `cli/commands/`
2. Register in `cli/main.py`
3. Add tests in `tests/`
4. Update documentation

### New AI Agents

1. Create agent class in `agents/`
2. Inherit from `BaseAgent`
3. Add to command interfaces
4. Write comprehensive tests
5. Document usage patterns

### New AI Providers

1. Create provider in `agents/providers/`
2. Implement `AIClient` interface
3. Add to configuration system
4. Update provider selection logic
5. Add provider-specific tests

### New Android Features

1. Add functionality to `android/` module
2. Implement proper error handling
3. Add device compatibility checks
4. Create CLI command interface
5. Write integration tests

## 🎯 Project Goals

When contributing, keep these goals in mind:

1. **Simplicity**: Make Android development easier
2. **Reliability**: Robust error handling and testing
3. **Performance**: Efficient operations with caching
4. **Security**: Safe handling of credentials and operations
5. **Flexibility**: Support multiple AI providers and workflows
6. **Documentation**: Clear documentation for all features

## 📋 Pull Request Process

1. **Create PR** against `develop` branch
2. **Fill PR Template** with complete information
3. **Ensure CI Passes** - all tests and checks
4. **Request Review** from maintainers
5. **Address Feedback** and iterate as needed
6. **Squash Commits** before merge (if requested)

### PR Template

```markdown
## Pull Request

**Description:**
Brief description of changes.

**Type of Change:**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing:**
- [ ] Added new tests
- [ ] Updated existing tests
- [ ] Manual testing completed

**Documentation:**
- [ ] Updated README
- [ ] Updated docstrings
- [ ] Updated examples

**Checklist:**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
```

## 🏆 Recognition

Contributors will be recognized in:

- README.md contributors section
- CHANGELOG.md for significant contributions
- GitHub releases notes
- Project documentation

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: dev@cadx.ai for private matters

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CADX! Your efforts help make Android development better for everyone. 🚀