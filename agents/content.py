from agents.base import BaseAgent


class ContentAgent(BaseAgent):
    """Creates structured content using supplied research notes."""

    def run(self, task: str) -> str:
        if not task or not task.strip():
            raise ValueError("Content task cannot be empty.")

        prompt = f"""
You are a professional content creation assistant.

USER TASK:
{task.strip()}

INSTRUCTIONS:

1. Follow the user's requested format, tone, and level of detail.
2. Organize the output with clear headings where appropriate.
3. Use simple, understandable language.
4. Avoid unnecessary repetition.
5. Do not invent facts, statistics, dates, quotations, or citations.
6. When research notes are supplied, use them as the primary
   evidence for factual claims.
7. Preserve relevant source titles and URLs from the research notes.
8. Place source URLs near the claims they support when the supplied
   information establishes a reasonable connection.
9. Never invent URLs or claim that a source verifies something
   when the research notes do not support that conclusion.
10. If information is missing or uncertain, clearly state the limitation.
11. Do not claim to have independently opened or verified webpages.
12. Distinguish current information from historical information
    when the supplied research notes allow this distinction.
13. Include a Sources section when relevant sources are provided.
14. If the task is creative and does not require research, do not
    add unnecessary citations or a Sources section.
15. Return the requested content without describing your internal process.

Produce the final content using only the evidence and context available
in the task and supplied research notes.
"""

        content = self.generate(prompt)

        if not content or not content.strip():
            raise RuntimeError(
                "Content Agent returned empty content."
            )

        return content.strip()