# Contributing to CloudTrace

Thank you for your interest in contributing to CloudTrace! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

There are many ways to contribute to CloudTrace:

1. **Reporting Bugs**: Create an issue with detailed steps to reproduce the bug
2. **Suggesting Enhancements**: Open an issue with a clear description of your proposed feature
3. **Improving Documentation**: Help make our docs more comprehensive and clear
4. **Code Contributions**: Submit a pull request with new features or bug fixes

## Development Environment Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/cloudtrace.git
   cd cloudtrace
   ```

3. Run the setup script to create a development environment:
   ```bash
   ./setup.sh
   ```

4. Install the git hooks:
   ```bash
   ./install_hooks.sh
   ```

## Pull Request Process

1. Update your fork to the latest code from the main repository
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes and commit them with clear messages:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

4. Push to your fork and submit a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Respond to any feedback on your pull request

## Code Style

CloudTrace follows the PEP 8 style guide with a few modifications:
- Line length of 100 characters
- Using Black for code formatting

The pre-commit hook will help ensure your code meets these standards.

## Running Tests

Run tests using pytest:
```bash
python -m pytest
```

For test coverage:
```bash
python -m pytest --cov=src tests/
```

## Permission Requirements

When developing features that use traceroute functionality, keep in mind that the application requires elevated privileges (admin/root access) to work correctly.

## Documentation

Please document all new features and update existing documentation as needed.

## License

By contributing to CloudTrace, you agree that your contributions will be licensed under the project's MIT license. 