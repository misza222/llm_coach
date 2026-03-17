# -*- coding: utf-8 -*-
"""
Life Coach system configuration.

Contains base settings. Additional parameters can be added as needed
(e.g. TEMPERATURE, MAX_TOKENS, COACH_PERSONALITY).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Central system configuration.

    Additional parameters can be added:
    - TEMPERATURE (float): Response randomness (0.0-1.0)
    - MAX_TOKENS (int): Maximum response length
    - COACH_PERSONALITY (str): Coach personality description
    - LANGUAGE (str): Preferred language ("pl" or "en")
    """

    # LLM model
    MODEL_NAME = os.getenv("MODEL_NAME")  # Full model name for the LLM API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # Custom base URL

    # LLM parameters
    TEMPERATURE = 0.0
    MAX_TOKENS = 10_000

    # Validate API key at startup
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found! "
            "Make sure the .env file contains: OPENAI_API_KEY=sk-..."
        )

    # Paths
    BASE_DIR = Path(__file__).parent
    MEMORY_DIR = BASE_DIR / "memory"
    TEMPLATES_DIR = BASE_DIR / "memory" / "templates"

    # Coach defaults
    COACH_NAME = "Jack"
    DEFAULT_USER_ID = "default_user"

    # Persistence
    PERSISTENCE_BACKEND = "in_memory"  # Options: "in_memory", "redis", "postgres"

    # Conversation limits (context window)
    MAX_HISTORY_MESSAGES = 10  # Number of recent messages passed to LLM

    # Debug mode
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
