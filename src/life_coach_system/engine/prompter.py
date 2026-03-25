"""
System Prompter — Jinja2-based dynamic system prompt builder.
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from life_coach_system.config import settings


class SystemPrompter:
    """Builds Jinja2-rendered system prompts from session state."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(
                [
                    str(settings.templates_dir),
                ]
            )
        )

    def build_system_prompt(
        self,
        core: dict[str, Any],
        profile: dict[str, Any],
        session: dict[str, Any],
        history: list[dict],
        *,
        cross_session: dict[str, Any] | None = None,
    ) -> str:
        """
        Render the main system prompt template with session context.

        Args:
            core: Core coach settings (e.g. coach_name).
            profile: User profile data (user_name, main_goal).
            session: Session state (phase, turn_count, detected_emotions).
            history: Recent conversation history.
            cross_session: Cross-session context (user_profile, past_sessions).

        Returns:
            Rendered system prompt string.
        """
        template = self.env.get_template("main.j2")

        return template.render(
            core=core,
            profile=profile,
            session=session,
            history=history,
            cross_session=cross_session or {},
        )
