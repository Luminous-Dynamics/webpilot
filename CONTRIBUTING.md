# Contributing to WebPilot

First off, thank you for considering contributing to WebPilot! It's people like you that make WebPilot such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by the [WebPilot Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to webpilot@example.com.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem.
* **Include Python version, OS information, and browser versions** where applicable.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful** to most WebPilot users.

### Pull Requests

Please follow these steps to have your contribution considered by the maintainers:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the code style of this project.
6. Issue that pull request!

## Development Process

### Setting Up Your Development Environment

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/webpilot.git
   cd webpilot
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Code Style Guidelines

We use several tools to maintain code quality:

#### Black (Code Formatting)
```bash
black src/ tests/
```

#### isort (Import Sorting)
```bash
isort src/ tests/
```

#### Flake8 (Linting)
```bash
flake8 src/ tests/
```

#### MyPy (Type Checking)
```bash
mypy src/
```

### Writing Tests

We aim for high test coverage. When adding new features:

1. **Write unit tests** for individual functions/methods
2. **Write integration tests** for feature interactions
3. **Write end-to-end tests** for complete workflows

Example test structure:
```python
import pytest
from webpilot import WebPilot

class TestWebPilot:
    def test_navigation(self):
        """Test basic navigation functionality."""
        with WebPilot() as pilot:
            result = pilot.start("https://example.com")
            assert result.success
            assert "Example Domain" in pilot.driver.title
    
    @pytest.mark.parametrize("browser", ["chrome", "firefox"])
    def test_multiple_browsers(self, browser):
        """Test functionality across different browsers."""
        # Test implementation
        pass
```

### Documentation

All public APIs must be documented with Google-style docstrings:

```python
def click(self, selector: str = None, text: str = None, timeout: float = 10) -> ActionResult:
    """
    Click on an element identified by selector or text.
    
    Args:
        selector: CSS selector or XPath of the element.
        text: Text content of the element to click.
        timeout: Maximum time to wait for element (seconds).
        
    Returns:
        ActionResult containing success status and metadata.
        
    Raises:
        TimeoutException: If element not found within timeout.
        WebPilotException: If neither selector nor text provided.
        
    Examples:
        >>> pilot.click(selector="#submit-button")
        >>> pilot.click(text="Submit")
    """
```

### Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

* **feat**: New feature
* **fix**: Bug fix
* **docs**: Documentation changes
* **style**: Code style changes (formatting, etc.)
* **refactor**: Code refactoring
* **test**: Test additions or changes
* **chore**: Build process or auxiliary tool changes

Examples:
```
feat: add ML-based test generation
fix: resolve timeout issue in cloud browser
docs: update installation guide for Windows
test: add unit tests for pattern detection
```

### Pull Request Process

1. **Update the README.md** with details of changes to the interface, if applicable.
2. **Update the CHANGELOG.md** with a note describing your changes.
3. **Increase version numbers** in any examples files and the README.md to the new version that this Pull Request would represent.
4. **Ensure all tests pass** and coverage remains high.
5. **Request review** from at least one maintainer.

### Code Review Process

All submissions require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information on using pull requests.

During code review, we look for:

* **Correctness**: Does the code do what it's supposed to?
* **Complexity**: Can the code be simplified?
* **Tests**: Are there adequate tests?
* **Documentation**: Are the changes documented?
* **Style**: Does the code follow our style guidelines?
* **Performance**: Are there any performance concerns?

## Project Structure

```
webpilot/
├── src/webpilot/          # Source code
│   ├── core/              # Core functionality
│   ├── backends/          # Browser backends
│   ├── ml/                # Machine learning
│   ├── cloud/             # Cloud integrations
│   └── utils/             # Utilities
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                  # Documentation
├── examples/              # Example scripts
└── scripts/               # Development scripts
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=webpilot --cov-report=html

# Run specific test file
pytest tests/unit/test_core.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_navigation"
```

### Writing Good Tests

1. **Test one thing at a time**
2. **Use descriptive test names**
3. **Follow Arrange-Act-Assert pattern**
4. **Use fixtures for common setup**
5. **Mock external dependencies**
6. **Test edge cases and error conditions**

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions will handle the rest

## Community

* Join our [Discord Server](https://discord.gg/webpilot)
* Follow us on [Twitter](https://twitter.com/webpilot)
* Read our [Blog](https://blog.webpilot.dev)

## Recognition

Contributors who make significant contributions will be:
* Added to the AUTHORS file
* Mentioned in release notes
* Given credit in documentation

## Questions?

Feel free to open an issue with the "question" label or reach out to the maintainers directly.

Thank you for contributing to WebPilot! 🚁