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

### Environment Variables Setup

1. **Copy the example file:**

   ```sh
   cp .env.example .env
   ```

2. **Fill in your API keys in `.env`:**

   - **X (Twitter) API**: Get credentials from [X Developer Portal](https://developer.x.com/)
   - **Google API**: Get credentials from [Google Cloud Console](https://console.cloud.google.com/)
   - **Bitvavo API**: Get credentials from [Bitvavo](https://bitvavo.com/)
   - **Redis**: Default is `redis://localhost:6379`

3. **Verify your configuration:**

   ```sh
   python check_env.py
   ```

4. **Important Security Notes:**
   - Never commit the `.env` file to version control
   - The `.env` file is already in `.gitignore`
   - Share `.env.example` with team members (contains placeholder values)
   - Each developer should create their own `.env` file

### Required API Keys

- `X_API_CLIENT_ID`, `X_API_CLIENT_SECRET`, `X_API_KEY`, `X_API_SECRET`
- `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`, `X_BEARER_TOKEN`
- `GOOGLE_API_KEY`, `GOOGLE_GENAI_API_KEY`, `GOOGLE_CSE_ID`
- `BITVAVO_API_KEY`, `BITVAVO_API_SECRET`
- `REDIS_URL` (optional, defaults to localhost)

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
