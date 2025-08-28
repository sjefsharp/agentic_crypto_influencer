# Agentic Crypto Influencer

Automate crypto influencer tasks with Python, X (Twitter) API, and Google GenAI.

## Installation

1. Install dependencies:
   ```sh
   poetry install
   ```
2. Create a `.env` file (see example in repo, do not commit!)
3. Start the app:
   ```sh
   poetry run python src/graphflow/graphflow.py
   ```

## Configuration

- Fill in your API keys in `.env`.
- Tokens are now stored in Redis.

## Testing

- Tests are located in the `tests/` directory.
- Run all tests:
  ```sh
  poetry run pytest
  ```

## Code Quality

- Pre-commit hooks: black, ruff, mypy.
- Install hooks:
  ```sh
  pre-commit install
  ```

## Security

- Check dependencies:
  ```sh
  poetry export -f requirements.txt | safety check
  ```

## Cron jobs

- See instructions in README and code for automatic posting.

## Logging

- Logs are written to stdout by default. Adjust logging in the tools for more control.

## Contributing

- Use branches and pull requests.
- Add docstrings and type hints to new code.

---

Questions? Open an issue or contact the maintainer.
