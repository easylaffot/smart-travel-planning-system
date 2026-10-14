"""Streamlit session-state management."""

from typing import Any

import streamlit as st

DEFAULT_STATE: dict[str, Any] = {
    "planning_result": None,
    "validated_request": None,
    "workflow_status": "ready",
    "workflow_error": None,
    "active_result_tab": "itinerary",
    "execution_mode": "Demo mode",
}


def initialize_state() -> None:
    """Create frontend state values only when they are missing."""

    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_result_state() -> None:
    """Clear generated results while preserving form values."""

    st.session_state.planning_result = None
    st.session_state.workflow_status = "ready"
    st.session_state.workflow_error = None


def set_workflow_status(
    status: str,
    error: str | None = None,
) -> None:
    """Update the visible workflow status and optional error."""

    st.session_state.workflow_status = status
    st.session_state.workflow_error = error

    st.session_state.workflow_status = status
    st.session_state.workflow_error = error
