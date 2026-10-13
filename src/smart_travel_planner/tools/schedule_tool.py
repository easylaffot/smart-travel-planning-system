"""Schedule validation utilities for travel itineraries."""

from __future__ import annotations

import json
from datetime import date, time
from decimal import Decimal, InvalidOperation

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator


class ScheduledActivity(BaseModel):
    """One itinerary activity within a trip window."""

    date: date
    start_time: time
    end_time: time
    title: str = Field(min_length=1)
    location: str = Field(min_length=1)
    category: str = Field(min_length=1)
    estimated_cost: Decimal = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    notes: str | None = None

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def parse_cost(cls, value: object) -> Decimal:
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("estimated_cost must be a valid decimal value") from exc

        if not parsed.is_finite():
            raise ValueError("estimated_cost must be finite")

        return parsed

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class DaySchedule(BaseModel):
    """A single day in a trip, ordered by time."""

    date: date
    activities: list[ScheduledActivity] = Field(default_factory=list)


class ScheduleValidationResult(BaseModel):
    """Result returned after validating and ordering a travel schedule."""

    valid: bool
    conflicts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ordered_days: list[DaySchedule] = Field(default_factory=list)
    activity_count: int = 0


class ItineraryScheduleValidatorInput(BaseModel):
    """Validated schedule payload for itinerary validation."""

    trip_start_date: date
    trip_end_date: date
    activities: list[dict] = Field(default_factory=list)


class ItineraryScheduleValidatorTool(BaseTool):
    """Validate schedule integrity and chronological ordering for a trip itinerary."""

    name: str = "itinerary_schedule_validator"
    description: str = (
        "Validate a trip itinerary for date coverage, time overlap, ordering, and duplicate "
        "activities before the plan is accepted."
    )
    args_schema: type[BaseModel] = ItineraryScheduleValidatorInput

    def _run(
        self,
        trip_start_date: date,
        trip_end_date: date,
        activities: list[dict] | None = None,
    ) -> str:
        """Validate and return a JSON payload summarizing itinerary health."""

        if trip_end_date < trip_start_date:
            return json.dumps(
                {
                    "status": "error",
                    "valid": False,
                    "conflicts": ["trip_end_date cannot be before trip_start_date"],
                    "warnings": [],
                    "ordered_days": [],
                    "activity_count": 0,
                    "error": "Trip end date cannot be before trip start date",
                },
                ensure_ascii=False,
                indent=2,
            )

        items = activities or []
        normalized: list[ScheduledActivity] = []
        conflicts: list[str] = []
        warnings: list[str] = []
        seen_keys: set[tuple[str, str, str, str, str]] = set()

        for activity in items:
            try:
                parsed = ScheduledActivity.model_validate(activity)
            except ValueError as exc:
                conflicts.append(str(exc))
                continue

            if parsed.date < trip_start_date or parsed.date > trip_end_date:
                conflicts.append(
                    "Activity "
                    f"'{parsed.title}' is outside the trip window for "
                    f"{parsed.date.isoformat()}"
                )
                continue

            if parsed.end_time <= parsed.start_time:
                conflicts.append(
                    "Activity "
                    f"'{parsed.title}' ends at {parsed.end_time.isoformat()} "
                    "before or at start time "
                    f"{parsed.start_time.isoformat()}"
                )
                continue

            key = (
                parsed.title.strip(),
                parsed.date.isoformat(),
                parsed.start_time.isoformat(),
                parsed.end_time.isoformat(),
                parsed.location.strip(),
            )
            if key in seen_keys:
                conflicts.append(
                    f"Duplicate activity rejected: {parsed.title} on {parsed.date.isoformat()}"
                )
                continue
            seen_keys.add(key)
            normalized.append(parsed)

        normalized.sort(key=lambda item: (item.date, item.start_time, item.title))

        for index, current in enumerate(normalized):
            for later in normalized[index + 1 :]:
                if current.date != later.date:
                    continue
                if later.start_time < current.end_time and later.end_time > current.start_time:
                    conflicts.append(
                        "Overlapping activities on "
                        f"{current.date.isoformat()}: '{current.title}' and "
                        f"'{later.title}'"
                    )

        ordered_days: list[DaySchedule] = []
        day_map: dict[date, list[ScheduledActivity]] = {}
        for item in normalized:
            day_map.setdefault(item.date, []).append(item)
        for day_value in sorted(day_map):
            ordered_days.append(
                DaySchedule(
                    date=day_value,
                    activities=sorted(
                        day_map[day_value],
                        key=lambda item: item.start_time,
                    ),
                )
            )

        if not normalized:
            warnings.append("No activities scheduled for the requested trip window.")

        result = ScheduleValidationResult(
            valid=not conflicts,
            conflicts=conflicts,
            warnings=warnings,
            ordered_days=ordered_days,
            activity_count=len(normalized),
        )

        return json.dumps(
            {
                "status": "success" if result.valid else "error",
                "valid": result.valid,
                "conflicts": result.conflicts,
                "warnings": result.warnings,
                "ordered_days": [
                    {
                        "date": day.date.isoformat(),
                        "activities": [
                            {
                                "date": activity.date.isoformat(),
                                "start_time": activity.start_time.isoformat(),
                                "end_time": activity.end_time.isoformat(),
                                "title": activity.title,
                                "location": activity.location,
                                "category": activity.category,
                                "estimated_cost": format(activity.estimated_cost, "f"),
                                "currency": activity.currency,
                                "notes": activity.notes,
                            }
                            for activity in day.activities
                        ],
                    }
                    for day in result.ordered_days
                ],
                "activity_count": result.activity_count,
                "error": None if result.valid else "Schedule validation failed.",
            },
            ensure_ascii=False,
            indent=2,
        )


itinerary_schedule_validator = ItineraryScheduleValidatorTool
