import streamlit as st
import pandas as pd
from src.data_fetcher import fetch_stock_data
from src.models.scoring import add_scores
from src.models.alerts import generate_alerts

st.title("🧠 Smart Alerts")

portfolio = pd.read_csv("src/data/portfolio.csv")
data = fetch_stock_data(portfolio["Ticker"].tolist())
df = add_scores(portfolio.merge(data, on="Ticker", how="left", suffixes=("", "_Live")))
alerts = generate_alerts(df)

if alerts.empty:
    st.success("No major alerts under the current rules.")
else:
    st.dataframe(alerts, use_container_width=True, hide_index=True)