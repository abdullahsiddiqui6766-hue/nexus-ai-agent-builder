from typing import Literal

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """User's request for the AI agent system."""

    task: str = Field(
        min_length=3,
        max_length=10_000,
        description="The task the agent system should complete.",
    )

    search_enabled: bool = False


class PlanStep(BaseModel):
    """One step in the execution plan."""

    agent: Literal["researcher", "content"]
    instruction: str = Field(min_length=1, max_length=2_000)


class ExecutionPlan(BaseModel):
    """Structured plan created by the planner."""

    steps: list[PlanStep] = Field(min_length=1, max_length=10)
    expected_output: str = Field(min_length=1, max_length=500)


class AgentResult(BaseModel):
    """Result returned by an individual agent."""

    agent_name: str = Field(min_length=1, max_length=100)
    content: str = Field(max_length=20_000)
    success: bool = True
    error: str | None = None


class ReviewResult(BaseModel):
    """Reviewer's assessment of generated content."""

    approved: bool
    feedback: str = Field(default="", max_length=3_000)
    revised_content: str | None = Field(default=None, max_length=20_000)


class WorkflowResult(BaseModel):
    """Final result returned by the orchestrator."""

    task: str
    status: Literal["success", "partial", "failed"]
    final_output: str = ""
    agent_results: list[AgentResult] = Field(default_factory=list)
    error: str | None = None