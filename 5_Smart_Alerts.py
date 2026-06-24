import streamlit as st
import pandas as pd
from src.data_fetcher import fetch_stock_data
from src.models.scoring import add_scores
from src.models.valuation import valuation_signal

st.title("⚖️ Valuation & Debt Monitor")

portfolio = pd.read_csv("src/data/portfolio.csv")
data = fetch_stock_data(portfolio["Ticker"].tolist())
df = add_scores(portfolio.merge(data, on="Ticker", how="left", suffixes=("", "_Live")))
df["Net Debt"] = df["Total Debt"] - df["Cash"]
df["Valuation Signal"] = df.apply(valuation_signal, axis=1)

st.subheader("Valuation")
st.dataframe(
    df[["Ticker","Company","Price","Market Cap","Trailing P/E","Forward P/E","PEG","Price/Sales","Revenue Growth","Valuation Score /15","Valuation Signal"]],
    use_container_width=True,
    hide_index=True
)

st.subheader("Debt")
df["Debt Warning"] = df["Debt Score /10"].apply(lambda x: "🔴 Heavy" if x <= 3 else "🟡 Watch" if x <= 7 else "🟢 Strong")
st.dataframe(
    df[["Ticker","Company","Total Debt","Cash","Net Debt","Debt/Equity","Debt Score /10","Debt Warning"]],
    use_container_width=True,
    hide_index=True
)