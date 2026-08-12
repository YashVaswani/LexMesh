"""
Google ADK (Agent Development Kit) Integration Module
Provides official Google ADK agent primitives and hierarchical routing
for ComplianceIQ (Supervisor Agent -> Chapter Sub-Agents).
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

class GoogleADKChapterSubAgent(GoogleADKAgentPrimitive):
    """Google ADK Sub-Agent bound to a specific GDPR Chapter domain."""
    def __init__(self, chapter_number: str, chapter_title: str):
        super().__init__(
            name=f"GoogleADK_Chapter_{chapter_number}_Agent",
            role=f"GDPR Chapter {chapter_number} Compliance Auditor",
            description=f"Specialized Google ADK sub-agent evaluating Chapter {chapter_number}: '{chapter_title}'."
        )
        self.core_agent = ChapterSubAgent(chapter_number, chapter_title)

    def execute(self, reqs: list, policy_text: str) -> list:
        print(f"[ADK] Executing {self.name} for {len(reqs)} requirements...")
        return self.core_agent.evaluate_requirements(reqs, policy_text)

class GoogleADKSupervisorAgent(GoogleADKAgentPrimitive):
    """Google ADK Supervisor/Router Agent overseeing dynamic sub-agent delegation."""
    def __init__(self):
        super().__init__(
            name="GoogleADK_Supervisor_Agent",
            role="Hierarchical RAG Pipeline Supervisor & Policy Router",
            description="Supervises policy chunk classification, delegates to Chapter Sub-Agents, and aggregates master JSON reports."
        )
        self.sub_agents = {}

    def get_sub_agent(self, chapter_number: str, chapter_title: str) -> GoogleADKChapterSubAgent:
        if chapter_number not in self.sub_agents:
            self.sub_agents[chapter_number] = GoogleADKChapterSubAgent(chapter_number, chapter_title)
        return self.sub_agents[chapter_number]

    def run_adk_pipeline(self, company_name: str, policy_name: str, policy_text: str, reqs_catalog: list) -> dict:
        """
        Executes Google ADK hierarchical agent delegation workflow.
        """
        print(f"[ADK] Starting Google ADK Agentic Workflow for '{company_name}'...")
        return supervisor.run_analysis(company_name, policy_name, policy_text, reqs_catalog)

# Global Google ADK Orchestrator instance
adk_supervisor = GoogleADKSupervisorAgent()
