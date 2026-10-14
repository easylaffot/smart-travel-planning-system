"""SQLite persistence for generated travel-planning results."""

import sqlite3
from pathlib import Path

from pydantic import ValidationError

from smart_travel_planner.models import PlanningResult
from smart_travel_planner.utils.exceptions import WorkflowExecutionError


class PlanRepository:
    """Store and retrieve complete planning results by application ID."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

        if self.database_path.parent != Path("."):
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize()

    def save(self, result: PlanningResult) -> None:
        """Insert or replace one validated planning result."""

        payload = result.model_dump_json()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO travel_plans (
                        application_id,
                        status,
                        created_at,
                        payload
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(application_id) DO UPDATE SET
                        status = excluded.status,
                        created_at = excluded.created_at,
                        payload = excluded.payload
                    """,
                    (
                        result.application_id,
                        result.status.value,
                        result.created_at.isoformat(),
                        payload,
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise WorkflowExecutionError("The travel plan could not be saved.") from exc

    def get(self, application_id: str) -> PlanningResult | None:
        """Retrieve a planning result or return None when not found."""

        cleaned_id = application_id.strip()

        if not cleaned_id:
            raise ValueError("application_id must not be empty")

        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT payload
                    FROM travel_plans
                    WHERE application_id = ?
                    """,
                    (cleaned_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise WorkflowExecutionError("The travel plan could not be retrieved.") from exc

        if row is None:
            return None

        try:
            return PlanningResult.model_validate_json(row[0])
        except ValidationError as exc:
            raise WorkflowExecutionError("The stored travel plan is invalid.") from exc

    def list_application_ids(self) -> list[str]:
        """Return stored application IDs from newest to oldest."""

        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT application_id
                    FROM travel_plans
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise WorkflowExecutionError("Stored travel plans could not be listed.") from exc

        return [str(row[0]) for row in rows]

    def _initialize(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS travel_plans (
                        application_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload TEXT NOT NULL
                    )
                    """
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise WorkflowExecutionError(
                "The travel-plan database could not be initialized."
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
