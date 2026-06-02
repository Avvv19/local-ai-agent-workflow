"""Streamlit review interface.

Runs the workflow directly against the app package (no separate API process
required) and persists every run to SQLite. Screens: process, review queue
(role-filtered), history (CSV export), and a metrics dashboard.

Run with:  streamlit run ui/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import config, database  # noqa: E402
from app.intake import extract_text  # noqa: E402
from app.orchestrator import run_workflow  # noqa: E402

st.set_page_config(page_title="Local AI Agent Workflow", layout="wide")
database.init_db()

st.title("Local AI Agent Workflow Automation System")
st.caption(
    f"Backend: **{config.LLM_BACKEND}**  |  "
    "Classify → Extract → Summarize → Route → Score → Validate → Review"
)

tab_process, tab_queue, tab_history, tab_dash = st.tabs(
    ["Process Document", "Review Queue", "History", "Dashboard"]
)

# --------------------------------------------------------------------------- #
with tab_process:
    col_in, col_out = st.columns(2)

    with col_in:
        st.subheader("Document Intake")
        uploaded = st.file_uploader("Upload a .txt or .pdf file", type=["txt", "pdf"])
        sample_files = sorted(config.SAMPLE_DIR.glob("*.txt"))
        sample_choice = st.selectbox(
            "…or load a sample", ["(none)"] + [f.name for f in sample_files])
        default_text = ""
        if uploaded is not None:
            default_text = extract_text(uploaded.name, uploaded.read())
        elif sample_choice != "(none)":
            default_text = (config.SAMPLE_DIR / sample_choice).read_text()

        text = st.text_area("Document text", value=default_text, height=320)
        run_clicked = st.button("Run Workflow", type="primary")

    with col_out:
        st.subheader("Result")
        if run_clicked and text.strip():
            run = run_workflow(text)
            doc_id = database.save_run(
                run, uploaded.name if uploaded else "pasted_text.txt", text)
            r = run.result
            badge = "🟢" if r.review_status == "Ready for Review" else "🟠"
            st.markdown(f"### {badge} {r.review_status}  (doc #{doc_id})")
            st.progress(r.confidence_score,
                        text=f"Confidence score: {r.confidence_score:.2f}")

            meta = {
                "Document Type": r.document_type,
                "Priority": r.priority,
                "Customer / Request ID": r.customer_id or r.request_id or "—",
                "Invoice Number": r.invoice_number or "—",
                "Vendor Name": r.vendor_name or "—",
                "Topic": r.topic or "—",
                "Requested Action": r.requested_action or "—",
                "Routing Decision": r.routing_decision,
                "Validation Status": r.validation_status,
                "Confidence Flag": r.confidence_flag,
                "Missing Fields": ", ".join(r.missing_fields) or "None",
            }
            st.table(pd.DataFrame(meta.items(), columns=["Field", "Value"]))
            st.markdown("**Summary**")
            st.info(r.summary)

            if not run.validation.ok:
                st.error("Validation errors: " + "; ".join(run.validation.errors))
            if run.validation.warnings:
                st.warning("Warnings: " + "; ".join(run.validation.warnings))

            with st.expander("Workflow step log"):
                st.dataframe(pd.DataFrame([log.__dict__ for log in run.logs]),
                             use_container_width=True)
            with st.expander("Raw JSON output"):
                st.json(r.to_record())
        elif run_clicked:
            st.warning("Please provide some document text first.")

# --------------------------------------------------------------------------- #
with tab_queue:
    st.subheader("Human Review Queue")
    roles = ["(all)"] + sorted(set(config.ROUTE_ROLES.values()))
    role_choice = st.selectbox("Filter by team role", roles)
    role = None if role_choice == "(all)" else role_choice
    queue = database.get_review_queue(role=role)
    if not queue:
        st.success("Nothing waiting for review.")
    else:
        for item in queue:
            with st.container(border=True):
                st.markdown(f"**Doc #{item['document_id']} — "
                            f"{item.get('document_type','?')}**  "
                            f"`{item.get('role','')}`")
                st.write(item.get("summary") or "")
                st.caption(f"Reason: {item['reason']}")
                new_route = st.selectbox(
                    "Override routing", config.ROUTES, key=f"route_{item['id']}",
                    index=config.ROUTES.index("Human Review Required"))
                b1, b2, b3 = st.columns(3)
                if b1.button("Approve", key=f"approve_{item['id']}"):
                    database.update_routing(item["document_id"], new_route)
                    database.resolve_review(item["id"], "approved")
                    st.rerun()
                if b2.button("Reject", key=f"reject_{item['id']}"):
                    database.resolve_review(item["id"], "rejected")
                    st.rerun()
                if b3.button("Mark reviewed", key=f"resolve_{item['id']}"):
                    database.resolve_review(item["id"], "resolved")
                    st.rerun()

# --------------------------------------------------------------------------- #
with tab_history:
    st.subheader("Workflow History")
    history = database.get_history(200)
    if not history:
        st.info("No documents processed yet.")
    else:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.download_button("Download all (CSV)", database.export_csv(),
                           file_name="workflow_history.csv", mime="text/csv")
        c2.download_button("Download reviewed only (CSV)",
                           database.export_csv(reviewed_only=True),
                           file_name="reviewed_records.csv", mime="text/csv")

# --------------------------------------------------------------------------- #
with tab_dash:
    st.subheader("Metrics Dashboard")
    m = database.get_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total documents", m["total_documents"])
    c2.metric("Ready for review", m["ready_for_review"])
    c3.metric("Needs human review", m["needs_human_review"])
    c4.metric("Avg confidence",
              f"{m['avg_confidence']:.2f}" if m["avg_confidence"] is not None else "—")
    if m["by_document_type"]:
        st.markdown("**By document type**")
        st.bar_chart(pd.Series(m["by_document_type"]))
    if m["by_route"]:
        st.markdown("**By routing decision**")
        st.bar_chart(pd.Series(m["by_route"]))
