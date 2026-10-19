import pytest

from core.models import WorkflowResult
from services.storage import WorkflowStorage


@pytest.fixture
def storage(tmp_path):
    database_path = tmp_path / "test_workflows.db"
    return WorkflowStorage(database_path)


@pytest.fixture
def sample_result():
    return WorkflowResult(
        task="Write a Python tutorial.",
        status="success",
        final_output="Python is a programming language.",
    )


def test_save_workflow_returns_id(storage, sample_result):
    workflow_id = storage.save(sample_result)

    assert isinstance(workflow_id, int)
    assert workflow_id > 0


def test_saved_workflow_appears_in_history(storage, sample_result):
    storage.save(sample_result)

    history = storage.get_history()

    assert len(history) == 1
    assert history[0]["task"] == "Write a Python tutorial."
    assert history[0]["status"] == "success"
    assert history[0]["final_output"] == (
        "Python is a programming language."
    )


def test_history_returns_newest_first(storage):
    first = WorkflowResult(
        task="First task",
        status="success",
        final_output="First result",
    )
    second = WorkflowResult(
        task="Second task",
        status="success",
        final_output="Second result",
    )

    storage.save(first)
    storage.save(second)

    history = storage.get_history()

    assert len(history) == 2
    assert history[0]["task"] == "Second task"
    assert history[1]["task"] == "First task"


def test_history_limit(storage):
    for number in range(3):
        storage.save(
            WorkflowResult(
                task=f"Task {number}",
                status="success",
                final_output=f"Result {number}",
            )
        )

    history = storage.get_history(limit=2)

    assert len(history) == 2


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_invalid_history_limit(storage, limit):
    with pytest.raises(ValueError, match="History limit"):
        storage.get_history(limit=limit)


def test_failed_workflow_is_saved(storage):
    result = WorkflowResult(
        task="Test failure",
        status="failed",
        final_output="",
        error="Workflow could not be completed.",
    )

    storage.save(result)
    history = storage.get_history()

    assert history[0]["status"] == "failed"
    assert history[0]["error"] == (
        "Workflow could not be completed."
    )


def test_empty_history(storage):
    assert storage.get_history() == []