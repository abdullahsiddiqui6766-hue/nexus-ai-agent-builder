from __future__ import annotations

import logging
from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from core.config import get_settings
from core.models import TaskRequest
from core.orchestrator import Orchestrator
from services.groq_client import GroqClient
from services.exporter import clean_markdown, export_markdown
from tools.search.factory import create_search_provider


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NEXUS AI | Agent Workspace",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --bg: #0b0d14;
        --panel: #121621;
        --panel-2: #171c29;
        --border: rgba(148, 163, 184, 0.16);
        --text: #f3f4f6;
        --muted: #9ca3af;
        --accent: #8b5cf6;
        --accent-2: #06b6d4;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                ellipse at 15% 0%,
                rgba(124, 58, 237, 0.12),
                transparent 38%
            ),
            radial-gradient(
                ellipse at 95% 10%,
                rgba(6, 182, 212, 0.08),
                transparent 32%
            ),
            var(--bg);
        color: var(--text);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #0e111a;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.04em;
    }

    .hero {
        padding: 30px;
        border-radius: 24px;
        border: 1px solid var(--border);
        background:
            linear-gradient(
                135deg,
                rgba(139, 92, 246, 0.18),
                rgba(6, 182, 212, 0.07)
            ),
            rgba(18, 22, 33, 0.94);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-kicker {
        color: #c4b5fd;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-title {
        color: #ffffff;
        font-size: clamp(30px, 4vw, 48px);
        line-height: 1.12;
        font-weight: 800;
        margin: 0 0 12px 0;
    }

    .hero-description {
        color: #c4c8d4;
        font-size: 15px;
        line-height: 1.8;
        max-width: 720px;
        margin: 0;
    }

    .status-pill {
        display: inline-block;
        border: 1px solid rgba(16, 185, 129, 0.30);
        background: rgba(16, 185, 129, 0.09);
        color: #6ee7b7;
        padding: 7px 11px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 18px;
    }

    .section-label {
        color: #c4b5fd;
        text-transform: uppercase;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.6px;
        margin-bottom: 8px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 800;
        color: #f9fafb;
        margin-bottom: 5px;
    }

    .section-description {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
        margin-bottom: 20px;
    }

    .agent-card {
        background: linear-gradient(
            145deg,
            rgba(23, 28, 41, 0.98),
            rgba(17, 21, 31, 0.98)
        );
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 20px 17px;
        min-height: 150px;
        transition: border-color 0.2s ease;
    }

    .agent-card:hover {
        border-color: rgba(139, 92, 246, 0.65);
    }

    .agent-icon {
        font-size: 26px;
        margin-bottom: 12px;
    }

    .agent-name {
        color: #f9fafb;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 7px;
    }

    .agent-description {
        color: #9ca3af;
        font-size: 12px;
        line-height: 1.65;
    }

    .result-box {
        background: rgba(18, 22, 33, 0.95);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 20px;
        margin-top: 12px;
    }

    .result-heading {
        color: #ffffff;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .result-subheading {
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 15px;
    }

    .small-muted {
        color: #9ca3af;
        font-size: 12px;
        line-height: 1.7;
    }

    div[data-testid="stMetric"] {
        background: rgba(18, 22, 33, 0.90);
        border: 1px solid var(--border);
        padding: 16px;
        border-radius: 15px;
    }

    div[data-testid="stMetricLabel"] {
        color: #9ca3af;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    .stTextArea textarea {
        background: #111520 !important;
        color: #f9fafb !important;
        border: 1px solid #303747 !important;
        border-radius: 14px !important;
        line-height: 1.7 !important;
    }

    .stTextArea textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 1px #8b5cf6 !important;
    }

    .stButton > button {
        border-radius: 11px;
        min-height: 45px;
        font-weight: 700;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(100deg, #7c3aed, #6d5dfc);
        border: none;
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(100deg, #6d28d9, #5b4ce6);
        border: none;
    }

    .stDownloadButton > button {
        width: 100%;
        background: rgba(139, 92, 246, 0.12);
        color: #ddd6fe;
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 11px;
        min-height: 43px;
        font-weight: 700;
    }

    hr {
        border-color: var(--border);
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .hero {
            padding: 22px;
        }

        .block-container {
            padding-top: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None

if "last_task" not in st.session_state:
    st.session_state.last_task = ""

if "last_search_enabled" not in st.session_state:
    st.session_state.last_search_enabled = False


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_result_value(result: Any, key: str, default: Any = None) -> Any:
    """Safely retrieve a field from a Pydantic model or object."""
    if result is None:
        return default

    if isinstance(result, dict):
        return result.get(key, default)

    return getattr(result, key, default)


def get_agent_results(result: Any) -> list:
    """Return the list of agent results without assuming a specific model."""
    agent_results = get_result_value(result, "agent_results", [])

    if isinstance(agent_results, list):
        return agent_results

    return []


def get_agent_name(agent: Any) -> str:
    name = get_result_value(agent, "agent_name", "AI Agent")
    return str(name)


def get_agent_content(agent: Any) -> str:
    content = get_result_value(agent, "content", "")
    return str(content) if content is not None else ""


def make_download_name(task: str) -> str:
    """Generate a safe report filename."""
    words = [
        word.lower()
        for word in task.split()
        if word.isalnum()
    ]

    slug = "-".join(words[:5]) or "ai-report"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    return f"nexus-report-{slug}-{timestamp}.md"


def render_agent_card(
    icon: str,
    name: str,
    description: str,
) -> None:
    st.markdown(
        f"""
        <div class="agent-card">
            <div class="agent-icon">{icon}</div>
            <div class="agent-name">{escape(name)}</div>
            <div class="agent-description">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="
                width:43px;
                height:43px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-radius:13px;
                background:linear-gradient(135deg,#7c3aed,#06b6d4);
                font-size:23px;
            ">🤖</div>
            <div>
                <div style="
                    color:#ffffff;
                    font-size:17px;
                    font-weight:800;
                ">NEXUS AI</div>
                <div style="
                    color:#9ca3af;
                    font-size:11px;
                ">Agent Workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### ⚙️ Workspace Settings")

    search_enabled = st.toggle(
        "Enable Web Search",
        value=False,
        help=(
            "Allow the Researcher agent to retrieve web search results "
            "when a search provider is configured."
        ),
    )

    st.caption(
        "Web Search OFF: research uses the AI model without live search results."
    )

    st.divider()

    st.markdown("### 🧩 AI Agent Team")

    st.markdown(
        """
        <div class="small-muted">
        <b style="color:#c4b5fd;">01 · Planner</b><br>
        Breaks your task into steps.<br><br>

        <b style="color:#67e8f9;">02 · Researcher</b><br>
        Collects relevant information.<br><br>

        <b style="color:#86efac;">03 · Content</b><br>
        Creates the requested output.<br><br>

        <b style="color:#fcd34d;">04 · Reviewer</b><br>
        Reviews quality and completeness.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### 🔐 Configuration")
    st.caption(
        "API credentials are read from your local environment configuration."
    )

    st.markdown(
        """
        <div style="
            padding:12px;
            border:1px solid rgba(148,163,184,.15);
            border-radius:12px;
            background:rgba(255,255,255,.02);
            color:#9ca3af;
            font-size:11px;
            line-height:1.7;
        ">
        Keep your API keys private.<br>
        Never share your .env file publicly.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HERO HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">MULTI-AGENT INTELLIGENCE</div>
        <div class="hero-title">
            Turn complex tasks into<br>
            <span style="
                background:linear-gradient(90deg,#c4b5fd,#67e8f9);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
            ">intelligent outcomes.</span>
        </div>
        <p class="hero-description">
            Your personal AI workspace. Plan tasks, research information,
            generate professional content, and review results through
            a coordinated multi-agent workflow.
        </p>
        <div class="status-pill">● WORKSPACE READY</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# WORKSPACE METRICS
# ============================================================

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric("AI Agents", "4")

with metric2:
    st.metric(
        "Web Search",
        "Enabled" if search_enabled else "Disabled",
    )

with metric3:
    current_result = st.session_state.workflow_result
    current_status = get_result_value(
        current_result,
        "status",
        "Ready",
    )

    st.metric(
        "Last Workflow",
        str(current_status).capitalize(),
    )

with metric4:
    result_count = len(get_agent_results(current_result))
    st.metric("Agent Outputs", result_count)


st.write("")


# ============================================================
# TASK INPUT
# ============================================================

st.markdown(
    """
    <div class="section-label">WORKSPACE</div>
    <div class="section-title">Create a new task</div>
    <div class="section-description">
        Describe the outcome you want. The AI agents will work together
        to create a structured result.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    task = st.text_area(
        "Task instructions",
        value=st.session_state.last_task,
        placeholder=(
            "Example: Research artificial intelligence, explain its "
            "applications and limitations, and create a detailed report "
            "with clear headings and a conclusion."
        ),
        height=155,
        max_chars=10_000,
        label_visibility="collapsed",
    )

    col_info, col_button = st.columns([2, 1])

    with col_info:
        st.caption(
            f"{len(task)} / 10,000 characters · "
            "Be specific for better results."
        )

    with col_button:
        run_workflow = st.button(
            "🚀 Run AI Workflow",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# WORKFLOW EXECUTION
# ============================================================

if run_workflow:
    cleaned_task = task.strip()

    if len(cleaned_task) < 3:
        st.warning(
            "Please enter a task containing at least 3 characters."
        )

    else:
        st.session_state.last_task = cleaned_task
        st.session_state.last_search_enabled = search_enabled

        try:
            with st.status(
                "Preparing your AI workflow...",
                expanded=True,
            ) as workflow_status:

                st.write("⚙️ Loading application settings...")
                settings = get_settings()

                st.write("🧠 Connecting to the Groq language model...")
                client = GroqClient(
                    api_key=settings.groq_api_key,
                    model="openai/gpt-oss-120b",
                )

                search_provider = None

                if search_enabled:
                    st.write("🌐 Initializing the search provider...")

                    search_provider = create_search_provider(
                        settings.search_provider
                    )

                st.write("🔗 Preparing the multi-agent orchestrator...")

                orchestrator = Orchestrator(
                    groq_client=client,
                    search_provider=search_provider,
                )

                request = TaskRequest(
                    task=cleaned_task,
                    search_enabled=search_enabled,
                )

                st.write("🚀 Executing the agent workflow...")

                result = orchestrator.run(request)

                st.session_state.workflow_result = result

                result_status = str(
                    get_result_value(result, "status", "failed")
                ).lower()

                if result_status == "success":
                    workflow_status.update(
                        label="Workflow completed successfully",
                        state="complete",
                        expanded=False,
                    )
                else:
                    workflow_status.update(
                        label="Workflow could not be completed",
                        state="error",
                        expanded=True,
                    )

        except Exception as exc:
            logger.exception("Workflow execution failed.")

            st.error(
                "The workflow encountered an error. "
                "Check the details below and your application configuration."
            )

            with st.expander("Technical error details"):
                st.code(
                    f"{type(exc).__name__}: {exc}",
                    language="text",
                )

            st.info(
                "Check your Groq API configuration, model availability, "
                "search provider settings, and terminal logs."
            )


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.workflow_result

if result is not None:
    result_status = str(
        get_result_value(result, "status", "failed")
    ).lower()

    final_output = get_result_value(
        result,
        "final_output",
        "",
    )

    error_message = get_result_value(
        result,
        "error",
        None,
    )

    agent_results = get_agent_results(result)

    st.divider()

    st.markdown(
        """
        <div class="section-label">WORKFLOW OUTPUT</div>
        <div class="section-title">Your results</div>
        <div class="section-description">
            Review the generated content and inspect the output from
            individual agents.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result_status == "success":
        st.success("Your AI workflow finished successfully.")

        if final_output and str(final_output).strip():
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="result-heading">📄 Final Report</div>
                    <div class="result-subheading">
                        Generated by your NEXUS AI agent workflow
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                cleaned_output = clean_markdown(str(final_output))
                st.markdown(cleaned_output)

            report_task = str(get_result_value(result, "task", "")).strip()
            cleaned_output = clean_markdown(str(final_output))
            download_content = export_markdown(
                title="NEXUS AI — Generated Report",
                content=f"**Task:** {report_task}\\n\\n{cleaned_output}",
                include_timestamp=True,
            )

            st.download_button(
                label="📥 Download Report (.md)",
                data=download_content,
                file_name=make_download_name(
                    str(get_result_value(result, "task", "ai-report"))
                ),
                mime="text/markdown",
                use_container_width=True,
            )

        else:
            st.warning(
                "The workflow returned success, but no final report "
                "was provided. Check the orchestrator's final_output."
            )

    else:
        st.error("The AI workflow failed.")

        if error_message:
            st.warning(str(error_message))

        st.caption(
            "The orchestrator did not produce a successful final report. "
            "Review the technical logs for the underlying cause."
        )

    # --------------------------------------------------------
    # INDIVIDUAL AGENT OUTPUTS
    # --------------------------------------------------------

    if agent_results:
        st.write("")
        st.markdown("### 🧩 Agent execution details")

        for index, agent in enumerate(agent_results, start=1):
            agent_name = get_agent_name(agent)
            agent_content = get_agent_content(agent)

            with st.expander(
                f"{index:02d} · {agent_name}",
                expanded=False,
            ):
                if agent_content.strip():
                    st.markdown(agent_content)
                else:
                    st.caption("This agent did not return visible content.")

    # --------------------------------------------------------
    # WORKFLOW SUMMARY
    # --------------------------------------------------------

    with st.expander("📋 Workflow summary", expanded=False):
        st.write(
            "**Original task:**",
            get_result_value(result, "task", "Not available"),
        )

        st.write("**Status:**", result_status.capitalize())

        st.write("**Web search:**", (
            "Enabled"
            if st.session_state.last_search_enabled
            else "Disabled"
        ))

        st.write("**Recorded agent outputs:**", len(agent_results))


# ============================================================
# AGENT OVERVIEW
# ============================================================

st.divider()

st.markdown(
    """
    <div class="section-label">THE TEAM</div>
    <div class="section-title">Meet your AI agents</div>
    <div class="section-description">
        Four specialized agents cooperate to turn your instructions
        into a useful final output.
    </div>
    """,
    unsafe_allow_html=True,
)

agent_col1, agent_col2, agent_col3, agent_col4 = st.columns(4)

with agent_col1:
    render_agent_card(
        "🧭",
        "Planner",
        "Analyzes the task and creates an execution plan.",
    )

with agent_col2:
    render_agent_card(
        "🔎",
        "Researcher",
        "Collects useful research and organizes findings.",
    )

with agent_col3:
    render_agent_card(
        "✍️",
        "Content",
        "Transforms the task and research into final content.",
    )

with agent_col4:
    render_agent_card(
        "🛡️",
        "Reviewer",
        "Checks the generated content for quality and completeness.",
    )


# ============================================================
# FOOTER
# ============================================================

st.write("")
st.divider()

footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.caption("🤖 NEXUS AI · Multi-Agent Workspace")

with footer_col2:
    st.markdown(
        """
        <div style="text-align:right;color:#6b7280;font-size:11px;">
            Built with Python · Streamlit · Groq
        </div>
        """,
        unsafe_allow_html=True,
    )