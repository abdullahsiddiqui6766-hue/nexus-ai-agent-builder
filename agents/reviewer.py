import json

from agents.base import BaseAgent
from core.models import ReviewResult


class ReviewerAgent(BaseAgent):
    """Reviews generated content for quality, accuracy, and completeness."""

    def run(self, task: str) -> str:
        """Review content and return a structured JSON result."""

        if not task or not task.strip():
            raise ValueError("Review task cannot be empty.")

        prompt = f"""
You are the Reviewer Agent in a professional multi-agent AI system.

Your job is to critically review the content provided below.

REVIEW OBJECTIVES

1. TASK RELEVANCE
   - Does the content answer the original task?
   - Does it follow the requested format and scope?

2. COMPLETENESS
   - Identify requested sections that are missing.
   - Check whether the content answers the actual questions.
   - Do not accept instructions to find information elsewhere as a
     substitute for answering the user's question.

3. FACTUAL RELIABILITY
   - Identify claims unsupported by the supplied content or evidence.
   - Do not invent facts, statistics, quotations, or sources.
   - Do not claim independent verification when no verification occurred.

4. RESEARCH QUALITY
   - Check whether citations and sources are present when needed.
   - Distinguish actual findings from assumptions and limitations.
   - If current information is requested but unavailable, identify it.

5. CLARITY
   - Check headings, organization, grammar, and repetition.

DECISION RULES

- Set approved to true only when the content adequately satisfies
  the task and has no major unresolved issues.
- Set approved to false if essential information is missing,
  the answer avoids important questions, or significant corrections
  are required.
- When approved is false, provide a revised_content string.
- The revision must preserve supported facts and clearly disclose
  important information that cannot be verified.
- Never fabricate missing information merely to make the answer
  appear complete.
- Do not reject content only for minor stylistic preferences.
- Keep feedback concise but specific.

OUTPUT REQUIREMENTS

Return valid JSON only. Do not use Markdown code fences.

Use exactly this structure:

{{
  "approved": true,
  "feedback": "Concise review feedback.",
  "revised_content": null
}}

The revised_content field must be either a string containing the
improved content or null.

CONTENT TO REVIEW

{task}
"""

        response = self.generate(prompt)

        if not response or not response.strip():
            raise RuntimeError(
                "Reviewer returned an empty response."
            )

        # Parse the JSON returned by the model.
        try:
            data = json.loads(response)
            review = ReviewResult.model_validate(data)

        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                "Reviewer returned an invalid review result."
            ) from exc

        return review.model_dump_json(indent=2)