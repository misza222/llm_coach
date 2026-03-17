# -*- coding: utf-8 -*-
"""
LLM Client - wrapper for OpenAI API with Instructor (structured output).

This module provides the only place for LLM calls in the entire system.
"""

from functools import lru_cache
from typing import List, Optional, Any
from openai import OpenAI
import instructor
from config import Config


@lru_cache()
def get_llm_client():
    """
    Singleton LLM client with Instructor patch.

    Instructor enables structured output (Pydantic models).
    Documentation: https://python.useinstructor.com/

    Returns:
        instructor.Instructor: Patched OpenAI client

    NOTE: This function is complete - no modification needed.
    """
    client = OpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_BASE_URL
    )
    return instructor.patch(client, mode=instructor.Mode.MD_JSON)


def call_llm(
    messages: List[dict],
    response_model: Optional[Any] = None,
    **kwargs
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
    default_params = {
        "model": Config.MODEL_NAME, ## model as config
        "messages": messages,
        "temperature": Config.TEMPERATURE,
        "max_tokens": Config.MAX_TOKENS,
    }
    default_params.update(kwargs)

    if response_model:
        # Structured output (Pydantic model)
        default_params["response_model"] = response_model
        return client.chat.completions.create(**default_params)
    else:
        # Plain text (no structured output) - level 1
        response = client.chat.completions.create(**default_params)
        return response.choices[0].message.content
