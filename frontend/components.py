"""Reusable professional dashboard components."""

from collections.abc import Iterable
from html import escape

import streamlit as st


def render_header() -> None:
    """Render the primary dashboard hero."""

    st.markdown(
        """
        <section class="dashboard-header">
            <div class="eyebrow">Multi-agent travel intelligence</div>
            <h1 class="dashboard-title">
                Smart Travel Planning System
            </h1>
            <p class="dashboard-subtitle">
                Build a personalized, budget-aware itinerary using
                coordinated destination, accommodation, transport,
                finance, and scheduling specialists.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, caption: str | None = None) -> None:
    """Render a consistent section title."""

    st.markdown(
        f'<div class="section-heading">{escape(title)}</div>',
        unsafe_allow_html=True,
    )

    if caption:
        st.markdown(
            f'<div class="section-caption">{escape(caption)}</div>',
            unsafe_allow_html=True,
        )


def render_metric_card(
    label: str,
    value: str,
    support: str = "",
) -> None:
    """Render one dashboard metric card."""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            <div class="metric-support">{escape(support)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status: str, label: str | None = None) -> None:
    """Render a coloured data or workflow status badge."""

    normalized = status.strip().lower().replace(" ", "_")
    css_status = {
        "live": "live",
        "mock": "mock",
        "estimated": "estimated",
        "unavailable": "unavailable",
        "ready": "ready",
        "running": "running",
        "error": "error",
    }.get(normalized, "estimated")

    shown_label = label or normalized.replace("_", " ").title()

    st.markdown(
        (f'<span class="status-badge status-{css_status}">{escape(shown_label)}</span>'),
        unsafe_allow_html=True,
    )


def render_workflow_steps(
    steps: Iterable[tuple[str, str]],
) -> None:
    """Render the multi-agent process summary."""

    step_html = []

    for title, description in steps:
        step_html.append(
            '<div class="workflow-step">'
            '<span class="workflow-dot"></span>'
            '<div class="workflow-copy">'
            f'<div class="workflow-title">{escape(title)}</div>'
            f'<div class="workflow-description">'
            f"{escape(description)}"
            "</div>"
            "</div>"
            "</div>"
        )

    rendered = '<div class="content-card workflow-card">' + "".join(step_html) + "</div>"

    st.markdown(
        rendered,
        unsafe_allow_html=True,
    )


def render_empty_result() -> None:
    """Render the initial backend-ready empty state."""

    st.markdown(
        """
        <div class="content-card">
            <div class="metric-label">Travel plan workspace</div>
            <div class="metric-value">No plan generated yet</div>
            <div class="metric-support">
                Complete the customer requirements form to validate the
                trip request. Backend execution will be connected in
                Phase 5B.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
