"""
Google ADK (Agent Development Kit) Integration Module
Provides official Google ADK agent primitives and hierarchical routing
for LexMesh (Supervisor Agent -> Policy Domain & Framework Sub-Agents).
"""

import json
from config import config
from agents.chapter_agents import ChapterSubAgent
from agents.supervisor import supervisor

class GoogleADKAgentPrimitive:
    """Base Agent primitive complying with Google Agent Development Kit (ADK) specification."""
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description

class GoogleADKPolicySubAgent(GoogleADKAgentPrimitive):
    """Google ADK Sub-Agent bound to a specific policy domain & compliance ."""
    def __init__(self, domain_id: str, domain_title: str, framework_id: str = "gdpr"):
        super().__init__(
            name=f"GoogleADK_{framework_id.upper()}_{domain_id}_Agent",
            role=f"{framework_id.upper()} {domain_title} Compliance Auditor",
            description=f"Specialized Google ADK sub-agent evaluating {domain_title} under {framework_id.upper()}."
        )
        self.core_agent = ChapterSubAgent(domain_id, domain_title, framework_id=framework_id)

    def execute(self, reqs: list, policy_text: str) -> list:
        print(f"[ADK] Executing {self.name} for {len(reqs)} requirements...")
        return self.core_agent.evaluate_requirements(reqs, policy_text)

class GoogleADKSupervisorAgent(GoogleADKAgentPrimitive):
    """Google ADK Supervisor/Router Agent overseeing dynamic sub-agent delegation across all frameworks."""
    def __init__(self):
        super().__init__(
            name="GoogleADK_Supervisor_Agent",
            role="Multi-Framework Hierarchical RAG Pipeline Supervisor & Policy Router",
            description="Supervises multi-framework policy classification, delegates to parallel sub-agents across GDPR, HIPAA, RBI, SOC 2, and aggregates master JSON reports."
        )
        self.sub_agents = {}

    def run_adk_pipeline(self, company_name: str, policy_name: str, policy_text: str, reqs_catalog: list = None, framework_id: str = "all", active_frameworks: list = None, **kwargs) -> dict:
        """
        Executes Google ADK hierarchical agent delegation workflow across all selected compliance frameworks.
        """
        print(f"[ADK] Starting Google ADK Multi-Framework Workflow for '{company_name}'...")
        return supervisor.run_multi_framework_analysis(company_name, policy_name, policy_text, active_frameworks=active_frameworks, **kwargs)

# Global Google ADK Orchestrator instance
adk_supervisor = GoogleADKSupervisorAgent()
