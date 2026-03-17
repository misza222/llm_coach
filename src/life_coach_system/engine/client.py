"""
LLM Client - wrapper for OpenAI API with Instructor (structured output).

This module provides the only place for LLM calls in the entire system.
"""

from functools import lru_cache
from typing import Any

import instructor
from openai import OpenAI

from life_coach_system.config import settings
from life_coach_system.exceptions import LLMError


@lru_cache
def get_llm_client() -> instructor.Instructor:
    """
    Singleton LLM client with Instructor patch.

    Instructor enables structured output (Pydantic models).
    Documentation: https://python.useinstructor.com/

    Returns:
        instructor.Instructor: Patched OpenAI client
    """
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    return instructor.patch(client, mode=instructor.Mode.MD_JSON)


def call_llm(
    messages: list[dict],
    response_model: Any = None,
    **kwargs: Any,
) -> Any:
    """
    Calls LLM API.

    Args:
        messages: List of messages in format [{role: "system"|"user"|"assistant", content: "..."}]
        response_model: (Optional) Pydantic model for structured output
        **kwargs: Additional parameters (temperature, max_tokens, etc.)

    Returns:
        - If response_model provided: Pydantic model instance
        - If response_model=None: String (plain text)

    Raises:
        LLMError: When the API call fails.

    Example usage without structured output:
    ```python
    messages = [
        {"role": "system", "content": "You are a coach."},
        {"role": "user", "content": "Hello!"}
    ]
    response = call_llm(messages)  # String
    ```

    Example usage with structured output:
    ```python
    class CoachResponse(BaseModel):
        emotion: str
        response: str

    messages = [...]
    response = call_llm(messages, response_model=CoachResponse)
    print(response.emotion)   # "joy"
    print(response.response)  # "Nice to meet you!"
    ```
    """
    client = get_llm_client()

    # Default parameters (can be overridden by **kwargs)
    default_params: dict[str, Any] = {
        "model": settings.model_name,
        "messages": messages,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }
    default_params.update(kwargs)

    try:
        if response_model:
            # Structured output (Pydantic model)
            default_params["response_model"] = response_model
            return client.chat.completions.create(**default_params)
        else:
            # Plain text (no structured output)
            response = client.chat.completions.create(**default_params)
            return response.choices[0].message.content
    except Exception as e:
        raise LLMError(f"LLM API call failed: {e}") from e
