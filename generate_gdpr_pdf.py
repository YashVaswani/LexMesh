"""
GDPR 99 Articles PDF Generator
Generates the official condensed GDPR reference PDF (Articles 1–99, Chapters I–XI)
for RAG ingestion into ComplianceIQ.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle

def generate_gdpr_reference_pdf(output_path: str = "gdpr_condensed.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor("#1E3A8A")
    c_secondary = colors.HexColor("#0D9488")
    c_dark = colors.HexColor("#1E293B")

    title_style = ParagraphStyle('GTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_primary, spaceAfter=4)
    subtitle_style = ParagraphStyle('GSubTitle', fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=c_secondary, spaceAfter=15)
    ch_style = ParagraphStyle('GCh', fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=c_primary, spaceBefore=12, spaceAfter=6)
    art_style = ParagraphStyle('GArt', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_secondary, spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('GBody', fontName='Helvetica', fontSize=9, leading=13, textColor=c_dark, spaceAfter=6)

    story = []

    story.append(Paragraph("GDPR (Regulation (EU) 2016/679) — Condensed Reference", title_style))
    story.append(Paragraph("Official Reference Text: Articles 1–99 across Chapters I–XI", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=12))

    gdpr_structure = [
        ("CHAPTER I — General Provisions (Articles 1–4)", [
            (1, "Subject-matter and objectives", "Sets rules protecting natural persons regarding personal-data processing and the free movement of such data."),
            (2, "Material scope", "Applies to personal data processed wholly/partly by automated means and manual processing."),
            (3, "Territorial scope", "Applies to processing by a controller/processor established in the Union, regardless of where processing occurs."),
            (4, "Definitions", "Personal data, processing, controller, processor, recipient, consent, personal data breach, biometrics.")
        ]),
        ("CHAPTER II — Principles (Articles 5–11)", [
            (5, "Principles relating to processing of personal data", "Personal data must be processed lawfully, fairly, transparently, for specified explicit purposes, limited to necessary data, accurate, kept identifiable no longer than necessary, with appropriate security."),
            (6, "Lawfulness of processing", "Processing is lawful only if based on consent, contract necessity, legal obligation, vital interests, public interest, or legitimate interests."),
            (7, "Conditions for consent", "Controller must demonstrate consent was given. Consent requests must be in plain language. Data subject can withdraw consent at any time."),
            (8, "Conditions applicable to child's consent", "Processing based on child's consent is lawful from age 16; below that, parental authorization is required."),
            (9, "Processing of special categories of personal data", "Prohibits processing revealing racial origin, political opinions, genetic/biometric data, health data unless explicit consent or legal exception applies."),
            (10, "Processing of personal data relating to criminal convictions", "Permitted only under official authority control or Union/Member State law."),
            (11, "Processing which does not require identification", "Controller is not obliged to retain identifying information solely to comply with GDPR.")
        ]),
        ("CHAPTER III — Rights of the Data Subject (Articles 12–23)", [
            (12, "Transparent information, communication and modalities", "Information must be provided concisely, transparently, intelligibly, and in plain language."),
            (13, "Information to be provided where data is collected from subject", "Disclose controller identity, DPO contact, processing purposes, legal basis, recipients, retention period, and subject rights."),
            (14, "Information to be provided where data was not obtained from subject", "Same disclosures as Art. 13 plus categories of data and source."),
            (15, "Right of access by the data subject", "Right to obtain confirmation of processing, access to personal data, and details on processing logic."),
            (16, "Right to rectification", "Inaccurate personal data must be corrected without undue delay."),
            (17, "Right to erasure ('right to be forgotten')", "Controller must erase personal data without undue delay when data is no longer necessary or consent is withdrawn."),
            (18, "Right to restriction of processing", "Right to restrict processing where accuracy is contested or processing is unlawful."),
            (19, "Notification obligation regarding rectification or erasure", "Controller must notify recipients of data rectification or erasure."),
            (20, "Right to data portability", "Right to receive personal data in a structured, commonly used, machine-readable format and transmit to another controller."),
            (21, "Right to object", "Right to object at any time to processing based on legitimate interests or direct marketing."),
            (22, "Automated individual decision-making, including profiling", "Right not to be subject to a decision based solely on automated processing/profiling."),
            (23, "Restrictions", "Member State law may restrict rights to safeguard national security, defence, public security.")
        ]),
        ("CHAPTER IV — Controller and Processor (Articles 24–43)", [
            (24, "Responsibility of the controller", "Implement appropriate technical and organizational measures to demonstrate compliance."),
            (25, "Data protection by design and by default", "Build data protection principles into processing design from the outset."),
            (26, "Joint controllers", "Joint controllers must transparently determine respective responsibilities."),
            (27, "Representatives of controllers not established in the Union", "Designate an EU representative where Art. 3(2) applies."),
            (28, "Processor", "Processing by a processor must be governed by a binding contract specifying subject matter, duration, nature, and obligations."),
            (29, "Processing under authority of controller or processor", "Only process under instructions of controller."),
            (30, "Records of processing activities", "Maintain detailed records of processing activities for organizations over 250 employees or high risk."),
            (31, "Cooperation with supervisory authority", "Cooperate with supervisory authorities on request."),
            (32, "Security of processing", "Implement technical measures including encryption, confidentiality, resilience, and regular vulnerability testing."),
            (33, "Notification of personal data breach to supervisory authority", "Notify supervisory authority within 72 hours of becoming aware of a breach."),
            (34, "Communication of personal data breach to data subject", "Notify data subject without undue delay if breach risks high risk to rights."),
            (35, "Data protection impact assessment (DPIA)", "Conduct DPIA prior to processing likely to result in high risk."),
            (36, "Prior consultation", "Consult supervisory authority prior to processing if DPIA indicates high unmitigated risk."),
            (37, "Designation of data protection officer (DPO)", "Mandatory DPO for public authorities or large scale monitoring/special category data."),
            (38, "Position of DPO", "DPO must be properly involved in data protection matters and report to highest management."),
            (39, "Tasks of DPO", "Inform, advise, monitor compliance, and act as contact point for supervisory authority."),
            (40, "Codes of conduct", "Encourage codes of conduct to contribute to proper GDPR application."),
            (41, "Monitoring of approved codes of conduct", "Monitoring delegated to accredited independent bodies."),
            (42, "Certification", "Establish certification mechanisms, seals, and marks."),
            (43, "Certification bodies", "Certification bodies must be accredited.")
        ]),
        ("CHAPTER V — Transfers to Third Countries (Articles 44–50)", [
            (44, "General principle for transfers", "Any transfer must satisfy conditions of Chapter V."),
            (45, "Transfers on basis of adequacy decision", "Allowed where EU Commission decides third country ensures adequate protection."),
            (46, "Transfers subject to appropriate safeguards", "Allowed with Compliance Contractual Clauses (SCCs) or Binding Corporate Rules (BCRs)."),
            (47, "Binding corporate rules (BCRs)", "Approved rules for intra-group international data transfers."),
            (48, "Transfers not authorized by Union law", "Foreign court orders only enforceable if based on international agreements."),
            (49, "Derogations for specific situations", "Derogations for explicit consent, contract performance, or public interest."),
            (50, "International cooperation for protection of personal data", "Build international enforcement cooperation mechanisms.")
        ]),
        ("CHAPTER VI to XI — Supervisory Authorities & Final Provisions (Articles 51–99)", [
            (51, "Supervisory authority", "Independent public authority to monitor GDPR compliance."),
            (77, "Right to lodge a complaint", "Right to lodge complaint with supervisory authority."),
            (83, "General conditions for imposing administrative fines", "Fines up to €20M or 4% global annual turnover."),
            (99, "Entry into force and application", "Applied from 25 May 2018; directly applicable across all Member States.")
        ])
    ]

    for ch_title, articles in gdpr_structure:
        story.append(Paragraph(ch_title, ch_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=c_secondary, spaceBefore=1, spaceAfter=6))
        for art_num, art_name, art_desc in articles:
            story.append(Paragraph(f"Article {art_num} — {art_name}", art_style))
            story.append(Paragraph(art_desc, body_style))

    doc.build(story)
    print(f"[INFO] Generated official GDPR reference PDF at: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_gdpr_reference_pdf()
