"""Export generated travel plans as JSON and Markdown."""

from html import escape

from frontend.view_models import format_currency
from smart_travel_planner.models import PlanningResult


def build_json_export(result: PlanningResult) -> str:
    """Return the complete planning result as formatted JSON."""

    return result.model_dump_json(indent=2)


def build_markdown_export(result: PlanningResult) -> str:
    """Return a readable Markdown representation of a travel plan."""

    if result.travel_plan is None:
        return _build_failed_result_markdown(result)

    plan = result.travel_plan
    budget = plan.budget_analysis
    currency = budget.currency

    lines = [
        "# Smart Travel Plan",
        "",
        f"**Application ID:** {result.application_id}",
        "",
        f"**Status:** {_display_text(result.status.value)}",
        "",
        "## Trip Overview",
        "",
        (
            f"- **Route:** "
            f"{result.customer_request.starting_location} to "
            f"{result.customer_request.destination}"
        ),
        (
            f"- **Dates:** "
            f"{result.customer_request.start_date.isoformat()} to "
            f"{result.customer_request.end_date.isoformat()}"
        ),
        (f"- **Duration:** {result.customer_request.duration_days} days"),
        (f"- **Travellers:** {result.customer_request.travellers}"),
        (
            f"- **Interests:** "
            f"{', '.join(_display_text(item.value) for item in result.customer_request.interests)}"
        ),
        "",
        "## Budget Summary",
        "",
        (f"- **Subtotal:** {format_currency(budget.subtotal, currency)}"),
        (f"- **Contingency:** {format_currency(budget.contingency_amount, currency)}"),
        (f"- **Estimated total:** {format_currency(budget.estimated_total, currency)}"),
        (f"- **Customer budget:** {format_currency(budget.customer_budget, currency)}"),
        (f"- **Difference:** {format_currency(budget.difference, currency)}"),
        f"- **Budget status:** {_display_text(budget.status)}",
        "",
        "## Day-by-Day Itinerary",
        "",
    ]

    if not plan.itinerary.day_schedules:
        lines.extend(
            [
                "No detailed daily schedule is available.",
                "",
            ]
        )
    else:
        for index, day in enumerate(
            plan.itinerary.day_schedules,
            start=1,
        ):
            day_number = day.get("day_number", index)
            date_value = day.get("date", "Date unavailable")
            title = day.get("title", f"Day {day_number}")

            lines.extend(
                [
                    (f"### Day {day_number}: {title} ({date_value})"),
                    "",
                ]
            )

            activities = day.get("activities", [])

            if not activities:
                lines.extend(
                    [
                        "- No activities listed.",
                        "",
                    ]
                )
                continue

            for activity in activities:
                start_time = activity.get(
                    "start_time",
                    "--:--",
                )
                end_time = activity.get(
                    "end_time",
                    "--:--",
                )
                activity_title = activity.get(
                    "title",
                    "Planned activity",
                )
                location = activity.get(
                    "location",
                    "Location unavailable",
                )
                category = _display_text(str(activity.get("category", "activity")))
                estimated_cost = format_currency(
                    activity.get("estimated_cost", "0"),
                    currency,
                )

                lines.append(f"- **{start_time}-{end_time}: {activity_title}**")
                lines.append(f"  - Location: {location}")
                lines.append(f"  - Category: {category}")
                lines.append(f"  - Estimated cost: {estimated_cost}")

            lines.append("")

    lines.extend(
        [
            "## Recommended Attractions",
            "",
        ]
    )

    if plan.destination_research.attractions:
        for attraction in plan.destination_research.attractions:
            name = attraction.get(
                "name",
                "Unnamed attraction",
            )
            category = _display_text(str(attraction.get("category", "activity")))
            duration = attraction.get(
                "duration",
                "Not available",
            )

            lines.append(f"- **{name}**: {category}, {duration}")
    else:
        lines.append("- No attraction recommendations available.")

    lines.extend(
        [
            "",
            "## Accommodation Options",
            "",
        ]
    )

    if plan.hotel_transport.hotels:
        for hotel in plan.hotel_transport.hotels:
            lines.append(
                f"- **{hotel.get('name', 'Hotel option')}**: "
                f"{format_currency(hotel.get('total_cost', '0'), currency)} "
                f"({_display_text(str(hotel.get('data_mode', 'unknown')))})"
            )
    else:
        lines.append("- No hotel options available.")

    lines.extend(
        [
            "",
            "## Transport Options",
            "",
        ]
    )

    if plan.hotel_transport.transport_options:
        for option in plan.hotel_transport.transport_options:
            lines.append(
                f"- **{option.get('operator', 'Transport option')}**: "
                f"{_display_text(str(option.get('mode', 'unknown')))}, "
                f"{format_currency(option.get('total_cost', '0'), currency)} "
                f"({_display_text(str(option.get('data_mode', 'unknown')))})"
            )
    else:
        lines.append("- No transport options available.")

    if result.revisions:
        lines.extend(
            [
                "",
                "## Budget Revision History",
                "",
            ]
        )

        for revision in result.revisions:
            lines.extend(
                [
                    f"### Revision {revision.revision_number}",
                    "",
                    (f"- Original total: {format_currency(revision.original_total, currency)}"),
                    (f"- Revised total: {format_currency(revision.revised_total, currency)}"),
                    (f"- Savings achieved: {format_currency(revision.savings_achieved, currency)}"),
                    f"- Reason: {revision.reason}",
                    "",
                ]
            )

    all_warnings = list(
        dict.fromkeys(
            result.warnings
            + plan.validation_warnings
            + plan.destination_research.warnings
            + plan.hotel_transport.warnings
            + plan.itinerary.warnings
        )
    )

    lines.extend(
        [
            "## Warnings and Limitations",
            "",
        ]
    )

    if all_warnings:
        lines.extend(f"- {warning}" for warning in all_warnings)
    else:
        lines.append("- No warnings were reported.")

    sources = list(
        dict.fromkeys(
            plan.destination_research.sources
            + plan.hotel_transport.sources
            + plan.itinerary.sources
        )
    )

    lines.extend(
        [
            "",
            "## Sources",
            "",
        ]
    )

    if sources:
        lines.extend(f"- {source}" for source in sources)
    else:
        lines.append("- No live research sources are available for this plan.")

    lines.extend(
        [
            "",
            "---",
            "",
            (
                "Generated by the Smart Travel Planning System. "
                "Mock results are not live booking offers."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def safe_download_filename(
    application_id: str,
    extension: str,
) -> str:
    """Build a filesystem-safe export filename."""

    safe_id = "".join(
        character for character in application_id if character.isalnum() or character in {"-", "_"}
    )

    normalized_extension = extension.lstrip(".").lower()

    return f"{safe_id or 'travel-plan'}.{normalized_extension}"


def escaped_preview(value: str) -> str:
    """Return HTML-safe preview content when needed."""

    return escape(value)


def _display_text(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _build_failed_result_markdown(
    result: PlanningResult,
) -> str:
    lines = [
        "# Smart Travel Plan",
        "",
        f"**Application ID:** {result.application_id}",
        "",
        f"**Status:** {_display_text(result.status.value)}",
        "",
        "## Errors",
        "",
    ]

    if result.errors:
        lines.extend(f"- {error}" for error in result.errors)
    else:
        lines.append("- No structured travel plan is available.")

    return "\n".join(lines) + "\n"
