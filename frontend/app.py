"""Professional Streamlit interface for the travel-planning system."""

from datetime import date, timedelta
from decimal import Decimal

import streamlit as st
from pydantic import ValidationError

from frontend.backend import (
    build_demo_workflow,
    build_live_workflow,
    live_mode_available,
)
from frontend.components import (
    render_empty_result,
    render_header,
    render_metric_card,
    render_section_heading,
    render_status_badge,
    render_workflow_steps,
)
from frontend.result_components import render_planning_result
from frontend.saved_plans import render_saved_plan_lookup
from frontend.state import (
    initialize_state,
    reset_result_state,
    set_workflow_status,
)
from frontend.styles import apply_styles
from smart_travel_planner.models import (
    Activity,
    CustomerTravelRequest,
    TravelClass,
)

st.set_page_config(
    page_title="Smart Travel Planning System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


ACTIVITY_LABELS = {
    "Sightseeing": Activity.SIGHTSEEING,
    "Shopping": Activity.SHOPPING,
    "Adventure": Activity.ADVENTURE,
    "Relaxation": Activity.RELAXATION,
    "Local food": Activity.LOCAL_FOOD,
    "Culture": Activity.CULTURE,
    "Nature": Activity.NATURE,
}

ACCOMMODATION_OPTIONS = {
    "Budget": TravelClass.BUDGET,
    "Mid-range": TravelClass.MID_RANGE,
    "Premium": TravelClass.PREMIUM,
}


def render_sidebar() -> None:
    """Render system status and workflow information."""

    with st.sidebar:
        st.markdown("## Travel Operations")
        st.caption(
            "CrewAI specialists coordinate destination research, "
            "travel options, financial checks, and itinerary design."
        )

        render_status_badge(
            st.session_state.workflow_status,
            st.session_state.workflow_status.replace("_", " ").title(),
        )

        st.markdown("---")
        st.markdown("### System status")

        status_rows = [
            ("Backend workflow", "Ready"),
            ("Travel agents", "5 configured"),
            ("Workflow process", "Sequential"),
            ("Budget revision", "Enabled"),
            ("Hotel data", "Mock fallback"),
            ("Transport data", "Mock fallback"),
        ]

        for label, value in status_rows:
            st.markdown(
                (
                    '<div class="sidebar-status-row">'
                    f'<span class="sidebar-status-label">{label}</span>'
                    f'<span class="sidebar-status-value">{value}</span>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.caption(
            "Prototype hotel and transport inventory is always labelled "
            "as mock data and must not be treated as a live booking offer."
        )

        st.markdown("---")
        render_saved_plan_lookup()


def render_trip_form() -> CustomerTravelRequest | None:
    """Collect and validate customer requirements."""

    tomorrow = date.today() + timedelta(days=1)

    with st.form(
        "travel_requirements_form",
        clear_on_submit=False,
        border=True,
    ):
        render_section_heading(
            "Customer travel requirements",
            (
                "Provide the core trip constraints. Dates, budget, and "
                "preferences are validated before agent execution."
            ),
        )

        origin_col, destination_col = st.columns(2)

        starting_location = origin_col.text_input(
            "Starting location",
            value="Mumbai",
            placeholder="Example: Mumbai",
        )

        destination = destination_col.text_input(
            "Destination",
            value="Jaipur",
            placeholder="Example: Jaipur",
        )

        start_col, end_col, traveller_col = st.columns([1, 1, 0.8])

        start_date = start_col.date_input(
            "Start date",
            value=tomorrow,
            min_value=date.today(),
        )

        end_date = end_col.date_input(
            "End date",
            value=tomorrow + timedelta(days=3),
            min_value=date.today(),
        )

        travellers = traveller_col.number_input(
            "Travellers",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
        )

        budget_col, currency_col = st.columns([1.4, 0.6])

        total_budget = budget_col.number_input(
            "Total budget",
            min_value=1000.0,
            max_value=100000000.0,
            value=60000.0,
            step=1000.0,
            format="%.2f",
        )

        currency = currency_col.selectbox(
            "Currency",
            options=["INR", "USD", "EUR", "GBP", "AED"],
            index=0,
        )

        activity_names = st.multiselect(
            "Preferred activities",
            options=list(ACTIVITY_LABELS),
            default=["Sightseeing", "Shopping", "Local food"],
            placeholder="Select at least one interest",
        )

        preference_col, transport_col = st.columns(2)

        accommodation_label = preference_col.selectbox(
            "Accommodation preference",
            options=list(ACCOMMODATION_OPTIONS),
            index=1,
        )

        transport_preference = transport_col.selectbox(
            "Transport preference",
            options=["Flight", "Train", "Bus", "Any"],
            index=0,
        )

        with st.expander("Advanced preferences"):
            special_requirements = st.text_area(
                "Special requirements",
                placeholder=(
                    "Accessibility, dietary, mobility, check-in, or other travel requirements"
                ),
                max_chars=1000,
            )

        submitted = st.form_submit_button(
            "Validate trip requirements",
            use_container_width=True,
        )

    if not submitted:
        return None

    try:
        request = CustomerTravelRequest(
            starting_location=starting_location,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            travellers=int(travellers),
            total_budget=Decimal(str(total_budget)),
            currency=currency,
            interests=[ACTIVITY_LABELS[name] for name in activity_names],
            accommodation_preference=(ACCOMMODATION_OPTIONS[accommodation_label]),
            transport_preference=transport_preference.lower(),
            special_requirements=(special_requirements.strip() or None),
        )
    except ValidationError as exc:
        set_workflow_status("error", str(exc))
        st.error(
            "The trip requirements could not be validated. "
            "Review the highlighted values and try again."
        )
        st.code(str(exc), language="text")
        return None

    st.session_state.validated_request = request
    set_workflow_status("ready")
    st.success("Trip requirements validated. The request is ready for multi-agent planning.")
    return request


def render_request_summary(
    request: CustomerTravelRequest,
) -> None:
    """Render validated request metrics."""

    render_section_heading(
        "Validated trip overview",
        "This is the exact request that will be sent to the backend.",
    )

    cards = [
        (
            "Route",
            f"{request.starting_location} → {request.destination}",
            "Validated origin and destination",
        ),
        (
            "Trip duration",
            f"{request.duration_days} days",
            (f"{request.start_date.isoformat()} to {request.end_date.isoformat()}"),
        ),
        (
            "Travellers",
            str(request.travellers),
            request.accommodation_preference.value.replace(
                "_",
                " ",
            ).title(),
        ),
        (
            "Total budget",
            f"{request.currency} {request.total_budget:,.2f}",
            request.transport_preference.title(),
        ),
    ]

    columns = st.columns(4)

    for column, card in zip(columns, cards, strict=True):
        with column:
            render_metric_card(
                label=card[0],
                value=card[1],
                support=card[2],
            )

    interest_text = ", ".join(
        interest.value.replace("_", " ").title() for interest in request.interests
    )

    st.markdown(
        f"""
        <div class="content-card">
            <div class="metric-label">Selected interests</div>
            <div class="metric-value">{interest_text}</div>
            <div class="metric-support">
                Recommendations will be prioritized using these
                preferences.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_generation_controls(
    request: CustomerTravelRequest,
) -> None:
    """Render workflow mode and plan-generation actions."""

    render_section_heading(
        "Generate travel plan",
        (
            "Demo mode uses deterministic offline data. Live AI mode "
            "uses the configured Ollama Cloud model and CrewAI agents."
        ),
    )

    mode_col, action_col = st.columns([0.55, 0.45])

    with mode_col:
        execution_mode = st.radio(
            "Execution mode",
            options=["Demo mode", "Live AI mode"],
            horizontal=True,
            key="execution_mode",
        )

    live_available = live_mode_available()

    with action_col:
        if execution_mode == "Live AI mode" and not live_available:
            st.warning(
                "Live AI mode requires OLLAMA_API_KEY and OLLAMA_MODEL in the private .env file."
            )

        generate_disabled = execution_mode == "Live AI mode" and not live_available

        generate_clicked = st.button(
            "Generate AI travel plan",
            type="primary",
            use_container_width=True,
            disabled=generate_disabled,
        )

    clear_clicked = st.button(
        "Clear generated plan",
        use_container_width=False,
    )

    if clear_clicked:
        reset_result_state()
        st.rerun()

    if not generate_clicked:
        return

    execute_planning_workflow(
        request=request,
        execution_mode=execution_mode,
    )


def execute_planning_workflow(
    request: CustomerTravelRequest,
    execution_mode: str,
) -> None:
    """Run the Phase 4 workflow and retain its structured result."""

    set_workflow_status("running")

    progress = st.progress(0)
    status = st.status(
        "Preparing the travel-planning workflow...",
        expanded=True,
    )

    try:
        status.write("Validating customer requirements")
        progress.progress(10)

        status.write("Preparing travel specialists and tools")
        progress.progress(25)

        if execution_mode == "Live AI mode":
            workflow = build_live_workflow()
            status.write("Running the live CrewAI agent workflow")
        else:
            workflow = build_demo_workflow(request)
            status.write("Running the deterministic offline demonstration")

        progress.progress(50)

        result = workflow.run(request)

        status.write("Validating final dates, budget, and status")
        progress.progress(80)

        st.session_state.planning_result = result

        if result.errors:
            set_workflow_status(
                "error",
                "; ".join(result.errors),
            )
            status.update(
                label="Travel plan completed with errors",
                state="error",
                expanded=True,
            )
        else:
            set_workflow_status("ready")
            progress.progress(100)
            status.update(
                label="Travel plan generated successfully",
                state="complete",
                expanded=False,
            )

        st.rerun()

    except Exception as exc:
        set_workflow_status("error", str(exc))
        status.update(
            label="Travel-plan generation failed",
            state="error",
            expanded=True,
        )
        st.error("The workflow could not generate the travel plan. No credentials were displayed.")


def render_result_workspace() -> None:
    """Render the generated plan or initial empty state."""

    result = st.session_state.planning_result

    if result is None:
        render_empty_result()
        return

    render_planning_result(result)


def main() -> None:
    """Render the complete Phase 5B travel dashboard."""

    initialize_state()
    apply_styles()
    render_sidebar()
    render_header()

    if st.session_state.workflow_error:
        st.error("The most recent workflow operation reported an error.")
        with st.expander("View error details"):
            st.code(
                st.session_state.workflow_error,
                language="text",
            )

    form_panel, workflow_panel = st.columns(
        [0.92, 1.08],
        gap="large",
    )

    with form_panel:
        request = render_trip_form()

    with workflow_panel:
        render_section_heading(
            "Agent workflow",
            ("Each specialist receives only the tools needed for the assigned responsibility."),
        )

        render_workflow_steps(
            [
                (
                    "Travel Coordinator",
                    "Interprets requirements and controls final review.",
                ),
                (
                    "Destination Research Specialist",
                    "Researches attractions, weather, and routing.",
                ),
                (
                    "Hotel and Transport Specialist",
                    "Compares accommodation and mobility options.",
                ),
                (
                    "Travel Budget Analyst",
                    "Calculates verified costs and budget difference.",
                ),
                (
                    "Itinerary Planner",
                    "Builds and validates the daily schedule.",
                ),
            ]
        )

    active_request = request or st.session_state.validated_request

    if active_request is not None:
        render_request_summary(active_request)
        render_generation_controls(active_request)

    render_section_heading(
        "Planning output",
        ("Structured itinerary, options, budget, data labels, sources, and warnings appear below."),
    )

    render_result_workspace()


if __name__ == "__main__":
    main()
