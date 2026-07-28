"""Interactive friendship timeline for The Making of a Trio."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.timeline_data import TimelineDataError, chapter_range, load_timeline, phase_status


ROOT = Path(__file__).resolve().parent
REAL_TIMELINE = ROOT / "data" / "output" / "friendship_timeline.json"
DEMO_TIMELINE = ROOT / "data" / "demo" / "friendship_timeline.demo.json"
PAIR_DISPLAY = {
    "harry_ron": ("Harry", "Ron"),
    "harry_hermione": ("Harry", "Hermione"),
    "ron_hermione": ("Ron", "Hermione"),
}


def relationship_diagram(relationships: dict[str, dict[str, Any]]) -> str:
    positions = {
        "Harry": (300, 64),
        "Ron": (104, 330),
        "Hermione": (496, 330),
    }
    symbols = {"Harry": "⚡", "Ron": "♟️", "Hermione": "📚"}
    label_positions = {
        "harry_ron": (176, 182),
        "harry_hermione": (424, 182),
        "ron_hermione": (300, 290),
    }
    palette = ["#aa9d8c", "#927d67", "#7e6650", "#9a643e", "#8c4b32", "#6d3528"]
    edges = []
    for pair, (first, second) in PAIR_DISPLAY.items():
        relationship = relationships[pair]
        level = int(relationship["level"])
        x1, y1 = positions[first]
        x2, y2 = positions[second]
        label_x, label_y = label_positions[pair]
        dash = "9 9" if level == 0 else "4 7" if level == 1 else "none"
        width = 1.5 + level * 1.15
        label = html.escape(str(relationship["label"]))
        edges.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{palette[level]}" stroke-width="{width}" '
            f'stroke-dasharray="{dash}" stroke-linecap="round"/>'
            f'<g transform="translate({label_x} {label_y})">'
            '<rect x="-72" y="-17" width="144" height="34" rx="17" '
            'fill="#fffaf0" stroke="#d8c8ad"/>'
            f'<text text-anchor="middle" dominant-baseline="middle">{label}</text></g>'
        )
    nodes = []
    for name, (x, y) in positions.items():
        nodes.append(
            f'<g transform="translate({x} {y})">'
            '<circle r="51" fill="#fffaf0" stroke="#b88a59" stroke-width="2"/>'
            f'<text y="-3" class="symbol">{symbols[name]}</text>'
            f'<text y="26" class="name">{name}</text></g>'
        )
    return f"""
    <div class="diagram-shell">
      <svg viewBox="0 0 600 405" role="img"
           aria-label="Relationship diagram for Harry, Ron, and Hermione">
        <style>
          text {{ font-family: Georgia, serif; fill: #3c2d23; font-size: 14px; }}
          .symbol {{ text-anchor: middle; font-size: 27px; }}
          .name {{ text-anchor: middle; font-size: 16px; font-weight: 700; }}
        </style>
        {''.join(edges)}
        {''.join(nodes)}
      </svg>
    </div>
    <style>
      body {{ margin: 0; background: transparent; }}
      .diagram-shell {{
        border: 1px solid #dfceb3; border-radius: 22px;
        background: radial-gradient(circle at top, #fffdf6, #f5ead6);
        padding: 4px 16px 0; box-shadow: 0 10px 30px rgba(72, 49, 32, .08);
      }}
      svg {{ display: block; width: 100%; max-height: 405px; }}
    </style>
    """


def render_list(title: str, items: list[Any] | None) -> None:
    if not items:
        return
    st.markdown(f"#### {title}")
    for item in items:
        if isinstance(item, dict):
            text = item.get("action") or item.get("text") or ""
            character = item.get("character")
            effect = item.get("relationship_effect")
            if character:
                text = f"**{character}:** {text}"
            if effect:
                text += f" — _{effect}_"
            st.markdown(f"- {text}")
        else:
            st.markdown(f"- {item}")


st.set_page_config(
    page_title="The Making of a Trio",
    page_icon="📖",
    layout="centered",
)
st.markdown(
    """
    <style>
      .stApp { background: #f2e8d5; color: #382b23; }
      .block-container { max-width: 980px; padding-top: 2.5rem; padding-bottom: 4rem; }
      h1, h2, h3, h4 { font-family: Georgia, "Times New Roman", serif !important; color: #3c2b20; }
      h1 { letter-spacing: -0.025em; }
      [data-testid="stCaptionContainer"] { color: #765f4d; }
      div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 251, 241, .78); border-color: #dfceb3;
        border-radius: 18px; box-shadow: 0 8px 24px rgba(72, 49, 32, .06);
      }
      div[data-testid="stExpander"] {
        background: rgba(255, 251, 241, .72); border-color: #dfceb3;
        border-radius: 14px; overflow: hidden;
      }
      .status-pill {
        display: inline-block; padding: .3rem .7rem; border-radius: 999px;
        background: #e7d6b9; color: #66482f; font-size: .78rem; font-weight: 700;
        letter-spacing: .02em;
      }
      .demo-note {
        border-left: 4px solid #b47a45; background: #fff7e7;
        padding: .75rem 1rem; border-radius: 8px; color: #5a402c;
      }
      .relationship-key { color: #745c49; font-size: .88rem; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("The Making of a Trio")
st.caption(
    "An interactive timeline showing how Harry, Ron, and Hermione become "
    "friends during the first novel."
)

try:
    timeline = load_timeline(REAL_TIMELINE, DEMO_TIMELINE)
except TimelineDataError as error:
    st.error(str(error))
    st.stop()

if timeline.source == "demo":
    st.markdown(
        f'<div class="demo-note"><strong>Demo data</strong><br>'
        f'{html.escape(timeline.notice)}</div>',
        unsafe_allow_html=True,
    )

phases = timeline.data["phases"]
phase_labels = [phase["label"] for phase in phases]
selected_label = st.select_slider(
    "Choose a story phase",
    options=phase_labels,
    value=phase_labels[0],
)
phase = phases[phase_labels.index(selected_label)]

st.markdown("---")
heading_col, status_col = st.columns([3, 1])
with heading_col:
    st.header(f"{phase.get('symbol', '')} {phase['label']}")
    st.caption(chapter_range(phase.get("chapter_numbers") or []))
with status_col:
    st.markdown(
        f'<div style="text-align:right;padding-top:1.1rem">'
        f'<span class="status-pill">{html.escape(phase_status(phase, timeline.source))}</span>'
        "</div>",
        unsafe_allow_html=True,
    )

components.html(relationship_diagram(phase["relationships"]), height=445)
st.markdown(
    '<div class="relationship-key">Line weight and style show broad relationship '
    "stages—not scientific scores.</div>",
    unsafe_allow_html=True,
)

summary = phase.get("summary")
if summary:
    with st.container(border=True):
        st.subheader(phase.get("friendship_stage") or "Phase summary")
        st.write(summary)
        if phase.get("change_from_previous_phase"):
            st.markdown(f"**What changed:** {phase['change_from_previous_phase']}")

detail_columns = st.columns(2)
with detail_columns[0]:
    render_list("Key actions", phase.get("character_actions"))
    render_list("Cooperation", phase.get("cooperation"))
with detail_columns[1]:
    render_list("Conflict or tension", phase.get("conflict"))
    render_list("Limitations", phase.get("limitations"))

evidence = phase.get("evidence") or []
if evidence:
    st.subheader("Supporting evidence")
    st.caption(
        "Ranked source-text evidence from deterministic retrieval—not generated interpretation."
    )
    for index, item in enumerate(evidence, start=1):
        chapter = item.get("chapter", "Unknown")
        relevance = item.get("relevance") or "Supporting passage"
        characters = ", ".join(item.get("characters") or [])
        with st.expander(f"{index}. Chapter {chapter} · {relevance}"):
            if characters:
                st.caption(f"Characters detected: {characters}")
            st.write(item.get("excerpt") or "No excerpt available.")
else:
    st.info("No supporting evidence was retained for this phase.")

with st.expander("Relationship scale"):
    scale = timeline.data["project"].get("relationship_scale") or {}
    for value in sorted(scale, key=int):
        st.markdown(f"**{value} — {scale[value]}**")
    note = timeline.data["project"].get("measurement_note")
    if note:
        st.caption(note)
