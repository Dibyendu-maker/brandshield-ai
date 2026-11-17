import pandas as pd
import streamlit as st

from frontend.api_client import APIClient
from frontend.components.styles import (
    apply_enterprise_theme,
    render_score_badge,
    render_severity_pill,
    render_status_pill,
)

st.set_page_config(
    page_title="BrandShield AI | Enterprise Brand Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_enterprise_theme()

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "client" not in st.session_state:
    st.session_state.client = APIClient()
if "active_submission_id" not in st.session_state:
    st.session_state.active_submission_id = None


def set_active_submission(sub_id: int | None):
    """Synchronizes active_submission_id with st.session_state and st.query_params."""
    st.session_state.active_submission_id = sub_id
    if sub_id is not None:
        st.query_params["sub_id"] = str(sub_id)
    else:
        st.query_params.pop("sub_id", None)


# 1. Backend Connectivity & Health Check
health_result = st.session_state.client.check_health()
backend_online = health_result.get("healthy", False)

if not backend_online:
    st.error("⚠️ **BrandShield AI Backend Disconnected**")
    st.markdown(
        """
        The Streamlit frontend cannot establish a connection with the backend API service at `http://127.0.0.1:8000`.

        **To launch the backend API service, open a terminal and run:**
        ```powershell
        uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
        ```
        """
    )
    col_retry, _ = st.columns([1, 4])
    with col_retry:
        if st.button("🔄 Retry Connection", use_container_width=True):
            st.rerun()

    with st.sidebar:
        st.markdown(
            """
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
                <span style="font-size: 11px; color: #FCA5A5; font-weight: 700;">● BACKEND OFFLINE</span>
                <div style="font-size: 12px; color: #F8FAFC; margin-top: 4px;">Service unreachable.</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    st.stop()

# Auto-login to default demo user (creator) if not authenticated
if not st.session_state.token:
    try:
        login_res = st.session_state.client.login(
            "creator@novatech.com", "Password123!"
        )
        st.session_state.token = login_res["access_token"]
        st.session_state.current_user = login_res["user"]
        st.session_state.client = APIClient(token=st.session_state.token)
    except Exception as e:
        st.sidebar.warning(f"Auto-login failed: {e}")

# Restore and validate active_submission_id from st.query_params if present
query_sub_id = st.query_params.get("sub_id")
if query_sub_id:
    if query_sub_id.isdigit():
        target_id = int(query_sub_id)
        if st.session_state.active_submission_id != target_id:
            try:
                validated = st.session_state.client.get_submission(target_id)
                st.session_state.active_submission_id = validated["id"]
            except Exception:
                # Inaccessible, deleted, or belongs to another organization
                set_active_submission(None)
    else:
        st.query_params.pop("sub_id", None)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #4F46E5, #7C3AED); width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🛡️</div>
            <div>
                <h2 style="font-size: 18px; font-weight: 800; margin: 0; color: #FFFFFF; letter-spacing: -0.02em;">BrandShield AI</h2>
                <span style="font-size: 11px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Governance Cloud</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Active Organization Card
    st.markdown(
        """
        <div style="background: #1E293B; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; border: 1px solid #334155;">
            <span style="font-size: 10px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Workspace</span>
            <div style="font-size: 14px; font-weight: 700; color: #F8FAFC;">NovaTech Global</div>
            <div style="font-size: 11px; color: #10B981;">● Backend Online (Tenant Isolated)</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Demo Persona Switcher (For Judges)
    st.markdown(
        "<p style='font-size: 12px; font-weight: 700; color: #94A3B8; margin-bottom: 6px;'>🎭 ROLE PERSONA SWITCHER</p>",
        unsafe_allow_html=True,
    )
    current_role = (
        st.session_state.current_user["role"]
        if st.session_state.current_user
        else "creator"
    )
    persona = st.selectbox(
        "Current Persona",
        options=["Creator (Alex)", "Reviewer (Sarah)", "Administrator (Admin)"],
        index=0
        if current_role == "creator"
        else (1 if current_role == "reviewer" else 2),
        label_visibility="collapsed",
    )

    if st.button("Switch Persona", use_container_width=True):
        email_map = {
            "Creator (Alex)": "creator@novatech.com",
            "Reviewer (Sarah)": "reviewer@novatech.com",
            "Administrator (Admin)": "admin@novatech.com",
        }
        selected_email = email_map[persona]
        try:
            res = st.session_state.client.login(selected_email, "Password123!")
            st.session_state.token = res["access_token"]
            st.session_state.current_user = res["user"]
            st.session_state.client = APIClient(token=st.session_state.token)
            st.success(
                f"Switched to {res['user']['full_name']} ({res['user']['role'].upper()})"
            )
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

    if st.session_state.current_user:
        u = st.session_state.current_user
        st.markdown(
            f"""
            <div style="font-size: 11px; color: #94A3B8; margin-top: 4px; margin-bottom: 20px;">
                Logged in: <strong style="color: #F1F5F9;">{u["full_name"]}</strong><br/>
                Role: <span style="color: #A78BFA; font-weight: 700;">{u["role"].upper()}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Navigation Menu
    menu_selection = st.radio(
        "Navigation",
        [
            "📊 Executive Dashboard",
            "✍️ Content Submission",
            "🔍 Compliance Inspector",
            "🛠️ AI Correction Studio",
            "⚖️ Human Review Workflow",
            "📜 Revision Audit Trail",
            "📚 Brand Guidelines & RAG Vault",
            "📋 Approved Specs & Terminology",
            "📈 Governance Analytics",
            "⚙️ System Disclosures",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<p style='font-size: 11px; color: #64748B;'>BrandShield AI v1.0.0<br/>CodeZen India 2026 Round 2</p>",
        unsafe_allow_html=True,
    )


# Helper function to load demo scenario
def load_canonical_demo():
    try:
        title = "NovaBook Pro Enterprise Q4 Launch Copy"
        content = (
            "Introducing NovaBook Pro! The world's number one laptop with 24 hours of "
            "battery life and a 5-year warranty. Guaranteed success for every user!"
        )
        sub = st.session_state.client.submit_content(
            title=title, content_type="text", original_text=content
        )
        sub_id = sub["id"]
        set_active_submission(sub_id)
        # Trigger compliance audit
        st.session_state.client.run_compliance_audit(sub_id)
        st.success("✅ NovaTech Demonstration Scenario loaded and audited!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load demo scenario: {e}")


# ==================== PAGE: EXECUTIVE DASHBOARD ====================
if menu_selection == "📊 Executive Dashboard":
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <div>
                <span class="brand-badge">Command Center</span>
                <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Brand Compliance Dashboard</h1>
                <p style="color: #94A3B8; margin: 0; font-size: 14px;">Real-time brand compliance monitoring, risk mitigation, and content approvals.</p>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Demo Launch Banner
    col_banner, col_btn = st.columns([3, 1])
    with col_banner:
        st.info(
            "💡 **Hackathon Evaluator Quickstart:** Click the button to the right to run the end-to-end NovaTech demonstration scenario (specs, forbidden phrases, superiority claims, and intent-preserving corrections)."
        )
    with col_btn:
        if st.button("🚀 Load NovaTech Demo", use_container_width=True):
            load_canonical_demo()

    try:
        analytics = st.session_state.client.get_analytics()
        submissions = st.session_state.client.list_submissions()

        # Top Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f"""
                <div class="brand-card">
                    <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Submissions</span>
                    <div style="font-size: 32px; font-weight: 800; color: #FFFFFF; margin-top: 4px;">{analytics["total_submissions"]}</div>
                    <span style="font-size: 11px; color: #38BDF8;">Across organization</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with m2:
            avg_score = analytics["average_compliance_score"]
            color = (
                "#10B981"
                if avg_score >= 80
                else ("#F59E0B" if avg_score >= 60 else "#EF4444")
            )
            st.markdown(
                f"""
                <div class="brand-card">
                    <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Avg Compliance Score</span>
                    <div style="font-size: 32px; font-weight: 800; color: {color}; margin-top: 4px;">{avg_score}%</div>
                    <span style="font-size: 11px; color: #94A3B8;">Objective weighted score</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"""
                <div class="brand-card">
                    <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Approval Rate</span>
                    <div style="font-size: 32px; font-weight: 800; color: #A78BFA; margin-top: 4px;">{analytics["approval_rate"]}%</div>
                    <span style="font-size: 11px; color: #94A3B8;">Human reviewer governed</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with m4:
            total_violations = sum(analytics["violations_by_category"].values())
            st.markdown(
                f"""
                <div class="brand-card">
                    <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Detected Violations</span>
                    <div style="font-size: 32px; font-weight: 800; color: #F87171; margin-top: 4px;">{total_violations}</div>
                    <span style="font-size: 11px; color: #EF4444;">Prevented pre-publication</span>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "<h3 style='font-size: 18px; font-weight: 700; color: #FFFFFF; margin-top: 24px; margin-bottom: 12px;'>Recent Content Submissions</h3>",
            unsafe_allow_html=True,
        )
        if not submissions:
            st.info(
                "No submissions found. Submit content using the sidebar or load the demo scenario."
            )
        else:
            table_data = []
            for s in submissions:
                table_data.append(
                    {
                        "ID": s["id"],
                        "Title": s["title"],
                        "Type": s["content_type"].upper(),
                        "Score": f"{s['compliance_score']}%",
                        "Status": s["current_status"].replace("_", " ").title(),
                        "Creator": s["creator_name"] or "Unknown",
                        "Created": s["created_at"][:10],
                    }
                )
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Quick Selector
            sub_options = {
                f"#{s['id']} — {s['title']} ({s['current_status'].upper()})": s["id"]
                for s in submissions
            }
            selected_sub = st.selectbox(
                "Inspect Submission", options=list(sub_options.keys())
            )
            if st.button("Open in Compliance Inspector"):
                set_active_submission(sub_options[selected_sub])
                st.info(
                    f"Loaded submission #{st.session_state.active_submission_id}. Switch to '🔍 Compliance Inspector' in the navigation menu."
                )

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

# ==================== PAGE: CONTENT SUBMISSION ====================
elif menu_selection == "✍️ Content Submission":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Content Ingestion Pipeline</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Submit Content for Governance Audit</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Upload text, documents, or marketing images for automated pre-publication compliance auditing.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    tab_text, tab_file, tab_demo = st.tabs(
        ["📝 Direct Text Input", "📁 Document / Image Upload", "⚡ Quick Demo Scenario"]
    )

    with tab_text:
        with st.form("text_submission_form"):
            title = st.text_input(
                "Campaign / Content Title",
                placeholder="e.g. NovaBook Pro Enterprise Q4 Launch Copy",
            )
            raw_text = st.text_area(
                "Content Body (Markdown or Plain Text)",
                placeholder="Paste marketing copy, press releases, product descriptions, or social ads...",
                height=180,
            )
            submitted = st.form_submit_button("Submit & Run Compliance Audit")

            if submitted:
                if not title.strip() or not raw_text.strip():
                    st.error("Please provide both a title and content body.")
                else:
                    with st.spinner(
                        "Ingesting content and executing compliance audit..."
                    ):
                        try:
                            sub = st.session_state.client.submit_content(
                                title=title, content_type="text", original_text=raw_text
                            )
                            set_active_submission(sub["id"])
                            # Run audit
                            st.session_state.client.run_compliance_audit(sub["id"])
                            st.success(
                                f"Submission #{sub['id']} created and audited successfully!"
                            )
                        except Exception as e:
                            st.error(f"Submission error: {e}")

    with tab_file:
        with st.form("file_submission_form"):
            file_title = st.text_input(
                "Campaign / Content Title", placeholder="e.g. Brand Campaign Media Kit"
            )
            uploaded_file = st.file_uploader(
                "Upload Document or Image",
                type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg", "webp"],
                help="Supported documents: PDF, DOCX, TXT, MD. Images: PNG, JPG, WEBP (evaluated for color palette, contrast & composition).",
            )
            file_submitted = st.form_submit_button("Upload & Audit")

            if file_submitted:
                if not file_title.strip() or not uploaded_file:
                    st.error("Please provide a title and select a file.")
                else:
                    with st.spinner(
                        "Extracting content and running multimodal inspection..."
                    ):
                        try:
                            sub = st.session_state.client.submit_content(
                                title=file_title,
                                content_type="document",
                                file_bytes=uploaded_file.getvalue(),
                                filename=uploaded_file.name,
                            )
                            set_active_submission(sub["id"])
                            st.session_state.client.run_compliance_audit(sub["id"])
                            st.success(
                                f"File uploaded and audited as Submission #{sub['id']}!"
                            )
                        except Exception as e:
                            st.error(f"Upload error: {e}")

    with tab_demo:
        st.markdown("""
            ### Canonical Hackathon Evaluation Scenario (NovaTech)
            **Submitted Flawed Ad:**
            > *"Introducing NovaBook Pro! The world's number one laptop with 24 hours of battery life and a 5-year warranty. Guaranteed success for every user!"*
        """)
        if st.button("🚀 Load and Audit Canonical Demo Copy", use_container_width=True):
            load_canonical_demo()

# ==================== PAGE: COMPLIANCE INSPECTOR ====================
elif menu_selection == "🔍 Compliance Inspector":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Explainable Audit Engine</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Compliance Audit & Evidence Inspector</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Evidence-first brand intelligence connecting every violation to approved specifications and source documents.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Submission selector
    submissions = st.session_state.client.list_submissions()
    if not submissions:
        st.warning("No submissions found. Submit content first.")
    else:
        sub_options = {
            f"#{s['id']} — {s['title']} ({s['current_status'].upper()})": s["id"]
            for s in submissions
        }
        current_idx = 0
        if st.session_state.active_submission_id:
            keys = list(sub_options.values())
            if st.session_state.active_submission_id in keys:
                current_idx = keys.index(st.session_state.active_submission_id)

        selected_key = st.selectbox(
            "Select Submission to Inspect",
            options=list(sub_options.keys()),
            index=current_idx,
        )
        selected_id = sub_options[selected_key]
        set_active_submission(selected_id)

        # Fetch submission details
        sub = st.session_state.client.get_submission(selected_id)

        # Header metrics
        score = sub["compliance_score"]
        col_score, col_status = st.columns([1, 2])
        with col_score:
            st.markdown(render_score_badge(score), unsafe_allow_html=True)
        with col_status:
            st.markdown(
                f"""
                <div class="brand-card">
                    <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Submission Overview</span>
                    <div style="margin-top: 6px; font-size: 14px;">
                        <strong>Title:</strong> {sub["title"]}<br/>
                        <strong>Status:</strong> {render_status_pill(sub["current_status"])}<br/>
                        <strong>Creator:</strong> {sub["creator_name"] or "Unknown"}<br/>
                        <strong>Total Findings:</strong> {len(sub["findings"])}
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        # Submitted Content Viewer
        st.markdown(
            "<h4 style='color: #FFFFFF; margin-top: 16px;'>Submitted Content</h4>",
            unsafe_allow_html=True,
        )
        latest_rev = (
            sub["revisions"][-1]["content"]
            if sub["revisions"]
            else sub["original_text"]
        )
        st.info(latest_rev)

        # Re-run audit button
        if st.button("🔄 Re-Run Compliance Audit"):
            with st.spinner("Analyzing against latest brand knowledge..."):
                st.session_state.client.run_compliance_audit(selected_id)
                st.success("Audit refreshed!")
                st.rerun()

        # Detailed Findings Accordion
        st.markdown(
            "<h3 style='color: #FFFFFF; margin-top: 24px; font-weight: 800;'>Detected Violations & Evidence</h3>",
            unsafe_allow_html=True,
        )
        findings = sub["findings"]

        if not findings:
            st.success(
                "🎉 No compliance violations detected! Content meets all approved guidelines."
            )
        else:
            for idx, f in enumerate(findings):
                severity_html = render_severity_pill(f["severity"])
                with st.expander(
                    f'Finding #{idx + 1} [{f["severity"]}] {f["category"].upper()}: "{f["problematic_snippet"]}"',
                    expanded=True,
                ):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(
                            f"""
                            <strong>Problematic Content:</strong> <span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 2px 6px; border-radius: 4px;">{f["problematic_snippet"]}</span><br/>
                            <div style="margin-top: 8px;"><strong>Explanation:</strong> {f["explanation"]}</div>
                            <div style="margin-top: 8px; color: #34D399;"><strong>Recommended Correction:</strong> {f["recommended_correction"]}</div>
                        """,
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f"""
                            <div style="background: #1E293B; border-radius: 8px; padding: 10px; font-size: 12px; border: 1px solid #334155;">
                                <strong style="color: #A78BFA;">Ground Truth Evidence:</strong><br/>
                                <span style="color: #94A3B8;">Source Fact:</span><br/>
                                <span style="color: #F8FAFC; font-weight: 600;">{f["approved_source_fact"] or "Brand Governance Standard"}</span><br/><br/>
                                <span style="color: #94A3B8;">Guideline Reference:</span><br/>
                                <span style="color: #38BDF8;">{f["brand_guideline_ref"] or "General Brand Policy"}</span><br/><br/>
                                <span style="color: #94A3B8;">Confidence:</span> <strong>{int(f["confidence"] * 100)}%</strong>
                            </div>
                        """,
                            unsafe_allow_html=True,
                        )

# ==================== PAGE: AI CORRECTION STUDIO ====================
elif menu_selection == "🛠️ AI Correction Studio":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Intent-Preserving Correction</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">AI Correction Studio</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Non-destructive suggestions preserving creator's promotional voice while strictly enforcing approved facts.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    submissions = st.session_state.client.list_submissions()
    if not submissions:
        st.warning("No submissions found.")
    else:
        sub_options = {f"#{s['id']} — {s['title']}": s["id"] for s in submissions}
        current_idx = 0
        if st.session_state.active_submission_id:
            keys = list(sub_options.values())
            if st.session_state.active_submission_id in keys:
                current_idx = keys.index(st.session_state.active_submission_id)

        selected_key = st.selectbox(
            "Select Submission", options=list(sub_options.keys()), index=current_idx
        )
        sub_id = sub_options[selected_key]
        set_active_submission(sub_id)
        sub = st.session_state.client.get_submission(sub_id)

        # Get diff
        diff_data = st.session_state.client.get_diff(sub_id)
        original_text = sub["original_text"] or ""
        latest_rev = (
            sub["revisions"][-1]["content"] if sub["revisions"] else original_text
        )

        # Generate suggested version via compliance audit response
        audit_res = st.session_state.client.run_compliance_audit(sub_id)
        suggested_copy = audit_res["suggested_revision"]

        st.markdown(
            "<h3 style='color: #FFFFFF; margin-top: 16px;'>Interactive Side-by-Side Comparison</h3>",
            unsafe_allow_html=True,
        )
        col_orig, col_sugg = st.columns(2)
        with col_orig:
            st.markdown(
                """
                <div style="background: #111827; padding: 14px; border-radius: 8px; border: 1px solid #1F2937;">
                    <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #F87171;">Original Submitted Copy</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
            st.error(original_text)

        with col_sugg:
            st.markdown(
                """
                <div style="background: #111827; padding: 14px; border-radius: 8px; border: 1px solid #1F2937;">
                    <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #34D399;">BrandShield AI Suggested Compliant Copy</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
            st.success(suggested_copy)

        # Diff View
        st.markdown(
            "<h4 style='color: #FFFFFF; margin-top: 16px;'>Word-Level Diff Analysis</h4>",
            unsafe_allow_html=True,
        )
        diff_chunks = diff_data["diff_chunks"]
        diff_html = ""
        for chunk in diff_chunks:
            if chunk["type"] == "equal":
                diff_html += f"<span>{chunk['text']} </span>"
            elif chunk["type"] == "deleted":
                diff_html += f"<span class='diff-deleted'>{chunk['text']}</span> "
            elif chunk["type"] == "inserted":
                diff_html += f"<span class='diff-inserted'>{chunk['text']}</span> "

        st.markdown(
            f"""
            <div style="background: #0F172A; padding: 16px; border-radius: 8px; border: 1px solid #1E293B; line-height: 1.8; font-size: 15px;">
                {diff_html}
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Interactive Editor to Apply or Modify
        st.markdown(
            "<h3 style='color: #FFFFFF; margin-top: 24px;'>Apply Suggestion or Edit Directly</h3>",
            unsafe_allow_html=True,
        )
        with st.form("revision_form"):
            edited_content = st.text_area(
                "Final Content for Submission (Pre-populated with AI Suggestion)",
                value=suggested_copy,
                height=140,
            )
            changes_notes = st.text_input(
                "Summary of Changes",
                value="Applied AI compliant specifications and tone corrections.",
            )
            save_btn = st.form_submit_button("💾 Save as New Revision")

            if save_btn:
                try:
                    rev = st.session_state.client.save_revision(
                        submission_id=sub_id,
                        content=edited_content,
                        version_label="User Edit",
                        changes_summary=changes_notes,
                    )
                    # Re-audit
                    st.session_state.client.run_compliance_audit(sub_id)
                    st.success(
                        f"Revision #{rev['revision_number']} saved! Compliance score refreshed."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving revision: {e}")

# ==================== PAGE: HUMAN REVIEW WORKFLOW ====================
elif menu_selection == "⚖️ Human Review Workflow":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Human-in-the-Loop Governance</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Review & Approval Workflow</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Human reviewers retain final authority. Manage approvals, change requests, and collaborative audit discussions.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    submissions = st.session_state.client.list_submissions()
    if not submissions:
        st.warning("No submissions found.")
    else:
        sub_options = {
            f"#{s['id']} — {s['title']} ({s['current_status'].upper()})": s["id"]
            for s in submissions
        }
        current_idx = 0
        if st.session_state.active_submission_id:
            keys = list(sub_options.values())
            if st.session_state.active_submission_id in keys:
                current_idx = keys.index(st.session_state.active_submission_id)

        selected_key = st.selectbox(
            "Select Submission for Review",
            options=list(sub_options.keys()),
            index=current_idx,
        )
        sub_id = sub_options[selected_key]
        set_active_submission(sub_id)
        sub = st.session_state.client.get_submission(sub_id)

        # Overview Card
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Compliance Score", f"{sub['compliance_score']}%")
        with c2:
            st.metric("Current Status", sub["current_status"].replace("_", " ").title())
        with c3:
            st.metric("Assigned Reviewer", sub["reviewer_name"] or "Unassigned")

        st.markdown("---")

        # Review Actions (Restricted to Reviewers & Admins)
        current_user = st.session_state.current_user
        user_role = current_user["role"] if current_user else "creator"

        st.markdown(
            "<h3 style='color: #FFFFFF;'>Workflow Actions</h3>", unsafe_allow_html=True
        )
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)

        with col_act1:
            if st.button(
                "📤 Submit for Review",
                disabled=(
                    sub["current_status"] in ["submitted", "under_review", "approved"]
                ),
            ):
                st.session_state.client.update_status(
                    sub_id, "submitted", "Author submitted draft for compliance review."
                )
                st.success("Draft submitted for review!")
                st.rerun()

        with col_act2:
            if st.button(
                "🔄 Request Changes",
                disabled=(
                    user_role not in ["reviewer", "admin"]
                    or sub["current_status"] in ["approved", "rejected"]
                ),
            ):
                st.session_state.client.update_status(
                    sub_id,
                    "changes_requested",
                    "Brand reviewer requested changes to meet compliance guidelines.",
                )
                st.warning("Changes requested from creator.")
                st.rerun()

        with col_act3:
            if st.button(
                "✅ Approve for Publication",
                disabled=(
                    user_role not in ["reviewer", "admin"]
                    or sub["current_status"] == "approved"
                ),
            ):
                st.session_state.client.update_status(
                    sub_id,
                    "approved",
                    "Approved by authorized brand reviewer for enterprise release.",
                )
                st.success("Submission APPROVED!")
                st.rerun()

        with col_act4:
            if st.button(
                "❌ Reject Submission",
                disabled=(
                    user_role not in ["reviewer", "admin"]
                    or sub["current_status"] == "rejected"
                ),
            ):
                st.session_state.client.update_status(
                    sub_id,
                    "rejected",
                    "Rejected due to critical brand guideline conflicts.",
                )
                st.error("Submission rejected.")
                st.rerun()

        if user_role not in ["reviewer", "admin"]:
            st.caption(
                "ℹ️ *Note: 'Approve' and 'Reject' actions require Reviewer or Administrator permissions. Switch to 'Reviewer (Sarah)' in the sidebar to approve.*"
            )

        # Collaborative Review Comment Thread
        st.markdown(
            "<h3 style='color: #FFFFFF; margin-top: 24px;'>Review Comments & Decision Audit Trail</h3>",
            unsafe_allow_html=True,
        )
        comments = sub["comments"]
        if not comments:
            st.info("No comments yet.")
        else:
            for c in comments:
                st.markdown(
                    f"""
                    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong style="color: #A78BFA;">{c["user_name"] or "Reviewer"}</strong>
                            <span style="font-size: 11px; color: #64748B;">{c["created_at"][:19].replace("T", " ")}</span>
                        </div>
                        <p style="margin: 6px 0 0 0; color: #E2E8F0; font-size: 14px;">{c["comment"]}</p>
                        {f'<span style="font-size: 11px; color: #38BDF8;">Transition: {c["status_transition"]}</span>' if c["status_transition"] else ""}
                    </div>
                """,
                    unsafe_allow_html=True,
                )

        with st.form("new_comment_form"):
            new_comment = st.text_input(
                "Add a Review Note or Instruction",
                placeholder="e.g. Please verify battery hours against Section 3.2 of the spec sheet...",
            )
            post_btn = st.form_submit_button("Post Comment")
            if post_btn and new_comment.strip():
                st.session_state.client.add_comment(sub_id, new_comment)
                st.success("Comment added!")
                st.rerun()

# ==================== PAGE: REVISION AUDIT TRAIL ====================
elif menu_selection == "📜 Revision Audit Trail":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Version Governance</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Revision History & Content Lineage</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Complete immutable audit log tracking every revision, author attribution, and modification.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    submissions = st.session_state.client.list_submissions()
    if not submissions:
        st.warning("No submissions found.")
    else:
        sub_options = {f"#{s['id']} — {s['title']}": s["id"] for s in submissions}
        current_idx = 0
        if st.session_state.active_submission_id:
            keys = list(sub_options.values())
            if st.session_state.active_submission_id in keys:
                current_idx = keys.index(st.session_state.active_submission_id)

        selected_key = st.selectbox(
            "Select Submission", options=list(sub_options.keys()), index=current_idx
        )
        sub_id = sub_options[selected_key]
        sub = st.session_state.client.get_submission(sub_id)

        revisions = sub["revisions"]
        st.markdown(
            f"<h4 style='color: #FFFFFF;'>Revisions Recorded: {len(revisions)}</h4>",
            unsafe_allow_html=True,
        )

        for rev in revisions:
            st.markdown(
                f"""
                <div class="brand-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span class="badge-medium">Revision #{rev["revision_number"]}</span>
                            <strong style="color: #FFFFFF; font-size: 15px; margin-left: 8px;">{rev["version_label"]}</strong>
                        </div>
                        <span style="font-size: 12px; color: #64748B;">{rev["created_at"][:19].replace("T", " ")}</span>
                    </div>
                    <div style="background: #0B132B; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 13px; color: #E2E8F0; margin-bottom: 8px;">
                        {rev["content"]}
                    </div>
                    <span style="font-size: 12px; color: #94A3B8;"><strong>Changes Summary:</strong> {rev["changes_summary"] or "None provided"}</span>
                </div>
            """,
                unsafe_allow_html=True,
            )

# ==================== PAGE: BRAND GUIDELINES & RAG VAULT ====================
elif menu_selection == "📚 Brand Guidelines & RAG Vault":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Brand Knowledge Engine</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Brand Guidelines & Document RAG Vault</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">ChromaDB vector store indexed with Sentence Transformers (all-MiniLM-L6-v2) for semantic retrieval.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    tab_overview, tab_upload = st.tabs(
        ["📖 Active Brand Guidelines", "📤 Upload Guideline Document"]
    )

    with tab_overview:
        guideline = st.session_state.client.get_guidelines()
        st.markdown(
            f"""
            <div class="brand-card">
                <span class="brand-badge">Brand Identity Profile</span>
                <h3 style="color: #FFFFFF; margin: 6px 0;">{guideline["brand_name"]}</h3>
                <p style="color: #94A3B8; font-size: 14px;">{guideline["brand_description"] or "No description configured."}</p>
                <div style="margin-top: 12px;">
                    <strong style="color: #A78BFA;">Mission & Values:</strong><br/>
                    <span style="color: #E2E8F0; font-size: 13px;">{guideline["mission_values"] or "None"}</span>
                </div>
                <div style="margin-top: 12px;">
                    <strong style="color: #38BDF8;">Approved Tone of Voice:</strong><br/>
                    <span style="color: #E2E8F0; font-size: 13px;">{guideline["preferred_tone"] or "Professional, approachable, trustworthy."}</span>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Color Palette Visualizer
        st.markdown(
            "<h4 style='color: #FFFFFF;'>Approved Color Palette</h4>",
            unsafe_allow_html=True,
        )
        colors = guideline["color_palette"]
        if colors:
            cols = st.columns(len(colors))
            for i, hex_code in enumerate(colors):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style="background-color: {hex_code}; height: 60px; border-radius: 8px; border: 1px solid #334155;"></div>
                        <div style="text-align: center; font-size: 12px; font-weight: 700; color: #E2E8F0; margin-top: 4px;">{hex_code}</div>
                    """,
                        unsafe_allow_html=True,
                    )

    with tab_upload:
        st.markdown("### Ingest Brand Guideline (PDF, DOCX, TXT, MD)")
        st.caption(
            "Documents are cleaned, chunked into 500-character segments, embedded with all-MiniLM-L6-v2, and stored in the ChromaDB vector database."
        )
        with st.form("doc_upload_form"):
            doc_title = st.text_input(
                "Document Title",
                placeholder="e.g. NovaTech Brand Guidelines & Visual System 2026",
            )
            doc_file = st.file_uploader(
                "Upload Brand Document", type=["pdf", "docx", "txt", "md"]
            )
            doc_btn = st.form_submit_button("Index into Knowledge Vault")

            if doc_btn and doc_file:
                with st.spinner("Extracting, chunking and generating embeddings..."):
                    try:
                        res = st.session_state.client.upload_guideline_document(
                            file_bytes=doc_file.getvalue(),
                            filename=doc_file.name,
                            title=doc_title,
                        )
                        st.success(
                            f"Indexed '{res['filename']}' ({res['chunk_count']} semantic chunks) into ChromaDB!"
                        )
                    except Exception as e:
                        st.error(f"Upload error: {e}")

        # List existing indexed documents
        st.markdown(
            "<h4 style='color: #FFFFFF; margin-top: 20px;'>Indexed Brand Documents</h4>",
            unsafe_allow_html=True,
        )
        docs = st.session_state.client.list_documents()
        if not docs:
            st.info("No external guideline documents uploaded yet.")
        else:
            doc_table = [
                {
                    "Document Title": d["document_title"],
                    "Filename": d["filename"],
                    "Type": d["file_type"].upper(),
                    "Semantic Chunks": d["chunk_count"],
                    "Uploaded": d["uploaded_at"][:10],
                }
                for d in docs
            ]
            st.dataframe(
                pd.DataFrame(doc_table), use_container_width=True, hide_index=True
            )

# ==================== PAGE: APPROVED SPECS & TERMINOLOGY ====================
elif menu_selection == "📋 Approved Specs & Terminology":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Deterministic Ground Truth</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Approved Specs & Terminology Registry</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Single source of truth for verified product specifications, approved pricing, and prohibited terms.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    tab_facts, tab_terms = st.tabs(
        ["📊 Approved Hardware & Policy Facts", "🚫 Prohibited & Preferred Terminology"]
    )

    with tab_facts:
        facts = st.session_state.client.list_facts()
        if facts:
            facts_table = [
                {
                    "ID": f["id"],
                    "Product": f["product_name"],
                    "Category": f["category"].upper(),
                    "Specification Key": f["fact_key"],
                    "Approved Value": f["fact_value"],
                    "Source Reference": f["source_reference"] or "Official Spec",
                }
                for f in facts
            ]
            st.dataframe(
                pd.DataFrame(facts_table), use_container_width=True, hide_index=True
            )

        with st.expander("➕ Add New Approved Brand Fact"):
            with st.form("new_fact_form"):
                p_name = st.text_input("Product Name", value="NovaBook Pro")
                p_cat = st.selectbox(
                    "Category", ["specification", "pricing", "warranty", "claim"]
                )
                f_key = st.text_input(
                    "Fact Key", placeholder="e.g. storage, processor, weight"
                )
                f_val = st.text_input(
                    "Approved Value", placeholder="e.g. 32GB Unified Memory"
                )
                f_source = st.text_input(
                    "Source Reference",
                    placeholder="e.g. Hardware Engineering Sheet v1.2",
                )
                add_fact_btn = st.form_submit_button("Save Brand Fact")

                if add_fact_btn:
                    try:
                        st.session_state.client.create_fact(
                            {
                                "product_name": p_name,
                                "category": p_cat,
                                "fact_key": f_key,
                                "fact_value": f_val,
                                "source_reference": f_source,
                            }
                        )
                        st.success("Brand fact registered!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab_terms:
        guideline = st.session_state.client.get_guidelines()
        st.markdown(
            "<h4 style='color: #F87171;'>Explicitly Prohibited Phrases</h4>",
            unsafe_allow_html=True,
        )
        prohibited = guideline["prohibited_phrases"]
        st.write(", ".join([f"`{p}`" for p in prohibited]))

        st.markdown(
            "<h4 style='color: #38BDF8; margin-top: 16px;'>Approved Terminology Mappings</h4>",
            unsafe_allow_html=True,
        )
        pref_map = guideline["preferred_terminology"]
        map_table = [
            {"Non-Standard / Deprecated Term": k, "Approved Standard Phrasing": v}
            for k, v in pref_map.items()
        ]
        st.dataframe(pd.DataFrame(map_table), use_container_width=True, hide_index=True)

# ==================== PAGE: GOVERNANCE ANALYTICS ====================
elif menu_selection == "📈 Governance Analytics":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Organizational Intelligence</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">Brand Governance Analytics & Insights</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Identify recurring organizational compliance bottlenecks and guideline ambiguity.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    analytics = st.session_state.client.get_analytics()

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("#### Violations by Category")
        cat_data = analytics["violations_by_category"]
        if cat_data:
            df_cat = pd.DataFrame(list(cat_data.items()), columns=["Category", "Count"])
            st.bar_chart(df_cat.set_index("Category"))
        else:
            st.info("No violations recorded yet.")

    with col_chart2:
        st.markdown("#### Status Distribution")
        status_data = analytics["status_distribution"]
        if status_data:
            df_stat = pd.DataFrame(
                list(status_data.items()), columns=["Status", "Submissions"]
            )
            st.bar_chart(df_stat.set_index("Status"))

    st.markdown("---")
    c_rec1, c_rec2 = st.columns(2)
    with c_rec1:
        st.markdown("#### Top Repeated Terminology Mistakes")
        rep_terms = analytics["top_repeated_terminology"]
        if rep_terms:
            st.dataframe(
                pd.DataFrame(rep_terms), use_container_width=True, hide_index=True
            )
        else:
            st.info("No repeated terminology errors.")

    with c_rec2:
        st.markdown("#### Frequently Incorrect Claims & Specifications")
        freq_claims = analytics["frequent_incorrect_claims"]
        if freq_claims:
            st.dataframe(
                pd.DataFrame(freq_claims), use_container_width=True, hide_index=True
            )
        else:
            st.info("No recurring claim conflicts.")

    # Actionable Policy Refinements
    st.markdown(
        "<h3 style='color: #FFFFFF; margin-top: 24px;'>Automated Brand Guideline Clarity Suggestions</h3>",
        unsafe_allow_html=True,
    )
    recs = analytics["policy_recommendations"]
    for r in recs:
        st.markdown(
            f"""
            <div class="brand-card">
                <span class="badge-high">{r["category"]}</span>
                <div style="margin-top: 6px; font-size: 14px; color: #FFFFFF;"><strong>Observation:</strong> {r["observation"]}</div>
                <div style="margin-top: 4px; font-size: 13px; color: #34D399;"><strong>Recommended Action:</strong> {r["action"]}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

# ==================== PAGE: SYSTEM DISCLOSURES ====================
elif menu_selection == "⚙️ System Disclosures":
    st.markdown(
        """
        <div>
            <span class="brand-badge">Compliance & Integrity</span>
            <h1 style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">System Disclosures & Architecture</h1>
            <p style="color: #94A3B8; margin: 0; font-size: 14px;">Technical disclosures and architectural declarations for CodeZen India 2026 Round 2.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("""
        ### Technology & API Disclosures
        - **Backend Framework:** FastAPI (Python 3.12, Uvicorn, Pydantic V2)
        - **Frontend Interface:** Streamlit (Custom Enterprise Dark Navy Theme)
        - **Embedding Model:** Sentence Transformers `all-MiniLM-L6-v2` (Local HuggingFace model, 384 dimensions)
        - **Vector Database:** ChromaDB (Local persistent client, tenant-isolated collections)
        - **Relational Storage:** SQLite / SQLAlchemy 2.0 (Migration-ready data access layer)
        - **Document Ingestion:** PyMuPDF (fitz), python-docx, Pillow, OpenCV-Python-Headless
        - **Multimodal Visual AI:** Google Gemini Vision (`gemini-1.5-flash`) with graceful deterministic fallbacks
        - **Security & Authentication:** JWT (PyJWT), Bcrypt 12-round salted password hashing, Tenant-isolated RBAC

        ### CodeZen India 2026 Technical Architecture & Key Improvements
        1. **Evidence-First Brand Intelligence:** Every detected violation is grounded with exact citations, verified specifications, and severity scoring.
        2. **Multimodal Brand Compliance:** Combines deterministic OpenCV/Pillow color clustering and WCAG 2.1 contrast calculations with Gemini Vision.
        3. **Human-Controlled Governance Intelligence:** Human reviewers maintain final authority. High scores never auto-publish. Complete revision tracking and policy refinement advice.
    """)
