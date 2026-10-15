"""Result rendering components for the travel dashboard."""

from html import escape
from typing import Any

import streamlit as st

from frontend.components import (
    render_metric_card,
    render_section_heading,
    render_status_badge,
)
from frontend.exporters import (
    build_json_export,
    build_markdown_export,
    safe_download_filename,
)
from frontend.view_models import format_currency
from smart_travel_planner.models import PlanningResult


def render_planning_result(result: PlanningResult) -> None:
    """Render the complete structured travel-planning result."""

    if result.travel_plan is None:
        st.error("No structured travel plan is available.")
        for error in result.errors:
            st.write(error)
        return

    plan = result.travel_plan
    currency = plan.budget_analysis.currency

    render_section_heading(
        "Generated travel plan",
        (
            f"Application ID: {result.application_id} · "
            f"Status: {result.status.value.replace('_', ' ').title()}"
        ),
    )

    json_export = build_json_export(result)
    markdown_export = build_markdown_export(result)

    download_json_col, download_markdown_col = st.columns(2)

    with download_json_col:
        st.download_button(
            "Download plan as JSON",
            data=json_export,
            file_name=safe_download_filename(
                result.application_id,
                "json",
            ),
            mime="application/json",
            use_container_width=True,
        )

    with download_markdown_col:
        st.download_button(
            "Download plan as Markdown",
            data=markdown_export,
            file_name=safe_download_filename(
                result.application_id,
                "md",
            ),
            mime="text/markdown",
            use_container_width=True,
        )

    summary_columns = st.columns(4)

    cards = [
        (
            "Destination",
            plan.itinerary.destination,
            (f"{plan.itinerary.start_date.isoformat()} to {plan.itinerary.end_date.isoformat()}"),
        ),
        (
            "Estimated total",
            format_currency(
                plan.budget_analysis.estimated_total,
                currency,
            ),
            "Verified budget calculation",
        ),
        (
            "Customer budget",
            format_currency(
                plan.budget_analysis.customer_budget,
                currency,
            ),
            "Validated customer constraint",
        ),
        (
            "Budget difference",
            format_currency(
                plan.budget_analysis.difference,
                currency,
            ),
            ("Remaining" if plan.budget_analysis.within_budget else "Deficit"),
        ),
    ]

    for column, card in zip(
        summary_columns,
        cards,
        strict=True,
    ):
        with column:
            render_metric_card(
                label=card[0],
                value=card[1],
                support=card[2],
            )

    if plan.budget_analysis.within_budget:
        st.success("The current travel plan is within the customer budget.")
    else:
        st.warning(
            "The current travel plan remains over budget. "
            "Review the alternatives and revision details."
        )

    tabs = st.tabs(
        [
            "Itinerary",
            "Attractions",
            "Hotels",
            "Transport",
            "Budget",
            "Sources & warnings",
        ]
    )

    with tabs[0]:
        render_itinerary(plan.itinerary.day_schedules, currency)

    with tabs[1]:
        render_attractions(
            plan.destination_research.attractions,
            plan.destination_research.local_experiences,
            routing_notes=plan.destination_research.routing_notes,
            weather_summary=plan.destination_research.weather_summary,
        )

    with tabs[2]:
        render_options(
            plan.hotel_transport.hotels,
            option_type="hotel",
            currency=currency,
        )

    with tabs[3]:
        render_options(
            plan.hotel_transport.transport_options,
            option_type="transport",
            currency=currency,
        )

    with tabs[4]:
        render_budget(result)

    with tabs[5]:
        render_sources_and_warnings(result)


def render_itinerary(
    day_schedules: list[dict[str, Any]],
    currency: str,
) -> None:
    """Render day-by-day travel schedules."""

    if not day_schedules:
        st.info("No detailed itinerary entries are available.")
        return

    for index, day in enumerate(day_schedules, start=1):
        day_number = day.get("day_number", index)
        date_value = day.get("date", "Date unavailable")
        title = day.get("title", f"Day {day_number}")

        with st.expander(
            f"Day {day_number} · {date_value} · {title}",
            expanded=index == 1,
        ):
            activities = day.get("activities", [])

            if not activities:
                st.caption("No activities are listed for this day.")
                continue

            for activity in activities:
                start = activity.get("start_time", "--:--")
                end = activity.get("end_time", "--:--")
                activity_title = activity.get(
                    "title",
                    "Planned activity",
                )
                location = activity.get(
                    "location",
                    "Location unavailable",
                )
                category = activity.get("category", "activity")
                cost = activity.get("estimated_cost", "0.00")

                st.markdown(
                    f"""
                    <div class="itinerary-item">
                        <div class="itinerary-time">
                            {escape(str(start))}–{escape(str(end))}
                        </div>
                        <div class="itinerary-copy">
                            <div class="itinerary-title">
                                {escape(str(activity_title))}
                            </div>
                            <div class="itinerary-meta">
                                {escape(str(location))} ·
                                {escape(str(category).replace("_", " ").title())}
                                · {escape(format_currency(cost, currency))}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_attractions(
    attractions: list[dict[str, Any]],
    experiences: list[dict[str, Any]],
    *,
    routing_notes: list[str] | None = None,
    weather_summary: dict[str, Any] | None = None,
) -> None:
    """Render destination recommendations."""

    render_section_heading("Recommended attractions")

    if not attractions:
        st.info("No attraction recommendations are available.")
        render_status_badge("unavailable", "Unavailable")
    else:
        columns = st.columns(2)

        for index, attraction in enumerate(attractions):
            with columns[index % 2]:
                render_option_card(
                    title=str(
                        attraction.get(
                            "name",
                            "Unnamed attraction",
                        )
                    ),
                    lines=[
                        (
                            "Category",
                            _format_category(str(attraction.get("category", "Not available"))),
                        ),
                        (
                            "Duration",
                            str(
                                attraction.get(
                                    "duration",
                                    "Not available",
                                )
                            ),
                        ),
                    ],
                    data_mode=str(
                        attraction.get(
                            "data_mode",
                            "estimated",
                        )
                    ),
                    source_url=str(attraction.get("source_url", "")),
                )

    render_section_heading("Local experiences")

    if not experiences:
        st.info("No local experiences are available.")
        render_status_badge("unavailable", "Unavailable")
    else:
        for experience in experiences:
            render_option_card(
                title=str(
                    experience.get(
                        "name",
                        "Local experience",
                    )
                ),
                lines=[
                    (
                        "Category",
                        _format_category(str(experience.get("category", "Not available"))),
                    )
                ],
                data_mode=str(
                    experience.get(
                        "data_mode",
                        "estimated",
                    )
                ),
                source_url=str(experience.get("source_url", "")),
            )

    if routing_notes:
        render_section_heading("Route guidance")
        st.caption("Route Estimate")
        for note in routing_notes:
            st.write(note)
    else:
        st.caption("Route Estimate: Unavailable")

    weather_mode = (
        str(weather_summary.get("data_mode", "unavailable")).lower()
        if weather_summary is not None
        else "unavailable"
    )
    weather_label = "Live Weather" if weather_mode == "live" else "Unavailable"
    render_status_badge(weather_mode, weather_label)
    if weather_summary is not None:
        summary = weather_summary.get("summary") or weather_summary.get("description")
        if summary:
            st.write(str(summary))


def render_options(
    options: list[dict[str, Any]],
    option_type: str,
    currency: str,
) -> None:
    """Render hotel or transport comparison cards."""

    if not options:
        st.info(f"No {option_type} options are available.")
        render_status_badge("unavailable", "Unavailable")
        return

    columns = st.columns(2)

    for index, option in enumerate(options):
        with columns[index % 2]:
            if option_type == "hotel":
                title = str(option.get("name", "Hotel option"))
                lines = [
                    ("Category", option.get("category", "N/A")),
                    ("Rating", option.get("rating", "N/A")),
                    ("Rooms", option.get("rooms", "N/A")),
                    ("Nights", option.get("nights", "N/A")),
                    (
                        "Estimated Price",
                        format_currency(
                            option.get("total_cost", "0"),
                            currency,
                        ),
                    ),
                ]
            else:
                title = str(
                    option.get(
                        "operator",
                        "Transport option",
                    )
                )
                lines = [
                    ("Mode", option.get("mode", "N/A")),
                    (
                        "Duration",
                        (f"{option.get('duration_minutes', 'N/A')} minutes"),
                    ),
                    (
                        "Departure",
                        option.get("departure_time", "N/A"),
                    ),
                    (
                        "Arrival",
                        option.get("arrival_time", "N/A"),
                    ),
                    (
                        "Estimated Fare",
                        format_currency(
                            option.get("total_cost", "0"),
                            currency,
                        ),
                    ),
                ]

            render_option_card(
                title=title,
                lines=[(str(label), str(value)) for label, value in lines],
                data_mode=str(option.get("data_mode", "mock")),
                source_url=str(option.get("source_url", "")),
            )


def render_option_card(
    title: str,
    lines: list[tuple[str, str]],
    data_mode: str,
    source_url: str = "",
) -> None:
    """Render one comparison card."""

    with st.container(border=True):
        st.markdown(f"#### {title}")
        render_status_badge(data_mode, _data_mode_label(data_mode))

        for label, value in lines:
            left, right = st.columns([0.8, 1.2])
            left.caption(label)
            right.markdown(f"**{value}**")

        safe_url = _safe_source_url(source_url)
        if safe_url:
            st.link_button("Live Source", safe_url)


def render_budget(result: PlanningResult) -> None:
    """Render the verified budget and revision history."""

    if result.travel_plan is None:
        return

    budget = result.travel_plan.budget_analysis
    currency = budget.currency

    budget_rows = [
        ("Subtotal", budget.subtotal),
        ("Contingency", budget.contingency_amount),
        ("Estimated total", budget.estimated_total),
        ("Customer budget", budget.customer_budget),
        ("Difference", budget.difference),
    ]

    for label, value in budget_rows:
        left, right = st.columns([1.2, 1])
        left.markdown(f"**{label}**")
        right.markdown(f"**{format_currency(value, currency)}**")

    st.markdown("---")

    render_status_badge(
        "live" if budget.within_budget else "unavailable",
        "Within budget" if budget.within_budget else "Over budget",
    )

    if budget.cost_reduction_recommendations:
        st.markdown("#### Cost-reduction recommendations")

        for recommendation in budget.cost_reduction_recommendations:
            st.write(f"• {recommendation}")

    if result.revisions:
        st.markdown("#### Revision history")

        for revision in result.revisions:
            with st.expander(
                f"Revision {revision.revision_number}",
            ):
                st.write(
                    "Original total:",
                    format_currency(
                        revision.original_total,
                        currency,
                    ),
                )
                st.write(
                    "Revised total:",
                    format_currency(
                        revision.revised_total,
                        currency,
                    ),
                )
                st.write(
                    "Savings:",
                    format_currency(
                        revision.savings_achieved,
                        currency,
                    ),
                )
                st.write(
                    "Remaining difference:",
                    format_currency(
                        revision.remaining_difference,
                        currency,
                    ),
                )
                st.write("Reason:", revision.reason)


def render_sources_and_warnings(
    result: PlanningResult,
) -> None:
    """Render sources, warnings, errors, and data labels."""

    if result.travel_plan is None:
        return

    plan = result.travel_plan

    sources = list(
        dict.fromkeys(
            plan.destination_research.sources
            + plan.hotel_transport.sources
            + plan.itinerary.sources
        )
    )

    st.markdown("#### Data status")

    modes = list(
        dict.fromkeys(plan.destination_research.data_modes + plan.hotel_transport.data_modes)
    )

    if modes:
        columns = st.columns(min(len(modes), 4))

        for index, mode in enumerate(modes):
            with columns[index % len(columns)]:
                render_status_badge(mode)
    else:
        st.caption("No data-mode labels were supplied.")

    st.markdown("#### Sources")

    if sources:
        for source in sources:
            safe_url = _safe_source_url(source)
            if safe_url:
                st.link_button("Live Source", safe_url)
            else:
                st.write(f"• {source}")
    else:
        st.info("No live research sources are available in offline demo mode.")

    warnings = list(
        dict.fromkeys(
            result.warnings
            + plan.validation_warnings
            + plan.destination_research.warnings
            + plan.hotel_transport.warnings
            + plan.itinerary.warnings
        )
    )

    if warnings:
        st.markdown("#### Warnings and limitations")

        for warning in warnings:
            st.warning(warning)

    if result.errors:
        st.markdown("#### Errors")

        for error in result.errors:
            st.error(error)


def _data_mode_label(data_mode: str) -> str:
    normalized = data_mode.strip().lower()
    if normalized == "live":
        return "Live Source"
    if normalized == "mock":
        return "Mock Fallback"
    if normalized == "unavailable":
        return "Unavailable"
    return normalized.replace("_", " ").title()


def _format_category(category: str) -> str:
    return {
        "local_food": "Local Food",
        "cultural_experience": "Cultural Experience",
    }.get(category.strip().lower(), category.replace("_", " ").title())


def _safe_source_url(source_url: str) -> str | None:
    candidate = source_url.strip()
    if candidate.lower().startswith(("http://", "https://")):
        return candidate
    return None
