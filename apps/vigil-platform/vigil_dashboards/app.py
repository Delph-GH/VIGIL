"""
apps/vigil-platform/vigil_dashboards/app.py

Vigil dashboard entry point.

Run:  streamlit run apps/vigil-platform/vigil_dashboards/app.py
Pages in pages/ appear automatically in the sidebar.
"""

import sys
from pathlib import Path

import streamlit as st

_here = Path(__file__).resolve().parent
_root = _here.parents[2]
for _p in (_root / "packages", _here):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from utils.backend import get_backend  # noqa: E402

st.set_page_config(page_title="Vigil Intelligence", page_icon="🗳️", layout="wide")


@st.cache_resource
def backend():
    return get_backend()


@st.cache_data(ttl=600)
def load_overview(days: int):
    b = backend()
    articles = b.fetch_recent_articles(days=days)
    analytics = b.analyze_articles(articles)
    sentiment = b.analyze_sentiment(articles)
    signal = b.compute_signal_noise(articles)
    sources = sorted({a.source_name for a in articles})
    return len(articles), analytics, sentiment, signal, sources


st.title("🗳️ Vigil Intelligence")
st.markdown("**French political intelligence**")

if backend().is_sample_data:
    st.warning(
        "Sample data: no article database is connected yet, so these figures "
        "are computed from synthetic articles. The analytics code itself is real."
    )

days = st.sidebar.slider("Look-back window (days)", 1, 30, 7)
n_articles, analytics, sentiment, signal, sources = load_overview(days)

avg = lambda key: (sum(a[key] for a in analytics) / len(analytics)) if analytics else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Articles analysed", n_articles)
c2.metric("Avg trust", f"{avg('trust'):.2f}")
c3.metric("Avg salience", f"{avg('salience'):.2f}")
c4.metric("Signal ratio", f"{signal['signal_ratio']:.0f}%")

st.markdown("---")
left, right = st.columns(2)
with left:
    st.subheader("Sentiment split (%)")
    st.bar_chart(sentiment)
with right:
    st.subheader("Average trust by source")
    by_source = {}
    for a in analytics:
        src = a.get("metadata", {}).get("source")
        if src:
            by_source.setdefault(src, []).append(a["trust"])
    st.bar_chart({s: sum(v) / len(v) for s, v in by_source.items()})

st.caption(f"Sources: {', '.join(sources)}")
