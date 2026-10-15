"""
frontend/components/charts.py
------------------------------
Reusable Plotly chart factory functions shared across all pages.
"""

import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import score_to_color


# ── Shared layout defaults ─────────────────────────────────────────────────────
_TRANSPARENT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter, sans-serif"),
    margin=dict(l=0, r=0, t=10, b=0),
)


def score_gauge(value: float, title: str = "Score", max_val: float = 10.0) -> go.Figure:
    """Circular gauge for a single numeric score."""
    color = score_to_color(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"color": "#94a3b8", "size": 13}},
        number={"suffix": f"/{max_val:.0f}", "font": {"color": "#f1f5f9", "size": 26}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#94a3b8", "tickwidth": 1},
            "bar":  {"color": color},
            "bgcolor": "rgba(255,255,255,0.04)",
            "bordercolor": "rgba(255,255,255,0.08)",
            "steps": [
                {"range": [0,          max_val * 0.4], "color": "rgba(239,68,68,0.12)"},
                {"range": [max_val*0.4, max_val * 0.7], "color": "rgba(245,158,11,0.12)"},
                {"range": [max_val*0.7, max_val],       "color": "rgba(16,185,129,0.12)"},
            ],
        },
    ))
    fig.update_layout(**_TRANSPARENT_LAYOUT, height=220)
    return fig


def radar_chart(labels: list[str], values: list[float], max_val: float = 10.0) -> go.Figure:
    """Spider/radar chart for multi-dimension score breakdown."""
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(99,102,241,0.18)",
        line=dict(color="#6366f1", width=2.5),
        marker=dict(size=7, color="#818cf8",
                    line=dict(color="#fff", width=1.5)),
    ))
    fig.update_layout(
        **_TRANSPARENT_LAYOUT,
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, max_val],
                gridcolor="rgba(255,255,255,0.08)",
                tickcolor="#94a3b8", tickfont=dict(size=10),
            ),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        height=320,
        margin=dict(l=40, r=40, t=20, b=20),
    )
    return fig


def bar_chart(
    x: list, y: list,
    color_scale: bool = True,
    height: int = 250,
    xlabel: str = "",
    ylabel: str = "",
) -> go.Figure:
    """Vertical bar chart with gradient coloring."""
    colors = [score_to_color(v) for v in y] if color_scale else "#6366f1"
    fig = go.Figure(go.Bar(
        x=x, y=y,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.1f}" for v in y],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    ))
    fig.update_layout(
        **_TRANSPARENT_LAYOUT,
        height=height,
        xaxis=dict(showgrid=False, color="#94a3b8", title=xlabel),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   color="#94a3b8", title=ylabel),
        bargap=0.3,
    )
    return fig


def line_chart(
    x: list, y: list,
    label: str = "Score",
    height: int = 240,
) -> go.Figure:
    """Smooth area line chart for trend data."""
    fig = go.Figure(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        name=label,
        line=dict(color="#6366f1", width=3, shape="spline"),
        marker=dict(size=9, color="#818cf8",
                    line=dict(color="#fff", width=2)),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.1)",
    ))
    fig.update_layout(
        **_TRANSPARENT_LAYOUT,
        height=height,
        xaxis=dict(showgrid=False, color="#94a3b8"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   color="#94a3b8", range=[0, 10]),
        showlegend=False,
    )
    return fig


def donut_chart(labels: list[str], values: list[float], title: str = "") -> go.Figure:
    """Donut (pie) chart for categorical breakdowns."""
    COLORS = [
        "#6366f1","#06b6d4","#10b981","#f59e0b",
        "#ef4444","#8b5cf6","#ec4899","#14b8a6",
    ]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=COLORS[:len(labels)], line=dict(color="#0a0e1a", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#f1f5f9", size=11),
        hoverinfo="label+value+percent",
    ))
    if title:
        fig.add_annotation(
            text=title, x=0.5, y=0.5,
            font=dict(color="#f1f5f9", size=13, family="Inter"),
            showarrow=False,
        )
    fig.update_layout(**_TRANSPARENT_LAYOUT, height=280, showlegend=False)
    return fig


def match_progress_bar(match_pct: float) -> str:
    """Return HTML for a styled inline progress bar showing match %."""
    color = "#10b981" if match_pct >= 70 else "#f59e0b" if match_pct >= 40 else "#ef4444"
    return f"""
    <div style='margin:.5rem 0;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:.3rem;'>
            <span style='color:#94a3b8; font-size:.82rem;'>Match Score</span>
            <span style='color:{color}; font-weight:700;'>{match_pct}%</span>
        </div>
        <div style='background:rgba(255,255,255,0.06); border-radius:99px; height:8px; overflow:hidden;'>
            <div style='background:{color}; width:{match_pct}%; height:8px;
                        border-radius:99px; transition:width .6s ease;'></div>
        </div>
    </div>
    """
