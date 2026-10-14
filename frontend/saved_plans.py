"""Saved-plan retrieval controls for Streamlit."""

import streamlit as st

from smart_travel_planner.storage import PlanRepository

DEFAULT_DATABASE_PATH = "data/travel_plans.db"


def get_repository() -> PlanRepository:
    """Return the frontend travel-plan repository."""

    return PlanRepository(DEFAULT_DATABASE_PATH)


def render_saved_plan_lookup() -> None:
    """Render recent-plan and application-ID retrieval controls."""

    st.markdown("### Saved travel plans")

    repository = get_repository()
    application_ids = repository.list_application_ids()

    if not application_ids:
        st.caption("No saved plans are available yet. Generate a plan first.")
        return

    selected_id = st.selectbox(
        "Recent application IDs",
        options=application_ids,
        key="saved_application_id",
    )

    manual_id = st.text_input(
        "Or enter an application ID",
        placeholder="TRIP-XXXXXXXXXXXX",
        key="manual_application_id",
    )

    lookup_id = manual_id.strip() or selected_id

    if st.button(
        "Load saved plan",
        use_container_width=True,
        key="load_saved_plan",
    ):
        result = repository.get(lookup_id)

        if result is None:
            st.error("No saved travel plan was found for that application ID.")
            return

        st.session_state.planning_result = result
        st.session_state.validated_request = result.customer_request
        st.session_state.workflow_status = "ready"
        st.session_state.workflow_error = None

        st.success(f"Loaded {result.application_id}")
        st.rerun()
