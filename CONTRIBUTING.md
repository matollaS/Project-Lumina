# Contributing to nlcore

Thank you for your interest in contributing to NeuroLumina Core!  We welcome
contributions from the fNIRS and neuroimaging community.

## Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/).
Please read it before participating.

## Development Setup

```bash
git clone https://github.com/neurolumina/nlcore.git
cd nlcore
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest                           # all 33 tests
pytest tests/test_snirf.py       # specific module
pytest --cov=nlcore              # with coverage
```

## Code Style

- **ruff** for linting and formatting: `ruff check . && ruff format .`
- **mypy** for type checking: `mypy nlcore/`

Run before submitting:

```bash
ruff check . && ruff format --check . && mypy nlcore/
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Add tests for any new functionality.  Aim for 100% pass rate.
3. Update docstrings and documentation if the public API changes.
4. Ensure `pytest` passes and `ruff`/`mypy` are clean.
5. Open a PR with a clear title and description.

## Adding New Algorithms

New preprocessing or analysis algorithms are welcome.  When contributing a new
method:

- Place it in the appropriate submodule (`preprocessing/`, `physiology/`, `utils/`).
- Add a citation to the original paper in the docstring.
- Include reference implementations that pass basic smoke tests.
- Mark experimental methods with a `.. warning::` in the docstring.

## Reporting Issues

- **Bugs:** Open a GitHub Issue with a minimal reproducible example and your
  environment (`pip freeze | grep nlcore`).
- **Feature requests:** Open a GitHub Discussion so the community can weigh in.

## Questions?

Open a GitHub Discussion or email `opensource@neurolumina.ai`.
