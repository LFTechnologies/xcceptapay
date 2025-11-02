# Contributing to XcceptaPay

Thank you for your interest in contributing to XcceptaPay - XRPL Offline Payments! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Node version, Docker version, etc.)
- **Screenshots** if applicable
- **Error logs** from `docker-compose logs`

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear use case** and motivation
- **Detailed description** of the proposed functionality
- **Possible implementation** approach (if you have ideas)
- **Alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding style** used throughout the project
3. **Add tests** if you're adding functionality
4. **Update documentation** if you're changing functionality
5. **Ensure all tests pass** before submitting
6. **Write clear commit messages** following our conventions

#### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add webhook support for settlement notifications

Add POST /webhooks/configure endpoint to allow merchants to
register webhook URLs for real-time settlement notifications.

Closes #123
```

```
fix(firmware): prevent relay timeout on long vending operations

Increase MAX_PULSE_MS from 3000ms to 5000ms to accommodate
slower vending mechanisms.

Fixes #456
```

## Development Setup

### Prerequisites

- Node.js 20+
- Python 3.10+
- Docker & Docker Compose
- Git

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/xrpl-offline-payments.git
   cd xrpl-offline-payments
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose up -d
   ```

4. **Run in development mode**

   **API:**
   ```bash
   cd api
   npm install
   npm run dev
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   **Kivy App:**
   ```bash
   cd app
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

### Testing

```bash
# API tests
cd api
npm test

# Frontend tests
cd frontend
npm test

# Python tests
cd app
pytest
```

### Code Style

#### JavaScript/TypeScript
- Use ESLint configuration provided
- Format with Prettier
- Run `npm run lint` before committing

#### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Run `black` for formatting
- Run `flake8` for linting

#### Arduino/C++
- Follow Arduino style guide
- Use meaningful variable names
- Comment complex logic

### Project Structure

```
xrpl-offline-payments/
├── api/              # Node.js backend
├── frontend/         # React dashboard
├── app/              # Kivy mobile wallet
├── firmware/         # ESP32 firmware
├── tools/            # CLI tools
├── scripts/          # Deployment scripts
├── docs/             # Documentation
└── tests/            # Integration tests
```

## Areas for Contribution

### High Priority

- 🔐 Security enhancements and audits
- 📱 Mobile app improvements (iOS/Android native)
- 📊 Analytics and reporting features
- 🌐 Internationalization (i18n)
- 🧪 Test coverage improvements

### Medium Priority

- 🎨 UI/UX improvements
- 📖 Documentation improvements
- 🐛 Bug fixes
- ⚡ Performance optimizations

### Good First Issues

Issues labeled `good-first-issue` are great for newcomers:

- Documentation typos/improvements
- Adding tests for existing features
- UI polish and refinements
- Example implementations
- Tool improvements

## Review Process

1. **Automated checks** must pass (linting, tests, build)
2. **Code review** by at least one maintainer
3. **Documentation** must be updated for user-facing changes
4. **Changelog** entry for significant changes

## Release Process

Releases follow semantic versioning (SemVer):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes, backward compatible

## Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Discord**: Real-time chat and support
- **Email**: support@xacceptapay.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project website (coming soon)

## Questions?

Don't hesitate to ask! Open an issue with the `question` label or reach out on Discord.

---

**Thank you for contributing to XcceptaPay! 🎉**
