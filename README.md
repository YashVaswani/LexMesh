# LexMesh — Policy-Centric Multi-Framework Compliance Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Orchestration-Google%20ADK-green.svg)](https://ai.google.dev/)
[![SDK](https://img.shields.io/badge/Google%20GenAI-v2.18.1-4285F4.svg)](https://github.com/googleapis/python-genai)
[![Database](https://img.shields.io/badge/Database-Supabase%20Cloud-emerald.svg)](https://supabase.com/)
[![LLM](https://img.shields.io/badge/LLMs-Gemini%20Flash%20%7C%20Groq%20Llama%203.3-orange.svg)](https://groq.com/)
[![UI](https://img.shields.io/badge/UI-NiceGUI-green.svg)](https://nicegui.io/)
[![PDF Engine](https://img.shields.io/badge/Exporter-ReportLab-darkblue.svg)](https://www.reportlab.com/)

**LexMesh** is an enterprise-grade, policy-centric **Multi-Framework Compliance & Legal Audit Engine**. Powered by Google ADK orchestration primitives, LexMesh simultaneously evaluates company policy documents against **250+ atomic, testable statutory requirements** across four major global regulatory standards:

1. **EU GDPR** — General Data Protection Regulation (Art. 1–99)
2. **US HIPAA** — Health Insurance Portability and Accountability Act (45 CFR § 160 & 164)
3. **RBI Cyber Framework** — Reserve Bank of India Cyber Security & KYC Master Directions
4. **SOC 2 Type II** — AICPA Trust Services Criteria (Security, Availability, Confidentiality, Processing Integrity, Privacy)

---

## 🌟 Key Features & Capabilities

- 🤖 **Google ADK Supervisor Architecture**: Uses a **Supervisor Router Agent** to oversee policy ingestion and delegate audit evaluations in parallel to **Chapter Sub-Agents** via an 8-worker thread pool.
- ⚡ **High-Speed Sub-45s Pipeline**: Evaluates 250+ requirements across selected statutory frameworks simultaneously in **under 45 seconds** using 15-item micro-batching and `asyncio.to_thread` non-blocking execution.
- 🏢 **Org Industry Presets & Framework Deselection**: Provides an **Organization Industry** selector with presets (SaaS, Healthcare, Banking/Fintech, Global, Custom) that automatically presets checkable switches, letting users easily include/exclude specific standards (RBI, HIPAA, GDPR, SOC 2).
- 📊 **Weighted Article Coverage Scoring**: Calculates framework compliance scores by grouping requirement verdicts by article/control first. Weights requirements (Fully Met = 1.0, Partially Met = 0.70, Not Met = 0.0) to prevent partial coverage from dragging overall scores near 0%.
- 🎯 **Targeted Zero-Cost RAG Matcher**: Extracts top relevant policy paragraphs (~600 chars / ~350 tokens) per requirement using keyword-density scoring, eliminating context dilution and cutting API token consumption by **70%**.
- ⚡ **Persistent SHA-256 Audit Caching**: Features in-memory + Supabase Cloud database lookup fallback. Persistent database cached loader runs automatically across server restarts for instant zero-cost re-audits.
- 🔑 **Multi-Key API Fallback Engine**: Supports comma-separated keys (`GEMINI_API_KEY=key1,key2`) and multi-model rotation across modern **Google GenAI SDK v2** (`gemini-3.1-flash-lite`, `gemini-flash-latest`) with secondary **Groq fallback** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).
- 🎨 **Executive Sage & Beige Design System**: Features a high-contrast Warm Beige (`#F5F2EB`) and Forest Sage (`#23382B`) design system, Google Font **Plus Jakarta Sans** typography, Lucide vector SVG icons, and 0 emoji clutter.
- 🎯 **Interactive Scope Selection**: Sidebar dropdown and switches enable users to dynamically filter audit scores, policy domain gap accordions, and action plans by active standards in real-time.
- 🚨 **Statutory Fine & Exposure Calculator**: Evaluates statutory penalties across standards:
  - **EU GDPR**: Art. 83 Tier 1 (€10M or 2%) vs Tier 2 (€20M or 4% global annual revenue).
  - **US HIPAA**: Statutory Civil Monetary Penalty ($1.9M+/year under 45 CFR § 160).
  - **RBI Cyber**: Banking Regulation Act statutory penalties & FIU-IND enforcement directions.
  - **SOC 2**: Qualified vs Unqualified audit opinion risk.
- ✅ **Separated Compliant Areas & Remediation Plan**: Action plan strictly lists actual policy gaps (P1 Critical, P2 High, P3 Medium). Fully compliant items are moved to a dedicated **Compliant Areas** section in the UI (showing verification quotes) and in PDF reports.
- 📄 **Audit-Grade ReportLab PDF & JSON Exporter**: Renders PDF audit reports complete with wrapped regulation tables, status color indicators, policy quotes, and targeted scope downloads.

---

## 🏗️ Architecture Blueprint

```mermaid
flowchart TD
    A[📄 User Uploads Policy PDF] --> B[🔍 Metadata Extractor & Section Chunking]
    B --> C[🤖 Google ADK Supervisor Router Agent]
    C --> D[⚙️ 8-Worker Parallel Thread Pool]
    
    subgraph ParallelSubAgents [Parallel Chapter Sub-Agents]
        E1[EU GDPR Sub-Agent]
        E2[US HIPAA Sub-Agent]
        E3[RBI Cyber Sub-Agent]
        E4[SOC 2 Type II Sub-Agent]
    end
    
    D --> E1 & E2 & E3 & E4
    
    E1 & E2 & E3 & E4 <--> F[🎯 Targeted Paragraph Matcher]
    E1 & E2 & E3 & E4 <--> G[(⚡ SHA-256 Cache - In-Memory & Supabase)]
    E1 & E2 & E3 & E4 <--> H[🔑 Multi-Key Fallback Engine: Gemini v2 → Groq]
    
    E1 & E2 & E3 & E4 --> I[📊 Master Audit Report Aggregator]
    
    I --> J[🎨 Interactive NiceGUI Web Dashboard]
    I --> K[📄 ReportLab Audit PDF Exporter]
    I --> L[📥 Targeted Scope JSON Exporter]
```

---

## 📂 Repository Structure

```
LexMesh/
├── nicegui_app.py                 # NiceGUI Enterprise Web Dashboard & UI Entry Point
├── config.py                      # Multi-Key Environment Config & Key Parsing Engine
├── requirements.txt               # Lightweight Cloud Dependencies (~25 MB)
├── vercel.json                    # Vercel Deployment Configuration
├── Procfile                       # Procfile for Cloud Web Services
├── api/
│   └── index.py                   # Vercel Serverless Entry Point
├── gdpr_requirements_master.json  # 99 Article GDPR Statutory Requirement Catalog
├── hipaa_requirements_master.json # HIPAA 45 CFR § 160/164 Statutory Requirement Catalog
├── rbi_requirements_master.json   # RBI Master Direction Cyber Security Requirement Catalog
├── soc2_requirements_master.json  # AICPA SOC 2 Type II Trust Criteria Catalog
├── agents/
│   ├── __init__.py
│   ├── adk_agent.py               # Google ADK Agent Primitives & Workflow Orchestrator
│   ├── chapter_agents.py          # Targeted RAG, SHA-256 Audit Cache & LLM Provider Chain
│   └── supervisor.py              # Supervisor Agent, Scoring Engine & Action Plan Builder
├── db/
│   ├── __init__.py
│   └── supabase_client.py         # Supabase Cloud Client & Persistent Audit Cache Manager
├── reporter/
│   ├── __init__.py
│   └── pdf_generator.py           # Enterprise ReportLab PDF Exporter with Text Wrapping
├── ui/
│   ├── components/                # Modular NiceGUI UI Components & Lucide SVGs
│   │   ├── action_plan.py         # Remediation plan details UI card
│   │   ├── compliant_areas.py     # Fully met requirements & verification quotes card
│   │   └── ...
│   └── styles/theme.css           # Executive Warm Beige & Sage Green Design System
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.14)
- **API Keys**: Google AI Studio (`GEMINI_API_KEY`), Groq Console (`GROQ_API_KEY`)
- *(Optional)* Supabase Cloud project for cloud report & audit verdict storage

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/YashVaswani/LexMesh.git
cd LexMesh

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the project root:
```env
# Supports comma-separated keys for automatic rotation & higher throughput
GEMINI_API_KEY=your_gemini_key_1,your_gemini_key_2
GROQ_API_KEY=your_groq_key_1,your_groq_key_2

# Optional Supabase Cloud database configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 4. Launch Application
Start the interactive NiceGUI executive dashboard:
```bash
python nicegui_app.py
```
Open your browser at **`http://localhost:8080`**.

---

## 📊 Compliance Coverage Summary

| Framework Standard | Statutory Authority | Requirement Count | Fine / Risk Exposure |
| :--- | :--- | :--- | :--- |
| **EU GDPR** | Regulation (EU) 2016/679 | 99 Articles | Up to €20M or 4% Global Annual Revenue |
| **US HIPAA** | 45 CFR § 160 & § 164 | 43 Criteria | Up to $1.9M+ Civil Monetary Penalties / Year |
| **RBI Cyber** | RBI Master Directions | 68 Provisions | Banking Regulation Act Penalties & Directives |
| **SOC 2 Type II** | AICPA Trust Criteria | 43 Controls | Audit Qualification & Enterprise Deal Loss |

---

## 📄 License & Attribution
Engineered by the **LexMesh Development Team**. Powered by Google ADK, Google GenAI SDK v2, Gemini Flash, Groq Llama 3.3, Supabase, NiceGUI, Lucide Icons, and ReportLab.
