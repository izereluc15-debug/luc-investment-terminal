import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path

st.set_page_config(page_title="Luc Investment Terminal", page_icon="📈", layout="wide")

st.title("📈 Luc Investment Terminal")
st.caption("Portfolio dashboard with live stock data, valuation, debt monitoring, scoring, and alerts.")

PORTFOLIO_FILE = Path("src/data/portfolio.csv")

def safe_float(x):
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan

@st.cache_data(ttl=3600)
def fetch_stock_data(tickers):
    rows = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            rows.append({
                "Ticker": ticker,
                "Live Company": info.get("shortName", ticker),
                "Price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "Market Cap": info.get("marketCap"),
                "Forward P/E": info.get("forwardPE"),
                "Trailing P/E": info.get("trailingPE"),
                "PEG": info.get("pegRatio"),
                "Price/Sales": info.get("priceToSalesTrailing12Months"),
                "Revenue Growth": info.get("revenueGrowth"),
                "Earnings Growth": info.get("earningsGrowth"),
                "Profit Margin": info.get("profitMargins"),
                "Free Cash Flow": info.get("freeCashflow"),
                "Total Debt": info.get("totalDebt"),
                "Cash": info.get("totalCash"),
                "Debt/Equity": info.get("debtToEquity"),
                "Sector": info.get("sector"),
            })
        except Exception as e:
            rows.append({"Ticker": ticker, "Live Company": ticker, "Error": str(e)})
    return pd.DataFrame(rows)

def score_revenue_growth(x):
    x = safe_float(x)
    if pd.isna(x): return 8
    if x >= 0.30: return 20
    if x >= 0.20: return 17
    if x >= 0.10: return 13
    if x >= 0.00: return 8
    return 2

def score_earnings_growth(x, margin):
    x = safe_float(x)
    margin = safe_float(margin)
    if pd.notna(x):
        if x >= 0.30: return 20
        if x >= 0.20: return 17
        if x >= 0.10: return 13
        if x >= 0.00: return 8
        return 2
    if pd.notna(margin):
        if margin >= 0.30: return 18
        if margin >= 0.20: return 15
        if margin >= 0.10: return 12
        if margin >= 0.00: return 7
        return 2
    return 8

def score_fcf(x):
    x = safe_float(x)
    if pd.isna(x): return 6
    if x > 10_000_000_000: return 15
    if x > 1_000_000_000: return 12
    if x > 0: return 9
    return 3

def score_valuation(pe, peg, ps):
    pe = safe_float(pe)
    peg = safe_float(peg)
    ps = safe_float(ps)
    if pd.notna(peg):
        if peg < 1: return 15
        if peg < 1.5: return 13
        if peg < 2.5: return 9
        return 5
    if pd.notna(pe):
        if pe < 20: return 13
        if pe < 35: return 10
        if pe < 60: return 7
        return 4
    if pd.notna(ps):
        if ps < 5: return 10
        if ps < 10: return 7
        return 4
    return 6

def score_debt(debt, cash, debt_equity):
    debt = safe_float(debt)
    cash = safe_float(cash)
    debt_equity = safe_float(debt_equity)
    if pd.notna(debt) and pd.notna(cash):
        if debt <= cash: return 10
        if debt <= cash * 2: return 7
        return 3
    if pd.notna(debt_equity):
        if debt_equity < 50: return 9
        if debt_equity < 100: return 6
        return 3
    return 6

def rating(score):
    if score >= 95: return "🟢 Exceptional"
    if score >= 90: return "🟢 Strong"
    if score >= 80: return "🟢 Good"
    if score >= 70: return "🟡 Hold"
    if score >= 60: return "🟠 Watch"
    return "🔴 High Risk"

def add_scores(df):
    moat = {"NVDA":10,"TSM":10,"AVGO":10,"MSFT":10,"AMD":8,"AMZN":10,"PLTR":9,"RKLB":7,"TEM":7,"CRWV":8,"QQQM":10}
    management = {"NVDA":5,"TSM":5,"AVGO":5,"MSFT":5,"AMD":5,"AMZN":5,"PLTR":5,"RKLB":5,"TEM":4,"CRWV":4,"QQQM":5}
    market = {"NVDA":5,"TSM":5,"AVGO":5,"MSFT":5,"AMD":5,"AMZN":5,"PLTR":5,"RKLB":5,"TEM":5,"CRWV":5,"QQQM":5}

    rows = []
    for _, r in df.iterrows():
        t = r["Ticker"]
        rev = score_revenue_growth(r.get("Revenue Growth"))
        earn = score_earnings_growth(r.get("Earnings Growth"), r.get("Profit Margin"))
        fcf = score_fcf(r.get("Free Cash Flow"))
        val = score_valuation(r.get("Forward P/E"), r.get("PEG"), r.get("Price/Sales"))
        debt = score_debt(r.get("Total Debt"), r.get("Cash"), r.get("Debt/Equity"))
        total = min(rev + earn + fcf + val + debt + moat.get(t,7) + management.get(t,4) + market.get(t,4), 100)
        rows.append({
            "Ticker": t,
            "Revenue Score /20": rev,
            "Earnings Score /20": earn,
            "FCF Score /15": fcf,
            "Valuation Score /15": val,
            "Debt Score /10": debt,
            "Moat /10": moat.get(t,7),
            "Management /5": management.get(t,4),
            "Market Opportunity /5": market.get(t,4),
            "Total Score /100": total,
            "Rating": rating(total),
        })
    return df.merge(pd.DataFrame(rows), on="Ticker", how="left")

try:
    if not PORTFOLIO_FILE.exists():
        st.error("Missing file: src/data/portfolio.csv")
        st.stop()

    portfolio = pd.read_csv(PORTFOLIO_FILE)
    portfolio["Ticker"] = portfolio["Ticker"].astype(str).str.upper().str.strip()

    with st.sidebar:
        st.header("Settings")
        portfolio_value = st.number_input("Portfolio value ($)", min_value=0.0, value=2500.0, step=100.0)
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Fetching live market data..."):
        live = fetch_stock_data(portfolio["Ticker"].tolist())

    df = portfolio.merge(live, on="Ticker", how="left")
    df = add_scores(df)
    df["Dollar Allocation"] = portfolio_value * df["Weight"] / 100
    df["Net Debt"] = df["Total Debt"] - df["Cash"]

    weighted_score = (df["Total Score /100"] * df["Weight"]).sum() / max(df["Weight"].sum(), 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio Value", f"${portfolio_value:,.0f}")
    c2.metric("Holdings", len(df))
    c3.metric("Total Weight", f"{df['Weight'].sum():.1f}%")
    c4.metric("Weighted Score", f"{weighted_score:.1f}/100")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Portfolio",
        "Scorecard",
        "Debt & Valuation",
        "Market Risk",
        "Alerts"
    ])

    with tab1:
        st.subheader("Portfolio Overview")
        st.dataframe(
            df[["Ticker","Company","Weight","Dollar Allocation","Price","Revenue Growth","Forward P/E","PEG","Total Score /100","Rating"]],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("100-Point Company Scorecard")
        st.dataframe(
            df[["Ticker","Company","Revenue Score /20","Earnings Score /20","FCF Score /15","Valuation Score /15","Debt Score /10","Moat /10","Management /5","Market Opportunity /5","Total Score /100","Rating"]].sort_values("Total Score /100", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        st.subheader("Debt & Valuation Monitor")
        st.dataframe(
            df[["Ticker","Company","Market Cap","Forward P/E","Trailing P/E","PEG","Price/Sales","Total Debt","Cash","Net Debt","Debt Score /10","Valuation Score /15"]],
            use_container_width=True,
            hide_index=True
        )

    with tab4:
        st.subheader("Market Crisis Dashboard")
        crisis = pd.DataFrame([
            ["Market Valuations", 20, 13, "AI/growth valuations are elevated"],
            ["Interest Rates", 15, 9, "Watch Fed policy and yields"],
            ["Credit Markets", 15, 13, "No major stress signal"],
            ["Corporate Earnings", 15, 14, "Mega-cap earnings remain strong"],
            ["Unemployment", 10, 8, "Labor market remains important"],
            ["Consumer Spending", 10, 7, "Watch slowdown signs"],
            ["Yield Curve", 10, 6, "Monitor inversion/re-steepening"],
            ["Speculation", 5, 3, "AI optimism is elevated"],
        ], columns=["Indicator", "Max Points", "Current Score", "Comment"])
        total = crisis["Current Score"].sum()
        st.metric("Market Health Score", f"{total}/100")
        st.metric("Estimated Crisis Risk", f"{100-total}%")
        st.dataframe(crisis, use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("Smart Alerts")
        alerts = []
        for _, r in df.iterrows():
            if r["Valuation Score /15"] <= 5:
                alerts.append([r["Ticker"], "Valuation", "🔴 Expensive valuation"])
            if r["Debt Score /10"] <= 3:
                alerts.append([r["Ticker"], "Debt", "🔴 Heavy debt risk"])
            if safe_float(r.get("Free Cash Flow")) < 0:
                alerts.append([r["Ticker"], "Cash Flow", "🟡 Negative free cash flow"])
            if r["Total Score /100"] < 70:
                alerts.append([r["Ticker"], "Quality", "🟠 Speculative / watch closely"])

        if alerts:
            st.dataframe(pd.DataFrame(alerts, columns=["Ticker","Type","Alert"]), use_container_width=True, hide_index=True)
        else:
            st.success("No major alerts under the current rules.")

    st.caption("Educational tool only. Verify important numbers with official company filings.")

except Exception as e:
    st.error("The app crashed while loading.")
    st.exception(e)
