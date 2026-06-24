import streamlit as st
import pandas as pd
from src.data_fetcher import fetch_stock_data
from src.models.scoring import add_scores

st.title("🤖 AI Sector Monitor")

portfolio = pd.read_csv("src/data/portfolio.csv")
data = fetch_stock_data(portfolio["Ticker"].tolist())
df = add_scores(portfolio.merge(data, on="Ticker", how="left", suffixes=("", "_Live")))

ai_df = df.sort_values("AI Exposure /10", ascending=False)
st.dataframe(
    ai_df[["Ticker","Company","Weight","AI Exposure /10","Revenue Growth","Free Cash Flow","Total Score /100","Investment Rating"]],
    use_container_width=True,
    hide_index=True
)

st.caption("AI exposure scores are qualitative starter scores stored in `src/data/quality_scores.json`.")