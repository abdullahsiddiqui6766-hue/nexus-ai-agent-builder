import sqlite3
from pathlib import Path

from core.models import WorkflowResult


class WorkflowStorage:
    """Store and retrieve workflow history using SQLite."""

    def __init__(
        self,
        database_path: str | Path = "data/workflows.db",
    ) -> None:
        self.database_path = Path(database_path)

        if str(database_path) != ":memory:":
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""

        return sqlite3.connect(str(self.database_path))

    def _initialize_database(self) -> None:
        """Create the workflow history table if it does not exist."""

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    final_output TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    )
                )
                """
            )

    def save(self, result: WorkflowResult) -> int:
        """Save a workflow result and return its database ID."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO workflows (
                    task,
                    status,
                    final_output,
                    error
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    result.task,
                    result.status,
                    result.final_output,
                    result.error,
                ),
            )

            return int(cursor.lastrowid)

    def get_history(self, limit: int = 20) -> list[dict]:
        """Return the most recent workflow records."""

        if not 1 <= limit <= 100:
            raise ValueError("History limit must be between 1 and 100.")

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    id,
                    task,
                    status,
                    final_output,
                    error,
                    created_at
                FROM workflows
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]