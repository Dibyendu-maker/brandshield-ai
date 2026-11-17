import streamlit as st


def apply_enterprise_theme():
    """Injects premium enterprise dark navy & subtle violet styling."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Global typography & base background */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background-color: #0A0F1D;
            color: #F1F5F9;
        }

        /* Top header bar */
        header[data-testid="stHeader"] {
            background: rgba(10, 15, 29, 0.85);
            backdrop-filter: blur(12px);
        }

        /* Sidebar custom enterprise styling */
        section[data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
        }

        /* Custom Cards */
        .brand-card {
            background: #111827;
            border: 1px solid #1F2937;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            transition: border-color 0.2s ease;
        }
        .brand-card:hover {
            border-color: #374151;
        }

        /* Header gradient badge */
        .brand-badge {
            display: inline-block;
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 4px 10px;
            border-radius: 20px;
            margin-bottom: 8px;
        }

        /* Severity Pills */
        .badge-critical {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        .badge-high {
            background-color: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.4);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        .badge-medium {
            background-color: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            border: 1px solid rgba(59, 130, 246, 0.4);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        .badge-low {
            background-color: rgba(107, 114, 128, 0.15);
            color: #9CA3AF;
            border: 1px solid rgba(107, 114, 128, 0.4);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }

        /* Status Pills */
        .badge-approved {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.4);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
        }
        .badge-rejected {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
        }
        .badge-review {
            background-color: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.4);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
        }
        .badge-draft {
            background-color: rgba(148, 163, 184, 0.15);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.4);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
        }

        /* Metric Hero */
        .metric-container {
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin-top: 8px;
        }
        .metric-score {
            font-size: 44px;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1;
        }
        .metric-score-high { color: #10B981; }
        .metric-score-med { color: #F59E0B; }
        .metric-score-low { color: #EF4444; }

        /* Diff Highlighting */
        .diff-deleted {
            background-color: rgba(239, 68, 68, 0.25);
            color: #FCA5A5;
            text-decoration: line-through;
            padding: 2px 5px;
            border-radius: 4px;
        }
        .diff-inserted {
            background-color: rgba(16, 185, 129, 0.25);
            color: #6EE7B7;
            font-weight: 600;
            padding: 2px 5px;
            border-radius: 4px;
        }

        /* Button Enhancements */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 8px 18px;
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
            transform: translateY(-1px);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def render_score_badge(score: float):
    if score >= 85:
        color_class = "metric-score-high"
        status_label = "Compliant"
    elif score >= 60:
        color_class = "metric-score-med"
        status_label = "Needs Attention"
    else:
        color_class = "metric-score-low"
        status_label = "High Risk Violations"

    return f"""
        <div class="brand-card">
            <span class="brand-badge">Overall Brand Compliance</span>
            <div class="metric-container">
                <span class="metric-score {color_class}">{score}%</span>
                <span style="color: #94A3B8; font-size: 14px; font-weight: 600;">{status_label}</span>
            </div>
            <p style="color: #64748B; font-size: 12px; margin-top: 8px; margin-bottom: 0;">
                Calculated via deterministic rule audit, ground truth specs & WCAG heuristics.
            </p>
        </div>
    """


def render_severity_pill(severity: str) -> str:
    s = severity.upper()
    if s == "CRITICAL":
        return '<span class="badge-critical">CRITICAL</span>'
    elif s == "HIGH":
        return '<span class="badge-high">HIGH</span>'
    elif s == "MEDIUM":
        return '<span class="badge-medium">MEDIUM</span>'
    else:
        return '<span class="badge-low">LOW</span>'


def render_status_pill(status_val: str) -> str:
    s = status_val.lower()
    if s == "approved":
        return '<span class="badge-approved">Approved</span>'
    elif s == "rejected":
        return '<span class="badge-rejected">Rejected</span>'
    elif s in ["submitted", "under_review", "resubmitted"]:
        return (
            f'<span class="badge-review">{status_val.replace("_", " ").title()}</span>'
        )
    elif s == "changes_requested":
        return '<span class="badge-high">Changes Requested</span>'
    else:
        return f'<span class="badge-draft">{status_val.title()}</span>'
