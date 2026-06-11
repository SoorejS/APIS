# Contributing to APIS

First off, thank you for considering contributing to APIS! It's people like you that make APIS a robust and scalable infrastructure for AI systems. 

## Code of Conduct
By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs
Bugs are tracked as GitHub issues. When you create an issue, please use the provided [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include as many details as possible, such as:
- A quick summary and/or background.
- Steps to reproduce the behavior.
- Expected vs actual behavior.
- OS, database, and environment details.

### Suggesting Enhancements
Enhancement suggestions are tracked as GitHub issues. Please use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and explain:
- Why this feature is necessary or useful.
- How it should work conceptually.
- Any potential alternatives you've considered.

### Pull Requests
1. **Fork the repo** and create your branch from `main`.
2. **Setup your environment:**
   - Backend: Install dependencies via `pip install -r requirements.txt`. Ensure you use Python 3.10+.
   - Frontend: `cd dashboard` and `npm install`.
3. **Write tests:** If you've added code that should be tested, add tests to the `tests/` directory.
4. **Ensure the test suite passes:** Run `pytest` and `npm run lint`.
5. **Format your code:** We use standard formatting tools (e.g., Black for Python, Prettier for TypeScript).
6. **Open the PR:** Describe your changes thoroughly and link any relevant issues.

## Development Setup
Check out the Quickstart section in the [README.md](README.md) for detailed instructions on getting the stack running locally.

## License
By contributing to APIS, you agree that your contributions will be licensed under its MIT License.
