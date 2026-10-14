"""Professional Streamlit dashboard styling."""

import streamlit as st

DASHBOARD_CSS = """
<style>
:root {
    --navy-950: #071426;
    --navy-900: #0B1F3A;
    --navy-800: #132B4F;
    --blue-700: #1D4ED8;
    --blue-600: #2563EB;
    --blue-100: #DBEAFE;
    --teal-700: #0F766E;
    --teal-100: #CCFBF1;
    --gold-600: #B7791F;
    --gold-100: #FEF3C7;
    --green-700: #15803D;
    --green-100: #DCFCE7;
    --amber-700: #B45309;
    --amber-100: #FEF3C7;
    --red-700: #B91C1C;
    --red-100: #FEE2E2;
    --slate-900: #172033;
    --slate-700: #334155;
    --slate-600: #526078;
    --slate-400: #94A3B8;
    --slate-200: #E2E8F0;
    --slate-100: #F1F5F9;
    --white: #FFFFFF;
}

.stApp {
    background:
        radial-gradient(
            circle at 85% 8%,
            rgba(37, 99, 235, 0.08),
            transparent 28%
        ),
        #F4F7FB;
}

.block-container {
    max-width: 1480px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255, 255, 255, 0.10);
}

[data-testid="stSidebar"] * {
    color: #F8FAFC;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color: #172033 !important;
}

.dashboard-header {
    position: relative;
    overflow: hidden;
    padding: 2.2rem 2.4rem;
    border-radius: 22px;
    background:
        linear-gradient(
            118deg,
            #071426 0%,
            #0B1F3A 45%,
            #123C69 100%
        );
    box-shadow: 0 18px 45px rgba(7, 20, 38, 0.20);
    margin-bottom: 1.4rem;
}

.dashboard-header::after {
    content: "";
    position: absolute;
    width: 330px;
    height: 330px;
    border-radius: 50%;
    right: -110px;
    top: -165px;
    background: rgba(56, 189, 248, 0.13);
}

.eyebrow {
    color: #7DD3FC;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.dashboard-title {
    color: #FFFFFF;
    font-size: clamp(2rem, 4vw, 3.3rem);
    font-weight: 800;
    line-height: 1.05;
    margin: 0;
    max-width: 900px;
}

.dashboard-subtitle {
    color: #CBD5E1;
    font-size: 1.02rem;
    line-height: 1.7;
    max-width: 820px;
    margin-top: 0.9rem;
    margin-bottom: 0;
}

.section-heading {
    color: #172033;
    font-size: 1.2rem;
    font-weight: 800;
    margin: 1.4rem 0 0.8rem;
}

.section-caption {
    color: #526078;
    font-size: 0.9rem;
    margin-top: -0.55rem;
    margin-bottom: 1rem;
}

.metric-card {
    height: 100%;
    min-height: 128px;
    padding: 1.15rem 1.2rem;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    background: #FFFFFF;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.metric-label {
    color: #64748B;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.metric-value {
    color: #172033;
    font-size: 1.48rem;
    font-weight: 800;
    margin-top: 0.5rem;
    line-height: 1.2;
}

.metric-support {
    color: #64748B;
    font-size: 0.82rem;
    margin-top: 0.4rem;
}

.content-card {
    padding: 1.25rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 17px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.055);
    margin-bottom: 1rem;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.02em;
}

.status-live {
    color: #166534;
    background: #DCFCE7;
}

.status-mock {
    color: #92400E;
    background: #FEF3C7;
}

.status-estimated {
    color: #1E40AF;
    background: #DBEAFE;
}

.status-unavailable {
    color: #991B1B;
    background: #FEE2E2;
}

.status-ready {
    color: #1E40AF;
    background: #DBEAFE;
}

.status-running {
    color: #0F766E;
    background: #CCFBF1;
}

.status-error {
    color: #991B1B;
    background: #FEE2E2;
}

.budget-success {
    color: #166534;
    background: #F0FDF4;
    border-left: 5px solid #22C55E;
}

.budget-warning {
    color: #92400E;
    background: #FFFBEB;
    border-left: 5px solid #F59E0B;
}

.workflow-step {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    padding: 0.65rem 0;
    border-bottom: 1px solid rgba(226, 232, 240, 0.75);
}

.workflow-step:last-child {
    border-bottom: 0;
}

.workflow-dot {
    width: 11px;
    height: 11px;
    margin-top: 0.35rem;
    border-radius: 50%;
    background: #2563EB;
    box-shadow: 0 0 0 4px #DBEAFE;
}

.workflow-title {
    color: #172033;
    font-size: 0.9rem;
    font-weight: 750;
}

.workflow-description {
    color: #64748B;
    font-size: 0.78rem;
    margin-top: 0.12rem;
}

div[data-testid="stForm"] {
    padding: 1.2rem;
    background: #FFFFFF;
    border: 1px solid #DCE4EF;
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-baseweb="select"] > div {
    border-color: #CBD5E1 !important;
    background: #FFFFFF !important;
    color: #172033 !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.13) !important;
}

.stButton > button,
.stFormSubmitButton > button {
    min-height: 44px;
    border-radius: 10px;
    border: 1px solid #1D4ED8;
    background: #1D4ED8;
    color: #FFFFFF !important;
    font-weight: 750;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: #1E40AF;
    background: #1E40AF;
    color: #FFFFFF !important;
}

[data-testid="stTabs"] button {
    color: #475569;
    font-weight: 700;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1D4ED8;
}

hr {
    border-color: #E2E8F0;
}

@media (max-width: 780px) {
    .block-container {
        padding-left: 0.85rem;
        padding-right: 0.85rem;
    }

    .dashboard-header {
        padding: 1.5rem;
        border-radius: 16px;
    }

    .dashboard-title {
        font-size: 2rem;
    }

    .metric-card {
        min-height: 110px;
    }
}

/* Phase 5A visibility and layout corrections */
html {
    font-size: 16px;
}

[data-testid="stSidebar"] {
    min-width: 285px !important;
    max-width: 285px !important;
}

[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 285px !important;
    max-width: 285px !important;
}

[data-testid="stSidebar"] > div:first-child {
    width: 285px !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    font-size: 0.86rem;
    line-height: 1.45;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

.dashboard-header .dashboard-title {
    color: #FFFFFF !important;
    opacity: 1 !important;
    text-shadow: none !important;
}

.dashboard-header .dashboard-subtitle {
    color: #D7E2F0 !important;
    font-size: 1rem !important;
}

.dashboard-header .eyebrow {
    color: #7DD3FC !important;
}

.workflow-card {
    padding: 0.65rem 1.2rem;
}

.workflow-step {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    padding: 0.95rem 0;
    border-bottom: 1px solid #E2E8F0;
}

.workflow-step:last-child {
    border-bottom: none;
}

.workflow-copy {
    flex: 1;
    min-width: 0;
}

.workflow-title {
    color: #172033 !important;
    font-size: 0.92rem;
    font-weight: 800;
    line-height: 1.35;
}

.workflow-description {
    color: #64748B !important;
    font-size: 0.82rem;
    line-height: 1.5;
    margin-top: 0.2rem;
}

.workflow-dot {
    display: block;
    flex: 0 0 11px;
}

div[data-testid="stForm"] label,
div[data-testid="stForm"] p {
    font-size: 0.84rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-baseweb="select"] * {
    font-size: 0.88rem !important;
}

.stButton > button,
.stFormSubmitButton > button {
    font-size: 0.88rem !important;
}

@media (max-width: 1100px) {
    [data-testid="stSidebar"] {
        min-width: 245px !important;
        max-width: 245px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 245px !important;
    }
}


.sidebar-status-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.8rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-status-label {
    color: #CBD5E1 !important;
    font-size: 0.78rem !important;
    line-height: 1.35;
}

.sidebar-status-value {
    color: #FFFFFF !important;
    font-size: 0.78rem !important;
    font-weight: 800;
    line-height: 1.35;
    text-align: right;
    white-space: nowrap;
}

</style>
"""


def apply_styles() -> None:
    """Inject the dashboard stylesheet."""

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
