# Contributing to maily

Thank you for your interest in contributing to **maily**! We welcome bug reports, feature suggestions, documentation improvements, and code contributions.

---

## 🛠️ Development Setup

The project uses [uv](https://docs.astral.sh/uv/) for fast, deterministic Python dependency management.

### Prerequisites

- Python 3.13+ (server requires `>=3.13`, client supports `>=3.10`)
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (optional, for containerized testing)

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/stormsia/maily.git && cd maily

# 2. Install dependencies into virtual environment
uv sync

# 3. Install pre-commit hooks (runs formatting and commit message linting)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

---

## 🧪 Testing & Quality Gates

Run the test suite and quality checks locally before submitting a PR:

```bash
# Run all unit and integration tests
uv run pytest

# Check code formatting and linting
uv run ruff check src tests client scripts
uv run ruff format --check src tests client scripts

# Run static type checking
uv run mypy src client scripts

# Verify standalone client mirror integrity
uv run python scripts/build_client.py --check

# Verify version consistency across the codebase
uv run python scripts/check_version_consistency.py
```

---

## 📝 Conventional Commits

We enforce the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commits and PR titles:

Format: `<type>[(<scope>)][!]: <description>`

### Allowed Types

- `feat`: A new feature (triggers minor SemVer bump)
- `fix`: A bug fix (triggers patch SemVer bump)
- `perf`: A code change that improves performance
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (whitespace, formatting)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `deps`: Dependency updates

### Examples

- `feat(api): add webhook notification on new message`
- `fix(client): handle 429 Retry-After header gracefully`
- `docs: update self-hosting docker guide`
- `feat(auth)!: require API key for all routes` (breaking change)

---

## 🚀 Pull Request Guidelines

1. **Branch from `main`**: Create a descriptive feature branch (e.g., `feat/webhook-retry`, `fix/tempmail-cors`).
2. **Atomic Commits**: Keep commits focused and logically grouped.
3. **Linear History**: Rebase against `main` before submitting; avoid merge commits in PR branches.
4. **Pass CI**: Ensure all GitHub Actions checks pass.
5. **Update Docs**: If adding or altering functionality, update relevant documentation.
