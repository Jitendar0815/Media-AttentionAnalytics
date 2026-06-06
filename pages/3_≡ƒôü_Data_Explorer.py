"""
pages/3_📁_Data_Explorer.py
Raw content table with filtering, search, summary stats and CSV export.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import components as ui  # noqa: E402
from src import data_generator as dg  # noqa: E402
from src import utils  # noqa: E402

utils.configure_page("Data Explorer", icon="📁")
utils.sidebar_nav(active="explorer")

ui.page_header(
    "Data Explorer",
    "Slice the underlying content dataset, inspect individual posts and export "
    "exactly what you filtered.",
    kicker="raw signal",
)

content = utils.load_content(160)

# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #
f1, f2, f3 = st.columns([1.2, 1, 1], gap="large")
with f1:
    platforms = st.multiselect("Platform", dg.PLATFORMS, default=dg.PLATFORMS)
with f2:
    formats = st.multiselect("Format", dg.CONTENT_FORMATS, default=dg.CONTENT_FORMATS)
with f3:
    min_attn = st.slider("Min attention score", 0, 100, 0)

search = st.text_input("Search title", placeholder="e.g. tutorial, reveal, deep dive…")

flt = content[
    content["platform"].isin(platforms)
    & content["format"].isin(formats)
    & (content["attention_score"] >= min_attn)
]
if search.strip():
    flt = flt[flt["title"].str.contains(search.strip(), case=False, na=False)]

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
ui.section_title("Selection summary", hint=f"{len(flt):,} of {len(content):,} rows")
if flt.empty:
    st.info("No content matches the current filters. Try widening them.")
    ui.footer()
    st.stop()

ui.metric_row([
    {"label": "Rows", "value": f"{len(flt):,}", "icon": "🧾", "accent": "var(--cyan)"},
    {"label": "Total views", "value": utils.human(flt["views"].sum()),
     "icon": "👁️", "accent": "var(--violet)"},
    {"label": "Avg attention", "value": f"{flt['attention_score'].mean():.1f}",
     "icon": "📡", "accent": "var(--accent)"},
    {"label": "Top viral index", "value": f"{flt['viral_index'].max():.2f}",
     "icon": "🚀", "accent": "var(--magenta)"},
])

# --------------------------------------------------------------------------- #
# Table
# --------------------------------------------------------------------------- #
ui.section_title("Content table")
sort_col = st.selectbox(
    "Sort by",
    ["published", "views", "attention_score", "retention", "viral_index"],
    index=1,
    format_func=lambda c: c.replace("_", " ").title(),
)
view = flt.sort_values(sort_col, ascending=False)

st.dataframe(
    view,
    width="stretch",
    hide_index=True,
    height=460,
    column_config={
        "content_id": "ID",
        "title": "Title",
        "platform": "Platform",
        "format": "Format",
        "published": st.column_config.DateColumn("Published", format="MMM DD, YYYY"),
        "views": st.column_config.NumberColumn("Views", format="%d"),
        "attention_score": st.column_config.ProgressColumn(
            "Attention", min_value=0, max_value=100, format="%.1f"),
        "retention": st.column_config.NumberColumn("Retention", format="%.2f"),
        "engagements": st.column_config.NumberColumn("Engagements", format="%d"),
        "viral_index": st.column_config.NumberColumn("Viral idx", format="%.2f"),
    },
)

# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
csv = view.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇  Download filtered data (CSV)",
    data=csv,
    file_name="attention_content_export.csv",
    mime="text/csv",
)

ui.footer()
