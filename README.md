<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,20:1a0533,50:00d4ff,80:6e40c9,100:0d1117&height=240&section=header&text=Local%20AI%20Agent%20Workflow&fontSize=42&fontColor=00d4ff&fontAlignY=38&desc=🤖%20Autonomous%20Document%20Intelligence%20Pipeline%20·%20Local%20First%20·%20Production%20Grade&descSize=16&descColor=c084fc&animation=twinkling" width="100%"/>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=22&duration=3000&pause=800&color=00D4FF&background=0D111700&center=true&vCenter=true&multiline=false&repeat=true&width=800&height=55&lines=received+→+clean+→+classify+→+extract+→+summarize;→+route+→+score+→+validate+→+escalate+→+log;100%25+JSON+Validity+·+100%25+Classification+Match;No+Paid+APIs+·+No+Cloud+Credentials+·+Runs+Locally" alt="Pipeline Animation"/>

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

<br/>

```
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
          UNSTRUCTURED DOCUMENTS  →  INTELLIGENT STRUCTURED RECORDS
                    No Paid APIs · No Cloud Credentials · Local First
◈━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◈
```

</div>

---

<div align="center">

## 🧠 WHAT IT DOES

</div>

Converts unstructured business documents — forms, tickets, emails, requests, operational notes — into **classified, extracted, summarized, routed, and review-ready structured records** using a local-first agentic AI pipeline.

It supports both an **AI Engineer** angle (agentic workflow, automation, backend APIs, validation, review queue, local AI execution) and a **Data Scientist** angle (text preprocessing, classification, structured records, evaluation checks, reporting-ready outputs).

<div align="center">

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        🔄  PIPELINE FLOW                                        │
│                                                                                 │
│  📥 received → 🧹 clean → 🏷️  classify → 🔍 extract → 📝 summarize             │
│             → 🔀 route → 📊 score → ✅ validate → 🚨 escalate → 🗄️  log        │
│                                                                                 │
│  Each step: small · independently testable · logged · confidence-scored         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

</div>

---

<div align="center">

## 📊 EVALUATION RESULTS

| Metric | Score | Count |
|:---|:---:|:---:|
| ✅ JSON Validity Rate | **100.0%** | 28/28 |
| ✅ Classification Match | **100.0%** | 28/28 |
| ✅ Routing Match | **100.0%** | 28/28 |
| ✅ Required-Field Completion | **78.6%** | 22/28 |
| ✅ Human-Review Precision | **1.00** | — |
| ✅ Human-Review Recall | **1.00** | — |

*Sample set: 28 documents · 7 categories · 6 incomplete · 4 ambiguous · 10 escalation triggers*

</div>

---

<div align="center">

## 🎯 BUSINESS PROBLEM

</div>

Teams still process incoming tickets, forms, emails, and requests by hand: read it, classify it, pull out fields, summarize, decide where it goes, check for missing info, prep it for review. **Slow · Inconsistent · Hard to scale.**

This local AI workflow automates that entire loop while keeping a human in the loop for anything low-confidence or incomplete.

---

<div align="center">

## 📄 DOCUMENT CATEGORIES & ROUTING

</div>

<div align="center">

| 🏷️ Category | 🔀 Routing Decision |
|:---:|:---:|
| `Billing Request` | Finance Review |
| `Support Ticket` | Customer Support Review |
| `Customer Complaint` | Operations Review |
| `Vendor Request` | Technical Review |
| `Internal Operations Request` | Operations Review |
| `Policy Question` | General Queue |
| `General Inquiry` | General Queue |

</div>

---

<div align="center">

## 📤 OUTPUT SCHEMA

</div>

```json
{
  "document_type"    : "Billing Request",
  "priority"         : "Medium",
  "customer_id"      : "CUS-1029",
  "invoice_number"   : "INV-88421",
  "issue_summary"    : "Customer was billed twice — suspected overcharge.",
  "requested_action" : "Refund duplicate charge and reissue invoice.",
  "summary"          : "Billing Request: customer reports duplicate charge, requests correction.",
  "routing_decision" : "Finance Review",
  "missing_fields"   : [],
  "validation_status": "pass",
  "review_status"    : "Ready for Review",
  "confidence_flag"  : "Acceptable",
  "confidence_score" : 1.0
}
```

---

<div align="center">

## 🏗️ ARCHITECTURE

</div>

<div align="center">

| Layer | Component |
|:---:|:---|
| 🖥️ **Frontend** | Streamlit UI — process, role-filtered review queue, history, dashboard |
| ⚡ **Backend** | FastAPI — optional API-key auth, CORS, Prometheus `/metrics`, CSV export |
| 🧩 **Orchestration** | Plain-Python step orchestrator with validation gate + confidence scoring |
| 🤖 **Model** | Ollama + Llama 3 (optionally via LangChain) — or deterministic mock |
| 🛡️ **Validation** | Rule-based Python checks + transparent confidence scoring |
| 🗄️ **Data** | SQLAlchemy ORM → SQLite or PostgreSQL · Alembic migrations |
| 📈 **Observability** | Structured logging + Prometheus metrics |

</div>

---

<div align="center">

## 🔧 CONFIDENCE SCORING — TRANSPARENT, NOT RANDOM

</div>

```python
# Confidence is calculated from verifiable workflow checks — never a black box
confidence_score = 1.0   # starts perfect

deductions = {
    "invalid_json"              : -0.40,
    "failed_validation"         : -0.30,
    "low_classification_conf"   : -0.20,
    "each_missing_required_field": -0.10,
    "weak_or_empty_summary"     : -0.10,
}

# A document routes to Human Review when score < 0.6
```

---

<div align="center">

## 🚨 HUMAN REVIEW TRIGGERS

</div>

<div align="center">

```
A document is escalated to Human Review when ANY of the following hold:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔴  Required fields are missing
  🔴  Document type is unclear (low classification confidence)
  🔴  Routing decision is unsupported or validation fails
  🔴  Confidence score < 0.6
  🔴  JSON output invalid after retry
  🔴  Summary is empty or too weak
  🔴  Input text is too short or ambiguous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

</div>

---

<div align="center">

## 🌐 API ENDPOINTS

</div>

<div align="center">

| Method | Path | Purpose |
|:---:|:---|:---|
| `GET` | `/health` | Health check + active backend |
| `POST` | `/process` | Run workflow on pasted text |
| `POST` | `/upload` | Run workflow on .txt/.pdf |
| `GET` | `/result/{id}` | Full record + workflow trace |
| `GET` | `/history` | Recent processed documents |
| `GET` | `/review-queue?role=` | Open review items, optional role filter |
| `POST` | `/review/{id}/resolve` | Resolve / approve / reject |
| `PATCH` | `/result/{id}/route` | Reviewer routing override |
| `GET` | `/metrics-summary` | Aggregate counts (JSON) |
| `GET` | `/export.csv` | History as CSV |
| `GET` | `/metrics` | Prometheus exposition format |

</div>

---

<div align="center">

## 🚀 HOW TO RUN LOCALLY

</div>

```bash
# ── 1. Install & Setup ────────────────────────────────────────────────────────
pip install -r requirements.txt
make migrate          # or the app auto-creates tables on first run

# ── 2. Start Services ─────────────────────────────────────────────────────────
make api              # → http://localhost:8000/docs
make ui               # → http://localhost:8501  (separate terminal)

# ── 3. Test & Lint ────────────────────────────────────────────────────────────
make test             # pytest + coverage
make lint             # ruff
make eval             # metrics over labelled sample set
```

```bash
# ── Real Local Model (Ollama + Llama 3) ───────────────────────────────────────
ollama pull llama3
export LLM_BACKEND=ollama          # or "langchain" (pip install langchain-ollama)
python scripts/check_ollama.py     # verify connectivity
python -m app.main

# ── Docker ────────────────────────────────────────────────────────────────────
docker compose up --build                   # mock backend, API + UI
docker compose --profile ollama up          # add local Ollama service
docker compose --profile postgres up        # add PostgreSQL service
```

---

<div align="center">

## 🛠️ TECH STACK

</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-6C47A3?style=for-the-badge&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logoColor=black)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

</div>

---

<div align="center">

## ⚠️ LIMITATIONS & ROADMAP

</div>

```
Current Limitations                    Planned Improvements
────────────────────────────────────   ────────────────────────────────────────
• Default: deterministic mock backend  → OCR for scanned PDFs
• Ollama/Llama 3 needs local setup     → Per-type extraction schemas
• Small evaluation sample set          → Per-user authentication & audit
• No OCR for scanned PDFs              → Alerting on metrics dashboard
                                       → Model-based confidence scoring
                                       → Multi-tenant review queues
                                       → Deployment automation
                                       → Historical evaluation dashboard
```

---

<div align="center">

## 👤 BUILT BY

**Venkata Vivek Varma Alluru**
*AI Engineer · ML Engineer · Data Scientist*

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Avvv19)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com)
[![Medium](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com)

> *"The best AI system is the one that solves real problems reliably at scale."*

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,25:6e40c9,50:00d4ff,75:1a0533,100:0d1117&height=120&section=footer" width="100%"/>
