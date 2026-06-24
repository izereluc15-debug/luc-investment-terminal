import streamlit as st
import pandas as pd
from src.data_fetcher import fetch_stock_data
from src.models.scoring import add_scores

st.title("📊 Company Scorecard")

portfolio = pd.read_csv("src/data/portfolio.csv")
data = fetch_stock_data(portfolio["Ticker"].tolist())
df = add_scores(portfolio.merge(data, on="Ticker", how="left", suffixes=("", "_Live")))

st.dataframe(
    df[[
        "Ticker","Company","Revenue Score /20","Earnings Score /20","FCF Score /15",
        "Valuation Score /15","Debt Score /10","Moat /10","Management /5",
        "Market Opportunity /5","AI Exposure /10","Total Score /100","Investment Rating"
    ]].sort_values("Total Score /100", ascending=False),
    use_container_width=True,
    hide_index=True
)