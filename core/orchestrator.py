from __future__ import annotations

import logging

from agents.content import ContentAgent
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.reviewer import ReviewerAgent

from core.models import (
    AgentResult,
    ExecutionPlan,
    ReviewResult,
    TaskRequest,
    WorkflowResult,
)

from services.groq_client import GroqClient
from services.storage import WorkflowStorage
from tools.search.base import SearchProvider


logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates AI agents with bounded context and controlled execution."""

    MAX_RESEARCH_STEPS = 2
    MAX_INSTRUCTION_CHARS = 2_000
    MAX_PLAN_CHARS = 6_000
    MAX_RESEARCH_CHARS = 8_000
    MAX_CONTENT_CHARS = 12_000
    MAX_REVIEW_EVIDENCE_CHARS = 4_000

    def __init__(
        self,
        groq_client: GroqClient,
        search_provider: SearchProvider | None = None,
        storage: WorkflowStorage | None = None,
    ) -> None:
        self.storage = storage

        self.planner = PlannerAgent(
            name="Planner",
            groq_client=groq_client,
            system_prompt=(
                "You are a careful planning assistant. "
                "Create a concise, practical execution plan. "
                "Use no more than two focused research steps. "
                "Avoid duplicate research tasks. "
                "Return the execution plan in the required JSON format."
            ),
        )

        self.researcher = ResearcherAgent(
            name="Researcher",
            groq_client=groq_client,
            system_prompt=(
                "You are a factual research assistant. "
                "Research only the assigned topic. "
                "Be concise and avoid repetition. "
                "Use supplied search results when available. "
                "Distinguish supported facts from uncertainty. "
                "Never invent statistics, sources, or citations. "
                "Preserve relevant source titles and URLs."
            ),
            search_provider=search_provider,
        )

        self.content_agent = ContentAgent(
            name="Content",
            groq_client=groq_client,
            system_prompt=(
                "You are a professional content creator. "
                "Answer the original task directly. "
                "Follow the requested structure and use relevant research. "
                "Preserve relevant source URLs from supplied research notes. "
                "Avoid repetition and unnecessary filler. "
                "Never invent statistics, dates, quotations, or sources. "
                "Clearly state important limitations when necessary."
            ),
        )

        self.reviewer = ReviewerAgent(
            name="Reviewer",
            groq_client=groq_client,
            system_prompt=(
                "You are a careful content reviewer. "
                "Check relevance, completeness, clarity, and factual support. "
                "Compare claims with the supplied research evidence. "
                "Preserve relevant source URLs when revising content. "
                "Approve satisfactory content. "
                "Never invent facts or citations. "
                "Return valid JSON in the required schema."
            ),
        )

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        """Limit context size while disclosing that content was shortened."""

        text = (text or "").strip()

        if len(text) <= limit:
            return text

        suffix = (
            "\n\n[Content shortened to fit the workflow context limit.]"
        )

        return text[: max(0, limit - len(suffix))].rstrip() + suffix

    def _save_result(self, result: WorkflowResult) -> None:
        """Save workflow history without hiding the workflow result."""

        if self.storage is None:
            return

        try:
            self.storage.save(result)
        except Exception:
            logger.exception("Could not save workflow history.")

    def run(self, request: TaskRequest) -> WorkflowResult:
        """Run planning, research, content generation, and review."""

        results: list[AgentResult] = []

        try:
            # -------------------------------------------------
            # 1. PLANNING
            # -------------------------------------------------

            logger.info("Starting Planner agent.")

            plan_text = self.planner.run(request.task)

            plan = ExecutionPlan.model_validate_json(plan_text)

            bounded_plan_text = self._truncate(
                plan_text,
                self.MAX_PLAN_CHARS,
            )

            # -------------------------------------------------
            # 2. RESEARCH
            # -------------------------------------------------

            research_notes: list[str] = []

            research_steps = [
                step
                for step in plan.steps
                if step.agent.strip().lower() == "researcher"
            ]

            if len(research_steps) > self.MAX_RESEARCH_STEPS:
                logger.warning(
                    "Planner produced %s research steps; limiting to %s.",
                    len(research_steps),
                    self.MAX_RESEARCH_STEPS,
                )

            for step in research_steps[: self.MAX_RESEARCH_STEPS]:
                instruction = self._truncate(
                    step.instruction,
                    self.MAX_INSTRUCTION_CHARS,
                )

                if not instruction:
                    continue

                logger.info("Running Researcher agent.")

                notes = self.researcher.run(
                    instruction,
                    use_search=request.search_enabled,
                )

                if notes and notes.strip():
                    bounded_notes = self._truncate(
                        notes,
                        self.MAX_RESEARCH_CHARS,
                    )

                    research_notes.append(bounded_notes)

                    results.append(
                        AgentResult(
                            agent_name="Researcher",
                            content=bounded_notes,
                        )
                    )

            combined_research = "\n\n".join(research_notes)

            if not combined_research:
                combined_research = (
                    "No research notes were generated. "
                    "Do not claim that external research was completed."
                )

            combined_research = self._truncate(
                combined_research,
                self.MAX_RESEARCH_CHARS,
            )

            # -------------------------------------------------
            # 3. CONTENT GENERATION
            # -------------------------------------------------

            content_task = f"""
ORIGINAL USER TASK:
{self._truncate(request.task, 5_000)}

EXECUTION PLAN:
{bounded_plan_text}

RESEARCH NOTES:
{combined_research}

CONTENT REQUIREMENTS:
- Answer the original task directly.
- Follow the requested format and structure.
- Use relevant research notes as evidence.
- Preserve relevant source titles and URLs.
- Place source URLs near claims they support when appropriate.
- Do not invent facts, dates, statistics, quotations, or citations.
- Do not imply that search snippets constitute full webpage verification.
- Clearly state important limitations.
- Produce a complete and useful final answer.

Generate the final content now.
"""

            logger.info("Running Content agent.")

            content = self.content_agent.run(content_task)

            if not content or not content.strip():
                raise RuntimeError(
                    "Content Agent returned empty content."
                )

            content = self._truncate(
                content,
                self.MAX_CONTENT_CHARS,
            )

            results.append(
                AgentResult(
                    agent_name="Content",
                    content=content,
                )
            )

            # -------------------------------------------------
            # 4. REVIEW
            # -------------------------------------------------

            # The Reviewer now receives research evidence as well
            # as the original task and generated content.

            review_evidence = self._truncate(
                combined_research,
                self.MAX_REVIEW_EVIDENCE_CHARS,
            )

            review_task = f"""
ORIGINAL USER TASK:
{self._truncate(request.task, 3_000)}

RESEARCH EVIDENCE:
{review_evidence}

GENERATED CONTENT:
{self._truncate(content, self.MAX_CONTENT_CHARS)}

REVIEW OBJECTIVES:

1. TASK RELEVANCE
   - Does the content answer the original user task?
   - Does it follow the requested format and scope?

2. COMPLETENESS
   - Are important requested details missing?
   - Does the content answer the actual questions?

3. FACTUAL RELIABILITY
   - Compare factual claims with the supplied research evidence.
   - Identify claims that are not supported by that evidence.
   - Do not invent facts, statistics, quotations, or sources.
   - Do not claim independent verification that did not occur.

4. SOURCE QUALITY
   - Check whether relevant source URLs from the research evidence
     are preserved in the generated content.
   - Identify citations whose URLs do not appear in the supplied
     research evidence.
   - Do not assume a URL supports a claim merely because it exists.
   - Remember that search snippets are not full webpage contents.

5. CLARITY
   - Check organization, grammar, headings, and repetition.

DECISION RULES:
- Approve content that adequately satisfies the task.
- Reject content only when important corrections are necessary.
- If revising, preserve supported facts and relevant source URLs.
- Never fabricate information to fill evidence gaps.
- Clearly disclose important limitations.
- Do not reject content for minor stylistic preferences.
- Keep feedback concise but specific.

Return the required JSON schema:
approved, feedback, revised_content.
"""

            logger.info("Running Reviewer agent.")

            review_text = self.reviewer.run(review_task)

            review = ReviewResult.model_validate_json(review_text)

            final_output = content

            if not review.approved and review.revised_content:
                revised_content = review.revised_content.strip()

                if revised_content:
                    final_output = self._truncate(
                        revised_content,
                        self.MAX_CONTENT_CHARS,
                    )

            # Record the review feedback and preserve the final output
            # as the authoritative workflow result.

            results.append(
                AgentResult(
                    agent_name="Reviewer",
                    content=review.feedback,
                )
            )

            workflow_result = WorkflowResult(
                task=request.task,
                status="success",
                final_output=final_output,
                agent_results=results,
            )

            logger.info("AI workflow completed successfully.")

        except Exception as exc:
            logger.exception("AI workflow failed.")

            workflow_result = WorkflowResult(
                task=request.task,
                status="failed",
                final_output="",
                agent_results=results,
                error=f"{type(exc).__name__}: {exc}",
            )

        self._save_result(workflow_result)

        return workflow_result