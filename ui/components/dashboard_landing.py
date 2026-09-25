from nicegui import ui
from ui.components.lucide import lucide_icon
from db.supabase_client import supabase_db
from datetime import datetime
import math

def create_dashboard_landing(on_run_new_audit=None):
    """Render the executive Dashboard Landing Page.

    Parameters
    ----------
    on_run_new_audit : callable | None
        Callback invoked when the user clicks the "Run New Audit" button.
    """

    # ========================================================
    # PAGE TITLE ROW
    # ========================================================

    with ui.row().classes(
        "w-full items-center justify-between"
    ):
        with ui.column().classes("gap-1"):
            ui.label(
                "Compliance Dashboard"
            ).classes(
                "text-3xl font-bold lex-page-title"
            )

            ui.label(
                "Enterprise compliance overview and audit history"
            ).classes(
                "text-sm lex-page-subtitle"
            )

        if on_run_new_audit:
            ui.button(
                "Run New Audit",
                on_click=on_run_new_audit,
            ).classes(
                "lex-run-button"
            ).style(
                "width: auto !important; "
                "padding: 0 32px !important;"
            ).props("unelevated no-caps")


    # ========================================================
    # FETCH REAL DATA
    # ========================================================
    
    reports = supabase_db.get_all_reports()
    
    total_audits = len(reports)
    
    last_audit_str = "None"
    recent_audits_data = []
    chart_dates = []
    chart_scores = []
    
    framework_scores = {}
    avg_by_framework = {}
    
    if reports:
        # Calculate framework averages
        # Map DB framework names to chart labels
        name_map = {
            "SOC 2 Type II": "SOC 2",
            "RBI Cyber Framework": "RBI Cyber",
            "US HIPAA": "HIPAA",
            "EU GDPR": "GDPR"
        }
        for r in reports:
            fw_summaries = r.get("framework_summaries") or {}
            for fw_key, fw_data in fw_summaries.items():
                raw_name = fw_data.get("framework_name", "")
                mapped_name = name_map.get(raw_name)
                # Fallbacks in case names change slightly
                if not mapped_name:
                    if "SOC" in raw_name: mapped_name = "SOC 2"
                    elif "RBI" in raw_name: mapped_name = "RBI Cyber"
                    elif "HIPAA" in raw_name: mapped_name = "HIPAA"
                    elif "GDPR" in raw_name: mapped_name = "GDPR"
                    else: mapped_name = raw_name
                
                score = fw_data.get("score", 0)
                if mapped_name:
                    framework_scores.setdefault(mapped_name, []).append(score)
            
        avg_by_framework = {
            fw: round(sum(scores) / len(scores), 1) if scores else 0
            for fw, scores in framework_scores.items()
        }
        
        # Sort descending (newest first) in case the DB didn't
        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Last Audit
        last_dt_str = reports[0].get("created_at")
        if last_dt_str:
            try:
                # Handle standard ISO8601 from Supabase
                dt = datetime.fromisoformat(last_dt_str.replace("Z", "+00:00"))
                last_audit_str = dt.strftime("%b %d, %Y")
            except:
                last_audit_str = str(last_dt_str)[:10]

        # All Audit Reports
        for r in reports:
            dt_str = r.get("created_at", "")
            fmt_date = ""
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    fmt_date = dt.strftime("%b %d, %Y")
                except:
                    fmt_date = str(dt_str)[:10]
                    
            recent_audits_data.append({
                "company": r.get("company_name", "Unknown"),
                "policy": r.get("policy_name", "Unknown"),
                "score": r.get("overall_score", 0),
                "date": fmt_date,
            })
            
        # Score Trend Chart (Last 10, chronological)
        trend_reports = reports[:10]
        trend_reports.reverse()
        for r in trend_reports:
            dt_str = r.get("created_at", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    chart_dates.append(dt.strftime("%b %d"))
                except:
                    chart_dates.append("")
            else:
                chart_dates.append("")
            chart_scores.append(r.get("overall_score", 0))

    # ========================================================
    # (Frameworks explanation moved to standalone page)
    # ========================================================

    # ========================================================
    # KPI STAT CARDS
    # ========================================================

    with ui.row().classes("w-full gap-5 mt-4 items-stretch"):

        _kpi_card(
            icon="file-text",
            label="TOTAL AUDITS RUN",
            value=str(total_audits),
            color="var(--lex-sage)",
            subtitle_hint="Audit History ↓",
            tooltip_text="Hover highlights table • Click to jump ↓",
            on_click=lambda: ui.run_javascript(
                "const el = document.getElementById('lex-recent-audits-section'); "
                "if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); "
                "el.classList.add('lex-table-highlight-pulse'); "
                "setTimeout(() => el.classList.remove('lex-table-highlight-pulse'), 1800); }"
            ),
            on_hover_enter=lambda: ui.run_javascript(
                "document.getElementById('lex-recent-audits-section')?.classList.add('lex-table-hover-highlight');"
            ),
            on_hover_leave=lambda: ui.run_javascript(
                "document.getElementById('lex-recent-audits-section')?.classList.remove('lex-table-hover-highlight');"
            ),
        )

        _kpi_card(
            icon="layers",
            label="FRAMEWORKS COVERED",
            value=str(len(avg_by_framework)) if avg_by_framework else "0",
            color="var(--lex-blue)",
            subtitle_hint="Click to explore frameworks ➔",
            tooltip_text="Click to explore frameworks ➔",
            on_click=lambda: ui.navigate.to('/frameworks'),
        )

        _kpi_card(
            icon="calendar",
            label="LAST AUDIT",
            value=last_audit_str,
            color="var(--lex-beige-dark)",
        )


    # ========================================================
    # CHARTS ROW
    # ========================================================

    with ui.row().classes("w-full gap-5 mt-2"):

        # ---------------------------------------------------
        # COMPLIANCE SCORE TREND (Area Line Chart)
        # ---------------------------------------------------

        with ui.column().classes(
            "flex-1 lex-score-card"
        ).style("min-width: 0;"):

            with ui.row().classes(
                "items-center gap-2 mb-2"
            ):
                lucide_icon(
                    "trending-up",
                    size=20,
                    class_name="lex-pipeline-icon",
                )

                ui.label(
                    "Compliance Score Trend"
                ).classes(
                    "lex-section-heading"
                ).style(
                    "margin: 0 !important;"
                )

            ui.echart({
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross",
                        "lineStyle": {
                            "color": "#4e795d",
                            "type": "dashed",
                            "width": 1.5,
                        },
                    },
                    "backgroundColor": "rgba(26, 36, 31, 0.94)",
                    "borderColor": "#4e795d",
                    "borderWidth": 1.5,
                    "padding": [10, 14],
                    "textStyle": {
                        "color": "#f5f2eb",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 600,
                        "fontSize": 12,
                    },
                    "formatter": "{b}<br/><span style='display:inline-block;margin-right:6px;border-radius:50%;width:8px;height:8px;background-color:#7ca689;'></span>{a}: <b>{c}%</b>",
                },
                "xAxis": {
                    "type": "category",
                    "data": chart_dates,
                    "axisLabel": {
                        "color": "#647269",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 600,
                    },
                    "axisLine": {
                        "lineStyle": {"color": "#d4cbc0"},
                    },
                },
                "yAxis": {
                    "type": "value",
                    "min": 0,
                    "max": 100,
                    "axisLabel": {
                        "formatter": "{value}%",
                        "color": "#647269",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 600,
                    },
                    "splitLine": {
                        "lineStyle": {
                            "color": "#e6dfd3",
                            "type": "dashed",
                        },
                    },
                },
                "series": [
                    {
                        "name": "Compliance Score",
                        "type": "line",
                        "smooth": True,
                        "data": chart_scores,
                        "lineStyle": {
                            "color": "#4e795d",
                            "width": 3,
                        },
                        "itemStyle": {
                            "color": "#4e795d",
                        },
                        "emphasis": {
                            "focus": "series",
                            "itemStyle": {
                                "color": "#7ca689",
                                "borderColor": "#ffffff",
                                "borderWidth": 2.5,
                                "shadowBlur": 12,
                                "shadowColor": "rgba(78, 121, 93, 0.6)",
                            },
                        },
                        "areaStyle": {
                            "color": {
                                "type": "linear",
                                "x": 0,
                                "y": 0,
                                "x2": 0,
                                "y2": 1,
                                "colorStops": [
                                    {
                                        "offset": 0,
                                        "color": "rgba(78, 121, 93, 0.35)",
                                    },
                                    {
                                        "offset": 1,
                                        "color": "rgba(78, 121, 93, 0.02)",
                                    },
                                ],
                            },
                        },
                        "symbol": "circle",
                        "symbolSize": 8,
                    }
                ],
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "top": "10%",
                    "containLabel": True,
                },
            }).classes("w-full").style("height: 320px;")

        # ---------------------------------------------------
        # AVERAGE SCORE BY FRAMEWORK (Horizontal Bar Chart)
        # ---------------------------------------------------

        with ui.column().classes(
            "flex-1 lex-score-card"
        ).style("min-width: 0;"):

            with ui.row().classes(
                "items-center gap-2 mb-2"
            ):
                lucide_icon(
                    "bar-chart-3",
                    size=20,
                    class_name="lex-target-icon",
                )

                ui.label(
                    "Average Score by Framework"
                ).classes(
                    "lex-section-heading"
                ).style(
                    "margin: 0 !important;"
                )

            # Prepare framework chart data
            color_lookup = {
                "SOC 2": "#8a7642",
                "RBI Cyber": "#b45339",
                "HIPAA": "#2e7067",
                "GDPR": "#4e795d"
            }
            framework_order = ["SOC 2", "RBI Cyber", "HIPAA", "GDPR"]
            series_data = [
                {
                    "value": avg_by_framework.get(fw, 0),
                    "itemStyle": {
                        "color": color_lookup[fw],
                        "borderRadius": [0, 6, 6, 0]
                    }
                }
                for fw in framework_order
            ]

            ui.echart({
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "shadow",
                        "shadowStyle": {
                            "color": "rgba(78, 121, 93, 0.12)",
                        },
                    },
                    "backgroundColor": "rgba(26, 36, 31, 0.94)",
                    "borderColor": "#4e795d",
                    "borderWidth": 1.5,
                    "padding": [10, 14],
                    "textStyle": {
                        "color": "#f5f2eb",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 600,
                        "fontSize": 12,
                    },
                    "formatter": "{b}: <b>{c}% Average Score</b>",
                },
                "xAxis": {
                    "type": "value",
                    "min": 0,
                    "max": 100,
                    "axisLabel": {
                        "formatter": "{value}%",
                        "color": "#647269",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 600,
                    },
                    "splitLine": {
                        "lineStyle": {
                            "color": "#e6dfd3",
                            "type": "dashed",
                        },
                    },
                },
                "yAxis": {
                    "type": "category",
                    "data": [
                        "SOC 2",
                        "RBI Cyber",
                        "HIPAA",
                        "GDPR",
                    ],
                    "axisLabel": {
                        "color": "#1b2721",
                        "fontFamily": "Plus Jakarta Sans",
                        "fontWeight": 700,
                        "fontSize": 13,
                    },
                    "axisLine": {
                        "lineStyle": {"color": "#d4cbc0"},
                    },
                },
                "series": [
                    {
                        "type": "bar",
                        "data": series_data,
                        "barWidth": "45%",
                        "emphasis": {
                            "focus": "self",
                            "itemStyle": {
                                "shadowBlur": 12,
                                "shadowColor": "rgba(0, 0, 0, 0.3)",
                            },
                        },
                    }
                ],
                "grid": {
                    "left": "3%",
                    "right": "6%",
                    "bottom": "3%",
                    "top": "8%",
                    "containLabel": True,
                },
            }).classes("w-full").style("height: 320px;")

    # ========================================================
    # RECENT AUDIT REPORTS TABLE
    # ========================================================

    with ui.column().classes("w-full lex-score-card mt-2").props('id="lex-recent-audits-section"'):

        with ui.row().classes(
            "w-full items-center justify-between mb-3"
        ):
            with ui.row().classes("items-center gap-2"):
                lucide_icon(
                    "clipboard-list",
                    size=20,
                    class_name="lex-pipeline-icon",
                )

                ui.label(
                    "All Audit Reports"
                ).classes(
                    "lex-section-heading"
                ).style(
                    "margin: 0 !important;"
                )

            if recent_audits_data:
                ui.label(
                    f"{len(recent_audits_data)} Total Audits"
                ).classes(
                    "text-xs font-bold px-3 py-1 rounded-full"
                ).style(
                    "background: rgba(78,121,93,0.12); color: #4e795d; border: 1px solid rgba(78,121,93,0.3);"
                )

        # The data is now dynamically pulled from Supabase via recent_audits_data

        # Table header (sticky)
        with ui.row().classes(
            "w-full items-center px-4 py-2"
        ).style(
            "border-bottom: 2px solid var(--lex-border);"
        ):
            ui.label("COMPANY").classes(
                "flex-1 text-xs font-extrabold tracking-widest"
            ).style("color: var(--lex-muted);")

            ui.label("POLICY").classes(
                "flex-1 text-xs font-extrabold tracking-widest"
            ).style("color: var(--lex-muted);")

            ui.label("SCORE").classes(
                "text-xs font-extrabold tracking-widest"
            ).style(
                "color: var(--lex-muted); "
                "width: 80px; text-align: center;"
            )

            ui.label("DATE").classes(
                "text-xs font-extrabold tracking-widest"
            ).style(
                "color: var(--lex-muted); "
                "width: 140px; text-align: center;"
            )

        # Table rows container with 8-report pagination
        PAGE_SIZE = 8
        total_audits = len(recent_audits_data) if recent_audits_data else 0
        total_pages = max(1, math.ceil(total_audits / PAGE_SIZE)) if total_audits > 0 else 1

        table_rows_container = ui.column().classes("w-full").style("gap: 0;")
        pagination_bar_container = ui.row().classes(
            "w-full items-center justify-between px-4 py-3 flex-wrap gap-3"
        ).style("border-top: 1px solid var(--lex-border);")

        current_page_box = {"page": 1}

        def render_audit_page(page_num: int):
            current_page_box["page"] = page_num
            table_rows_container.clear()
            pagination_bar_container.clear()

            if not recent_audits_data:
                with table_rows_container:
                    with ui.row().classes("w-full justify-center p-6"):
                        ui.label("No audits found. Run a new audit to see data here.").classes("text-sm text-gray-500")
                return

            start_idx = (page_num - 1) * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, total_audits)
            page_audits = recent_audits_data[start_idx:end_idx]

            with table_rows_container:
                for audit in page_audits:
                    _score = audit["score"]

                    if _score >= 80:
                        pill_bg = "#3b6349"
                    elif _score >= 60:
                        pill_bg = "#b45339"
                    else:
                        pill_bg = "#9e3232"

                    with ui.row().classes(
                        "w-full items-center px-4 py-3 lex-table-row cursor-pointer"
                    ).style(
                        "border-bottom: 1px solid var(--lex-border);"
                    ):
                        ui.label(
                            audit["company"]
                        ).classes(
                            "flex-1 font-bold"
                        ).style(
                            "color: var(--lex-text); "
                            "font-size: 0.95rem;"
                        )

                        ui.label(
                            audit["policy"]
                        ).classes(
                            "flex-1 font-semibold"
                        ).style(
                            "color: var(--lex-muted); "
                            "font-size: 0.9rem;"
                        )

                        ui.label(
                            f"{_score}%"
                        ).style(
                            f"background: {pill_bg}; "
                            "color: #ffffff; "
                            "border-radius: 999px; "
                            "padding: 4px 14px; "
                            "font-weight: 800; "
                            "font-size: 0.85rem; "
                            "width: 80px; "
                            "text-align: center;"
                        )

                        ui.label(
                            audit["date"]
                        ).classes(
                            "font-semibold"
                        ).style(
                            "color: var(--lex-muted); "
                            "font-size: 0.85rem; "
                            "width: 140px; "
                            "text-align: center;"
                        )

            # Pagination controls: ONLY show if total audits exceed 8
            if total_audits > PAGE_SIZE:
                with pagination_bar_container:
                    ui.label(
                        f"Showing {start_idx + 1}–{end_idx} of {total_audits} reports"
                    ).classes(
                        "text-xs font-semibold"
                    ).style("color: var(--lex-muted);")

                    with ui.row().classes("items-center gap-1.5"):
                        # Prev Button
                        prev_btn = ui.button(
                            "‹ Prev",
                            on_click=lambda: render_audit_page(max(1, current_page_box["page"] - 1))
                        ).props("dense unelevated size=sm").classes("px-3 py-1 font-bold rounded-lg text-xs")
                        if page_num <= 1:
                            prev_btn.disable().style("opacity: 0.35; cursor: not-allowed; background: var(--lex-surface-hover); color: var(--lex-muted);")
                        else:
                            prev_btn.style("background: var(--lex-surface-hover); color: var(--lex-text); cursor: pointer;")

                        # Numeric Page Pills
                        for p in range(1, total_pages + 1):
                            if p == 1 or p == total_pages or abs(p - page_num) <= 1:
                                is_active = (p == page_num)
                                p_btn = ui.button(
                                    str(p),
                                    on_click=lambda p_val=p: render_audit_page(p_val)
                                ).props("dense unelevated size=sm").classes("w-7 h-7 font-bold rounded-lg text-xs")
                                if is_active:
                                    p_btn.style("background: var(--lex-sage, #4e795d) !important; color: #ffffff !important;")
                                else:
                                    p_btn.style("background: var(--lex-surface-hover); color: var(--lex-text); cursor: pointer;")
                            elif abs(p - page_num) == 2:
                                ui.label("…").classes("text-xs font-bold px-1").style("color: var(--lex-muted);")

                        # Next Button
                        next_btn = ui.button(
                            "Next ›",
                            on_click=lambda: render_audit_page(min(total_pages, current_page_box["page"] + 1))
                        ).props("dense unelevated size=sm").classes("px-3 py-1 font-bold rounded-lg text-xs")
                        if page_num >= total_pages:
                            next_btn.disable().style("opacity: 0.35; cursor: not-allowed; background: var(--lex-surface-hover); color: var(--lex-muted);")
                        else:
                            next_btn.style("background: var(--lex-surface-hover); color: var(--lex-text); cursor: pointer;")

        render_audit_page(1)




# ============================================================
# INTERNAL KPI CARD HELPER
# ============================================================

def _kpi_card(
    icon: str,
    label: str,
    value: str,
    color: str,
    on_click=None,
    subtitle_hint=None,
    tooltip_text=None,
    on_hover_enter=None,
    on_hover_leave=None,
):
    """Render a single KPI stat card with strict alignment and interactive hover hints."""

    card = ui.column().classes(
        "flex-1 lex-score-card justify-between gap-3 h-36 cursor-pointer relative"
    ).style("min-width: 180px;")
    
    if on_click:
        card.on('click', on_click)

    if on_hover_enter:
        card.on('mouseenter', on_hover_enter)
    if on_hover_leave:
        card.on('mouseleave', on_hover_leave)

    if tooltip_text:
        card.tooltip(tooltip_text).classes(
            "text-xs font-bold px-3 py-1.5 rounded-lg shadow-xl"
        ).style(
            "background: rgba(26, 36, 31, 0.95); color: #f5f2eb; border: 1px solid var(--lex-sage);"
        )

    with card:

        with ui.row().classes(
            "items-center gap-3 flex-nowrap w-full"
        ):
            # Icon badge
            with ui.element("div").classes("shrink-0 lex-icon-badge").style(
                f"width: 42px; height: 42px; "
                f"border-radius: 12px; "
                f"background: {color}20; "
                f"display: flex; align-items: center; "
                f"justify-content: center;"
            ):
                lucide_icon(
                    icon,
                    size=22,
                    class_name="",
                    extra_style=f"color: {color};",
                )

            ui.label(
                label
            ).classes(
                "lex-card-title flex-1 leading-tight font-extrabold"
            ).style("font-size: 0.75rem; letter-spacing: 0.05em;")

        with ui.row().classes("w-full items-end justify-between"):
            ui.label(
                value
            ).style(
                f"font-size: 2.2rem; "
                f"font-weight: 900; "
                f"color: var(--lex-text); "
                f"line-height: 1; "
                f"margin-top: 0;"
            )

            if subtitle_hint:
                with ui.row().classes(
                    "items-center gap-1 text-[11px] font-extrabold px-2.5 py-1 rounded-lg lex-card-hint-badge"
                ).style(
                    "background: var(--lex-surface-hover); color: var(--lex-sage); border: 1px solid var(--lex-border);"
                ):
                    ui.label(subtitle_hint)

