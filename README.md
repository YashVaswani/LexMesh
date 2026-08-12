# 🛡️ LexMesh — Enterprise Agentic RAG Compliance Engine

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Orchestration-Google%20ADK-green.svg)](https://ai.google.dev/)
[![Database](https://img.shields.io/badge/VectorDB-Supabase%20pgvector-emerald.svg)](https://supabase.com/)
[![LLM](https://img.shields.io/badge/LLM-Gemini%203.6%20Flash%20%7C%20Groq%20Llama%203.3-orange.svg)](https://groq.com/)
[![UI](https://img.shields.io/badge/UI-Streamlit-ff4b4b.svg)](https://streamlit.io/)
[![PDF Engine](https://img.shields.io/badge/Exporter-ReportLab-darkblue.svg)](https://www.reportlab.com/)

**LexMesh** is an enterprise-grade, zero-cost-stack **Agentic RAG (Retrieval-Augmented Generation)** compliance engine that automates legal regulatory gap analysis. Built using Google ADK orchestration primitives, LexMesh evaluates company policy documents against all 99 Articles and 11 Chapters of the **EU General Data Protection Regulation (GDPR)** in **under 15 seconds**.

---

## 🌟 Key Features & Capabilities

- 🤖 **Google ADK Hierarchical Orchestration**: Uses a **Supervisor Router Agent** to oversee policy ingestion and delegate evaluation tasks in parallel to **11 Chapter Sub-Agents (Chapters I–XI)** via Python `ThreadPoolExecutor`.
- ⚡ **High-Speed Chapter Batching (< 15s)**: Optimizes multi-agent RAG execution from 10 minutes down to **~10–15 seconds total** by evaluating requirements in chapter batches.
- 🎯 **Deterministic Audit Engine (`temperature=0.0`)**: Enforces greedy decoding across Gemini 3.6 Flash and Groq Llama 3.3 70B, delivering 100% stable, repeatable, and audit-grade compliance reports.
- ☁️ **Cloud Vector Store & Pre-filtering**: Stores 64 atomic requirement chunks with 384-dimensional vector embeddings in **Supabase Cloud (`pgvector` + `jsonb`)**, using SQL pre-filtering (`.eq("chapter_number", chapter)`).
- ⚖️ **Official GDPR Article 83 Statutory Fine Calculator**: Automatically evaluates Tier 1 (€10M or 2% revenue) vs Tier 2 (€20M or 4% revenue) statutory fine exposure based on failing chapters and articles.
- 📂 **Auto-Metadata PDF Extractor**: Parses Page 1 of uploaded company policy PDFs to automatically extract Company Name and Policy Version/Title.
- 📋 **Prioritized Action Plan (P1 / P2 / P3)**: Automatically prioritizes severe `Conflicting` legal contradictions at the top of **P1 Critical Priority**, followed by `Not Met` omissions and `Partially Met` operational fixes.
- 📄 **Audit-Grade ReportLab PDF Exporter**: Exports complete 8-page compliance PDFs featuring cover score gauges, status legend boxes, requirement cards with cited policy quotes, and action plans.

---

## 🏗️ Architecture Blueprint

```mermaid
flowchart TD
    A[📄 User Uploads Policy PDF] --> B[🔍 Auto-Extract Company & Policy Metadata]
    B --> C[🤖 Google ADK Supervisor Agent]
    C --> D[⚙️ Parallel Execution Pool - ThreadPoolExecutor]
    
    subgraph SubAgents [11 Chapter Sub-Agents (Chapters I–XI)]
        E1[Ch I: General Provisions]
        E2[Ch II: Principles]
        E3[Ch III: Data Subject Rights]
        E4[Ch IV: Controller & Processor]
        E5[Ch V: Third Country Transfers]
        E6[Ch VI–XI: Governance & Penalties]
    end
    
    D --> E1 & E2 & E3 & E4 & E5 & E6
    
    E1 & E2 & E3 & E4 & E5 & E6 <--> F[(☁️ Supabase Cloud pgvector Store)]
    
    E1 & E2 & E3 & E4 & E5 & E6 --> G[📊 Master Report Aggregator]
    
    G --> H[🎨 Interactive Streamlit Web UI]
    G --> I[📄 ReportLab Audit PDF Exporter]
    G --> J[💾 JSON Report Storage]
```

---

## 📂 Repository Structure

```
LexMesh/
├── app.py                      # Interactive Streamlit Web Dashboard & UI
├── config.py                   # Environment configuration loader
├── generate_gdpr_pdf.py        # Script generating GDPR condensed reference PDF
├── sync_to_supabase.py         # Cloud vector store ingestion script
├── requirements.txt            # Python dependencies
├── gdpr_requirements_master.json # 64 atomic requirement catalog with vector embeddings
├── agents/
│   ├── __init__.py
│   ├── adk_agent.py            # Google ADK Agent Primitives & Orchestrator
│   ├── chapter_agents.py       # LLM provider fallback chain (Gemini 3.6 -> Groq 70B) & Sub-Agents
│   └── supervisor.py           # Supervisor Router Agent, dynamic scoring & action plans
├── db/
│   ├── __init__.py
│   └── supabase_client.py      # Supabase Client for pgvector & compliance reports
└── reporter/
    ├── __init__.py
    └── pdf_generator.py        # Enterprise ReportLab PDF report generator
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11 or higher
- Supabase Cloud account (`pgvector` enabled)
- API Keys: Google AI Studio (`GEMINI_API_KEY`), Groq Console (`GROQ_API_KEY`)

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/YashVaswani/LexMesh.git
cd LexMesh

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 4. Vector Database Ingestion (Supabase Cloud)
Sync the 64 atomic GDPR requirement chunks with 384-dimensional vector embeddings to Supabase:
```powershell
python sync_to_supabase.py
```

### 5. Launch Web Dashboard
Start the interactive Streamlit dashboard:
```powershell
python -m streamlit run app.py
```

---

## 🗺️ Roadmap (Phase 2 & Beyond)

- [x] **Phase 1**: Complete GDPR 99-Article Compliance Engine with Google ADK Parallel RAG & PDF Exporter.
- [ ] **Phase 2**: Multi-Framework Enterprise Support (**ISO 27001:2022**, **RBI Cybersecurity Framework**, **HIPAA**, **SOC 2 Type II**).
- [ ] **Phase 3**: Automated AI Remediation Patch Generator (generating draft policy rewrite clauses automatically).

---

## 📄 License & Attribution
Designed & Engineered by **LexMesh Team**. Powered by Google ADK, Gemini, Groq, Supabase, and Streamlit.
