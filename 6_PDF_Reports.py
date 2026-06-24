import streamlit as st
import pandas as pd
from src.models.risk import crisis_dashboard

st.title("🚨 Macro & Crisis Dashboard")

crisis = crisis_dashboard()
total_score = crisis["Current Score"].sum()
crisis_risk = max(0, 100 - total_score)

c1, c2, c3 = st.columns(3)
c1.metric("Market Health Score", f"{total_score}/100")
c2.metric("Crisis Risk Estimate", f"{crisis_risk}%")
c3.metric("Status", "🟡 Watch / Not Panic")

st.dataframe(crisis, use_container_width=True, hide_index=True)

st.caption("This is currently a rules-based macro template. Future versions can connect to FRED and other APIs.")