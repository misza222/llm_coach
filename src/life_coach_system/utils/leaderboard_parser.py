"""
Leaderboard Card Parser - extracts evaluation criteria from markdown.

Based on lesson 5.3 methodology.
"""

import re

from pydantic import BaseModel, Field


class CheckDefinition(BaseModel):
    """
    Definition of a single evaluation criterion.

    Extracted from leaderboard markdown file.
    """

    id: str = Field(..., description="Unique ID (LC-001, LC-002, etc.)")
    title: str = Field(..., description="Short title of criterion")
    description: str = Field(..., description="Full criterion text")
    priority: str = Field(..., description="MUST-HAVE or SHOULD-HAVE")
    examples_positive: list[str] = Field(default_factory=list)
    examples_negative: list[str] = Field(default_factory=list)

    def to_prompt_fragment(self) -> str:
        """Format check as prompt fragment for LLM."""
        return f"**{self.id} - {self.title}** ({self.priority})\nCriterion: {self.description}\n"


def parse_leaderboard_card(filepath: str) -> list[CheckDefinition]:
    """
    Parse leaderboard markdown file to extract criteria.

    Format expected:
    #### LC-001 🔴 MUST-HAVE | Title
    - **Criterion**: Description
    - **Positive examples**: ...
    - **Negative examples**: ...

    Args:
        filepath: Path to leaderboard_card_coach.md

    Returns:
        List of CheckDefinition objects
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    checks = []

    # Split by #### headers (each criterion section)
    sections = re.split(r"\n#### ", content)

    for section in sections[1:]:  # Skip preamble
        if not section.strip():
            continue

        lines = section.split("\n")
        header = lines[0]

        # Extract ID (LC-001, LC-002, etc.)
        id_match = re.search(r"(LC-\d{3})", header)
        if not id_match:
            continue
        check_id = id_match.group(1)

        # Extract priority
        if "🔴 MUST-HAVE" in header or "MUST-HAVE" in header:
            priority = "MUST-HAVE"
        elif "🟡 SHOULD-HAVE" in header or "SHOULD-HAVE" in header:
            priority = "SHOULD-HAVE"
        else:
            continue

        # Extract title (after | symbol)
        title_match = re.search(r"\|\s*(.+)$", header)
        title = title_match.group(1).strip() if title_match else ""

        # Extract description (after "- **Criterion**:")
        description = ""
        for line in lines:
            if "**Criterion**:" in line or "**Criterion:**" in line:
                description = line.split("**Criterion**")[-1].strip().lstrip(":").strip()
                break

        # Extract examples (simplified - can be enhanced)
        examples_positive = []
        examples_negative = []

        in_positive = False
        in_negative = False

        for line in lines:
            if "**Positive examples**" in line or "**Positive examples**:" in line:
                in_positive = True
                in_negative = False
            elif "**Negative examples**" in line or "**Negative examples**:" in line:
                in_positive = False
                in_negative = True
            elif line.strip().startswith("1.") or line.strip().startswith("2."):
                example = line.strip()[2:].strip().strip('"')
                if in_positive:
                    examples_positive.append(example)
                elif in_negative:
                    examples_negative.append(example)

        checks.append(
            CheckDefinition(
                id=check_id,
                title=title,
                description=description,
                priority=priority,
                examples_positive=examples_positive,
                examples_negative=examples_negative,
            )
        )

    return checks


def filter_checks_by_priority(
    checks: list[CheckDefinition], priority: str
) -> list[CheckDefinition]:
    """
    Filter checks by priority.

    Args:
        checks: All parsed checks
        priority: "MUST-HAVE", "SHOULD-HAVE", or "ALL"

    Returns:
        Filtered list of checks
    """
    if priority == "ALL":
        return checks

    return [c for c in checks if c.priority == priority]
