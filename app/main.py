import streamlit as st
import os
from pathlib import Path
import traceback

# Import services
from app.services.github_service import get_github_issue
from app.services.repository_service import clone_repository
from app.services.pdf_service import generate_plan_pdf
from app.agents.planner_agent import execute_planner, Plan

# Set page config
st.set_page_config(
    page_title="RepoFix Agent - Plan Generation Workspace",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Premium Design aesthetics
st.markdown("""
<style>
    /* Main Layout Styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    /* Text input border override */
    .stTextInput>div>div>input {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Button Styling */
    div.stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3), 0 4px 6px -2px rgba(37, 99, 235, 0.15) !important;
    }
    
    /* Custom Download Button Styling */
    .download-btn-container {
        margin-top: 15px;
    }
    
    /* Cards styling */
    .plan-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        display: inline-block;
        margin-right: 10px;
    }
    .badge-modify {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-new {
        background-color: rgba(74, 222, 128, 0.15);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }
    .badge-delete {
        background-color: rgba(248, 113, 113, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .file-row {
        background-color: #0f172a;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        margin-bottom: 10px;
    }
    .github-badge {
        background-color: #24292f;
        border: 1px solid #30363d;
        color: #c9d1d9;
        padding: 4px 8px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Dashboard Header
st.title("⚙️ RepoFix Agent Workspace")
st.markdown("Automate codebase analysis, issue planning, and testing verification directly from Github issues.")
st.write("---")

# Layout: 2 Columns
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("🎯 Issue Configuration")
    st.markdown("Enter details about the repository and the issue you'd like the planner agent to solve.")
    
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repository.git",
        help="Specify the target public GitHub repository URL."
    )
    
    issue_number_str = st.text_input(
        "GitHub Issue Number",
        placeholder="e.g. 42",
        help="Specify the issue number to solve."
    )
    
    submit_button = st.button("Generate Solution Plan")

# Initialize Session State to store generated plan and details
if "plan" not in st.session_state:
    st.session_state.plan = None
    st.session_state.cloned_path = None
    st.session_state.repo_url = None
    st.session_state.issue_num = None
    st.session_state.issue_details = None
    st.session_state.pdf_path = None

with col2:
    st.header("📋 Implementation & Verification Plan")
    
    if submit_button:
        if not repo_url.strip():
            st.error("Please enter a valid GitHub repository URL.")
        elif not issue_number_str.strip():
            st.error("Please enter a valid GitHub Issue Number.")
        else:
            try:
                issue_number = int(issue_number_str.strip())
            except ValueError:
                st.error("Issue Number must be a valid integer.")
                issue_number = None
                
            if issue_number is not None:
                # 1. Fetch GitHub issue details
                status_placeholder = st.empty()
                try:
                    status_placeholder.info(f"🔍 Fetching details for Issue #{issue_number} from GitHub...")
                    issue_details = get_github_issue(repo_url, issue_number)
                    st.session_state.issue_details = issue_details
                    st.session_state.repo_url = repo_url
                    st.session_state.issue_num = issue_number
                    
                    # 2. Clone repository
                    status_placeholder.info("📥 Cloning repository to secure workspace folder...")
                    cloned_path = clone_repository(repo_url)
                    st.session_state.cloned_path = cloned_path
                    
                    # 3. Run planner
                    status_placeholder.info("🧠 Running LangGraph planner agent on cloned codebase...")
                    # Pass full issue details to planner agent
                    full_issue_content = f"Issue Title: {issue_details['title']}\nDescription:\n{issue_details['body']}"
                    plan = execute_planner(cloned_path, full_issue_content)
                    st.session_state.plan = plan
                    
                    # 4. Generate PDF
                    status_placeholder.info("📄 Compiling report and generating PDF...")
                    pdf_filename = f"plan_{int(os.path.getmtime(cloned_path))}.pdf"
                    
                    # Create a local pdf directory to store output files
                    workspace_root = Path(__file__).resolve().parent.parent
                    pdf_dir = workspace_root / "pdf_outputs"
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    pdf_path = pdf_dir / pdf_filename
                    
                    generate_plan_pdf(
                        plan=plan,
                        repo_url=repo_url,
                        issue_desc=full_issue_content,
                        cloned_path=cloned_path,
                        output_path=str(pdf_path)
                    )
                    st.session_state.pdf_path = str(pdf_path)
                    
                    status_placeholder.success("✨ Planning session completed successfully!")
                    
                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"An error occurred during planning execution:")
                    st.code(traceback.format_exc(), language="python")
                
    # Display the plan if it exists in state
    if st.session_state.plan and st.session_state.issue_details:
        plan = st.session_state.plan
        issue = st.session_state.issue_details
        
        # Display Issue Header
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #ffffff;">#{st.session_state.issue_num}: {issue['title']}</h4>
                <div style="margin-top: 8px; display: flex; gap: 10px; align-items: center;">
                    <span class="github-badge">User: {issue['user']}</span>
                    <span class="github-badge" style="color: {'#4ade80' if issue['state'] == 'open' else '#f87171'}">State: {issue['state'].upper()}</span>
                    <a href="{issue['html_url']}" target="_blank" style="color: #60a5fa; text-decoration: none; font-size: 0.9rem;">🔗 View on GitHub</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Action Bar: Download Button
        pdf_path = Path(st.session_state.pdf_path)
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                
            st.download_button(
                label="📥 Download Plan PDF",
                data=pdf_bytes,
                file_name=pdf_path.name,
                mime="application/pdf"
            )
            
        # UI Tabs to browse the plan
        tab_overview, tab_changes, tab_tasks, tab_tests, tab_issue = st.tabs([
            "🔍 Overview", 
            "📂 File Changes", 
            "✅ Task Checklist", 
            "🧪 Verification",
            "💬 Issue Description"
        ])
        
        with tab_overview:
            st.subheader("Overview & Objectives")
            st.markdown(plan.overview)
            
            st.markdown("---")
            st.markdown(f"**Workspace Location:** `{st.session_state.cloned_path}`")
            
        with tab_changes:
            st.subheader("Proposed File Changes")
            if not plan.changes:
                st.info("No file changes specified.")
            else:
                for change in plan.changes:
                    change_type = change.model # "Modify", "New", "Delete"
                    if change_type == "New":
                        badge_html = '<span class="badge badge-new">New</span>'
                    elif change_type == "Delete":
                        badge_html = '<span class="badge badge-delete">Delete</span>'
                    else:
                        badge_html = '<span class="badge badge-modify">Modify</span>'
                        
                    st.markdown(
                        f"""
                        <div class="file-row">
                            <div style="margin-bottom: 8px;">
                                {badge_html} <b>{change.file_path}</b>
                            </div>
                            <div style="color: #94a3b8; font-size: 0.9rem;">
                                {change.description}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
        with tab_tasks:
            st.subheader("Implementation Task Checklist")
            st.markdown("Track your implementation progress step-by-step:")
            for idx, task_text in enumerate(plan.task):
                # Interactive checkboxes for user tracking
                st.checkbox(task_text, key=f"task_check_{idx}")
                
        with tab_tests:
            st.subheader("Verification & Testing Plan")
            st.markdown(plan.tests)
            
        with tab_issue:
            st.subheader("Raw GitHub Issue Description")
            st.markdown(issue['body'])
            
    else:
        # Welcome Card for empty state
        st.markdown(
            """
            <div style="background-color: #1e293b; border: 1px dashed #475569; border-radius: 12px; padding: 40px; text-align: center; margin-top: 20px;">
                <h3 style="margin-top: 0; color: #94a3b8;">No Active Plan Generated</h3>
                <p style="color: #64748b;">Configure the settings on the left and click <b>Generate Solution Plan</b> to run the planning agent.</p>
                <div style="margin-top: 20px; font-size: 1.2rem; color: #475569;">🤖 🔀 📄</div>
            </div>
            """,
            unsafe_allow_html=True
        )
