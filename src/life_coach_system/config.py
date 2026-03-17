"""
Life Coach system configuration.

Uses pydantic-settings to read from environment variables and .env file.
All business logic imports settings from here — never os.environ directly.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central system configuration loaded from environment / .env file.

    All fields map directly to environment variable names (case-insensitive).
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM connection
    openai_api_key: str
    openai_base_url: str
    model_name: str

    # LLM parameters
    temperature: float = 0.0
    max_tokens: int = 10_000

    # Coach defaults
    coach_name: str = "Jack"
    default_user_id: str = "default_user"

    # Persistence — set DATABASE_URL to enable SQL backend
    # SQLite:      sqlite:///sessions.db
    # PostgreSQL:  postgresql://user:pass@host:5432/dbname  # pragma: allowlist secret
    database_url: str | None = None

    # Conversation limits (context window)
    max_history_messages: int = 10

    # Debug mode
    debug: bool = True

    @property
    def base_dir(self) -> Path:
        """Absolute path to the life_coach_system package directory."""
        return Path(__file__).parent

    @property
    def templates_dir(self) -> Path:
        """Absolute path to Jinja2 templates directory."""
        return self.base_dir / "memory" / "templates"


# Module-level singleton — import this everywhere instead of instantiating Settings directly.
settings = Settings()
