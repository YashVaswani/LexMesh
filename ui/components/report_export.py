import json
import re
import tempfile
from pathlib import Path

from nicegui import ui

from reporter.pdf_generator import generate_compliance_pdf


EXPORT_SCOPES = {
    "🌐 All Selected Frameworks": None,
    "🇪🇺 EU GDPR Only": ["gdpr"],
    "🏥 US HIPAA Only": ["hipaa"],
    "🏦 RBI Cyber Framework Only": ["rbi"],
    "🛡️ SOC 2 Type II Only": ["soc2"],
}


def create_report_export(
    report,
    company="Organization",
):

    ui.label(
        "Report Export"
    ).classes(
        "lex-section-heading"
    )

    ui.label(
        report.get(
            "executive_summary",
            "Generate and download the compliance report.",
        )
    ).classes(
        "lex-posture-text"
    )

    ui.separator().classes(
        "my-4"
    )

    scope_select = ui.select(
        options=list(
            EXPORT_SCOPES.keys()
        ),
        value="🌐 All Selected Frameworks",
        label="Export compliance scope",
    ).props(
        "outlined"
    ).classes(
        "w-full"
    )

    with ui.row().classes(
        "w-full gap-4 mt-4"
    ):

        json_button = ui.button(
            "Download JSON",
            icon="data_object",
        ).props(
            "unelevated"
        ).classes(
            "lex-export-json-button"
        )

        pdf_button = ui.button(
            "Render PDF Report",
            icon="picture_as_pdf",
        ).props(
            "unelevated"
        ).classes(
            "lex-export-pdf-button"
        )

    result_label = ui.label(
        ""
    ).classes(
        "lex-analysis-status"
    )

    def target_report():

        keys = EXPORT_SCOPES.get(
            scope_select.value
        )

        if not keys:
            return report

        return _filter_export(
            report,
            keys,
        )

    def safe_name(value):

        value = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            str(value),
        )

        return value.strip("_") or "Organization"

    def download_json():

        payload = target_report()

        company_name = safe_name(
            company
        )

        keys = EXPORT_SCOPES.get(
            scope_select.value
        )

        tag = (
            "MASTER"
            if not keys
            else "_".join(keys).upper()
        )

        directory = Path(
            tempfile.gettempdir()
        ) / "lexmesh_exports"

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = directory / (
            f"LexMesh_GapAnalysis_"
            f"{tag}_{company_name}.json"
        )

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        ui.download(
            str(path)
        )

        result_label.set_text(
            "✅ JSON report generated."
        )

    def download_pdf():

        payload = target_report()

        company_name = safe_name(
            company
        )

        keys = EXPORT_SCOPES.get(
            scope_select.value
        )

        tag = (
            "MASTER"
            if not keys
            else "_".join(keys).upper()
        )

        directory = Path(
            tempfile.gettempdir()
        ) / "lexmesh_exports"

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = directory / (
            f"LexMesh_Report_"
            f"{tag}_{company_name}.pdf"
        )

        try:

            generate_compliance_pdf(
                payload,
                str(path),
            )

            ui.download(
                str(path)
            )

            result_label.set_text(
                "✅ PDF report generated."
            )

        except Exception as e:

            result_label.set_text(
                f"❌ PDF generation failed: {e}"
            )

            ui.notify(
                str(e),
                type="negative",
            )

    json_button.on_click(
        download_json
    )

    pdf_button.on_click(
        download_pdf
    )


def _filter_export(
    report,
    keys,
):

    payload = json.loads(
        json.dumps(report)
    )

    summary = payload.get(
        "summary",
        {},
    )

    frameworks = summary.get(
        "framework_summaries",
        {},
    )

    summary[
        "framework_summaries"
    ] = {
        k: v
        for k, v in frameworks.items()
        if k in keys
    }

    gaps = payload.get(
        "all_gaps_flat",
        [],
    )

    payload[
        "all_gaps_flat"
    ] = [
        gap
        for gap in gaps
        if gap.get("framework")
        in keys
    ]

    return payload