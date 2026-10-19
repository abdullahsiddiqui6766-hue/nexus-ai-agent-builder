import json

from agents.base import BaseAgent
from core.models import ExecutionPlan


class PlannerAgent(BaseAgent):
    """Creates a structured execution plan for a user task."""

    def run(self, task: str) -> str:
        if not task.strip():
            raise ValueError("Task cannot be empty.")

        prompt = f"""
Create a practical plan to complete the user's task.

Rules:
- Return valid JSON only.
- Do not include Markdown code fences.
- Use 1 to 10 steps.
- Each step's agent must be either "researcher" or "content".
- Researcher gathers relevant information.
- Content creates or organizes the requested output.
- Keep instructions specific and concise.

Expected JSON structure:
{{
  "steps": [
    {{
      "agent": "researcher",
      "instruction": "Research the key facts."
    }},
    {{
      "agent": "content",
      "instruction": "Write the final response."
    }}
  ],
  "expected_output": "A clear final answer"
}}

User task:
{task}
"""

        response = self.generate(prompt)

        try:
            data = json.loads(response)
            plan = ExecutionPlan.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                "Planner returned an invalid execution plan."
            ) from exc

        return plan.model_dump_json(indent=2)