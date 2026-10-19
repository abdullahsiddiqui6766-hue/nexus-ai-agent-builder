import pytest
from unittest.mock import Mock, patch

from core.models import TaskRequest
from core.orchestrator import Orchestrator
from services.storage import WorkflowStorage


@pytest.fixture
def orchestrator():
    """Create an orchestrator with a mocked Groq client."""
    groq_client = Mock()

    return Orchestrator(
        groq_client=groq_client,
    )


def test_successful_workflow_returns_final_output(orchestrator):
    """A successful workflow should return the generated content."""

    plan_json = """
    {
        "steps": [
            {
                "agent": "researcher",
                "instruction": "Research Python."
            }
        ],
        "expected_output": "A short summary"
    }
    """

    review_json = """
    {
        "approved": true,
        "feedback": "Looks good.",
        "revised_content": null
    }
    """

    with (
        patch.object(
            orchestrator.planner,
            "run",
            return_value=plan_json,
        ),
        patch.object(
            orchestrator.researcher,
            "run",
            return_value="Python research notes.",
        ),
        patch.object(
            orchestrator.content_agent,
            "run",
            return_value="Python is a programming language.",
        ),
        patch.object(
            orchestrator.reviewer,
            "run",
            return_value=review_json,
        ),
    ):
        result = orchestrator.run(
            TaskRequest(task="Write a summary about Python.")
        )

    assert result.status == "success"
    assert result.final_output == "Python is a programming language."


def test_reviewer_revision_becomes_final_output(orchestrator):
    """The reviewer's revised content should become the final output."""

    plan_json = """
    {
        "steps": [
            {
                "agent": "researcher",
                "instruction": "Research software testing."
            }
        ],
        "expected_output": "A short summary"
    }
    """

    review_json = """
    {
        "approved": false,
        "feedback": "Needs improvement.",
        "revised_content": "Improved draft."
    }
    """

    with (
        patch.object(
            orchestrator.planner,
            "run",
            return_value=plan_json,
        ),
        patch.object(
            orchestrator.researcher,
            "run",
            return_value="Software testing notes.",
        ),
        patch.object(
            orchestrator.content_agent,
            "run",
            return_value="Original draft.",
        ),
        patch.object(
            orchestrator.reviewer,
            "run",
            return_value=review_json,
        ),
    ):
        result = orchestrator.run(
            TaskRequest(
                task="Write a summary about software testing."
            )
        )

    assert result.status == "success"
    assert result.final_output == "Improved draft."


def test_successful_workflow_is_saved_to_database(orchestrator):
    """A successful workflow should be passed to storage."""

    storage = Mock(spec=WorkflowStorage)
    orchestrator.storage = storage

    plan_json = """
    {
        "steps": [
            {
                "agent": "researcher",
                "instruction": "Research Python."
            }
        ],
        "expected_output": "A short summary"
    }
    """

    review_json = """
    {
        "approved": true,
        "feedback": "Looks good.",
        "revised_content": null
    }
    """

    with (
        patch.object(
            orchestrator.planner,
            "run",
            return_value=plan_json,
        ),
        patch.object(
            orchestrator.researcher,
            "run",
            return_value="Python research notes.",
        ),
        patch.object(
            orchestrator.content_agent,
            "run",
            return_value="Python summary.",
        ),
        patch.object(
            orchestrator.reviewer,
            "run",
            return_value=review_json,
        ),
    ):
        result = orchestrator.run(
            TaskRequest(task="Write a summary about Python.")
        )

    assert result.status == "success"
    storage.save.assert_called_once_with(result)


def test_failed_workflow_is_saved_to_database(orchestrator):
    """A failed workflow should also be saved to storage."""

    storage = Mock(spec=WorkflowStorage)
    orchestrator.storage = storage

    with patch.object(
        orchestrator.planner,
        "run",
        side_effect=RuntimeError("Test failure"),
    ):
        result = orchestrator.run(
            TaskRequest(task="Write a summary about Python.")
        )

    assert result.status == "failed"
    storage.save.assert_called_once_with(result)


def test_storage_failure_does_not_hide_workflow_result(orchestrator):
    """A storage failure should not change a successful workflow result."""

    storage = Mock(spec=WorkflowStorage)
    storage.save.side_effect = RuntimeError("Database unavailable")
    orchestrator.storage = storage

    plan_json = """
    {
        "steps": [
            {
                "agent": "researcher",
                "instruction": "Research Python."
            }
        ],
        "expected_output": "A short summary"
    }
    """

    review_json = """
    {
        "approved": true,
        "feedback": "Looks good.",
        "revised_content": null
    }
    """

    with (
        patch.object(
            orchestrator.planner,
            "run",
            return_value=plan_json,
        ),
        patch.object(
            orchestrator.researcher,
            "run",
            return_value="Python research notes.",
        ),
        patch.object(
            orchestrator.content_agent,
            "run",
            return_value="Python summary.",
        ),
        patch.object(
            orchestrator.reviewer,
            "run",
            return_value=review_json,
        ),
    ):
        result = orchestrator.run(
            TaskRequest(task="Write a summary about Python.")
        )

    assert result.status == "success"
    assert result.final_output == "Python summary."
    storage.save.assert_called_once_with(result)