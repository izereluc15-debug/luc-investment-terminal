
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import math

st.set_page_config(
    page_title="Luc's Investment Terminal",
    page_icon="📈",
    layout="wide"
)

DEFAULT_PORTFOLIO = {
    "NVDA": {"name": "NVIDIA", "weight": 22},
    "TSM": {"name": "TSMC", "weight": 20},
    "AVGO": {"name": "Broadcom", "weight": 13},
    "MSFT": {"name": "Microsoft", "weight": 13},
    "AMD": {"name": "AMD", "weight": 10},
    "AMZN": {"name": "Amazon", "weight": 10},
    "PLTR": {"name": "Palantir", "weight": 5},
    "RKLB": {"name": "Rocket Lab", "weight": 2.3},
    "TEM": {"name": "Tempus AI", "weight": 2.3},
    "CRWV": {"name": "CoreWeave", "weight": 2.4},
    "QQQM": {"name": "Invesco NASDAQ 100 ETF", "weight": 0},
}

QUALITATIVE = {
    "NVDA": {"moat": 10, "management": 5, "tam": 5},
    "TSM": {"moat": 10, "management": 5, "tam": 5},
    "AVGO": {"moat": 10, "management": 5, "tam": 5},
    "MSFT": {"moat": 10, "management": 5, "tam": 5},
    "AMD": {"moat": 8, "management": 5, "tam": 5},
    "AMZN": {"moat": 10, "management": 5, "tam": 5},
    "PLTR": {"moat": 9, "management": 5, "tam": 5},
    "RKLB": {"moat": 7, "management": 5, "tam": 5},
    "TEM": {"moat": 7, "management": 4, "tam": 5},
    "CRWV": {"moat": 8, "management": 4, "tam": 5},
    "QQQM": {"moat": 10, "management": 5, "tam": 5},
}

st.title("📈 Luc's Investment Terminal")
st.caption("Self-updating long-term portfolio dashboard: quality, valuation, debt, AI exposure, and crisis signals.")

with st.sidebar:
    st.header("Settings")
    portfolio_value = st.number_input("Portfolio value ($)", min_value=0.0, value=2000.0, step=100.0)
    st.caption("Edit tickers and weights below. Format: TICKER,WEIGHT")
    tickers_input = st.text_area(
        "Portfolio",
        height=260,
        value="\n".join([f"{ticker},{data['weight']}" for ticker, data in DEFAULT_PORTFOLIO.items()])
    )
    refresh = st.button("Refresh data")

def parse_portfolio(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        ticker, weight = line.split(",", 1)
        try:
            rows.append({"Ticker": ticker.strip().upper(), "Weight %": float(weight.strip())})
        except:
            pass
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def fetch_one(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose")
    one_year_return = None
    if hist is not None and len(hist) > 5 and "Close" in hist:
        first = hist["Close"].iloc[0]
        last = hist["Close"].iloc[-1]
        if first:
            one_year_return = (last / first) - 1

    return {
        "Ticker": ticker,
        "Company": info.get("shortName", ticker),
        "Price": price,
        "Previous Close": prev_close,
        "1Y Return": one_year_return,
        "Market Cap": info.get("marketCap"),
        "Trailing P/E": info.get("trailingPE"),
        "Forward P/E": info.get("forwardPE"),
        "PEG": info.get("pegRatio"),
        "Price/Sales": info.get("priceToSalesTrailing12Months"),
        "Revenue Growth": info.get("revenueGrowth"),
        "Earnings Growth": info.get("earningsGrowth"),
        "Profit Margin": info.get("profitMargins"),
        "Operating Margin": info.get("operatingMargins"),
        "Free Cash Flow": info.get("freeCashflow"),
        "Total Debt": info.get("totalDebt"),
        "Cash": info.get("totalCash"),
        "Debt/Equity": info.get("debtToEquity"),
        "ROE": info.get("returnOnEquity"),
        "Beta": info.get("beta"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
    }

@st.cache_data(ttl=3600)
def fetch_all(tickers):
    output = []
    for ticker in tickers:
        try:
            output.append(fetch_one(ticker))
        except Exception as e:
            output.append({"Ticker": ticker, "Company": ticker, "Error": str(e)})
    return pd.DataFrame(output)

def score_revenue_growth(x):
    if pd.isna(x): return 8
    if x >= 0.30: return 20
    if x >= 0.20: return 17
    if x >= 0.10: return 13
    if x >= 0.00: return 8
    return 2

def score_earnings_growth(x, margin):
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
    if pd.isna(x): return 6
    if x > 10_000_000_000: return 15
    if x > 1_000_000_000: return 12
    if x > 0: return 9
    return 3

def score_valuation(pe, peg, ps):
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
    if pd.notna(debt) and pd.notna(cash):
        if debt <= cash: return 10
        if debt <= cash * 2: return 7
        return 3
    if pd.notna(debt_equity):
        if debt_equity < 50: return 9
        if debt_equity < 100: return 6
        return 3
    return 6

def calculate_scores(df):
    rows = []
    for _, r in df.iterrows():
        t = r["Ticker"]
        q = QUALITATIVE.get(t, {"moat": 7, "management": 4, "tam": 4})
        rev = score_revenue_growth(r.get("Revenue Growth"))
        earn = score_earnings_growth(r.get("Earnings Growth"), r.get("Profit Margin"))
        fcf = score_fcf(r.get("Free Cash Flow"))
        val = score_valuation(r.get("Forward P/E"), r.get("PEG"), r.get("Price/Sales"))
        debt = score_debt(r.get("Total Debt"), r.get("Cash"), r.get("Debt/Equity"))
        total = rev + earn + fcf + val + debt + q["moat"] + q["management"] + q["tam"]
        rows.append({
            "Ticker": t,
            "Revenue Growth Score /20": rev,
            "Earnings Score /20": earn,
            "FCF Score /15": fcf,
            "Valuation Score /15": val,
            "Debt Score /10": debt,
            "Moat /10": q["moat"],
            "Management /5": q["management"],
            "Market Opportunity /5": q["tam"],
            "Total Score /100": min(total, 100),
        })
    return pd.DataFrame(rows)

def format_large(x):
    if pd.isna(x): return "N/A"
    try:
        x = float(x)
        sign = "-" if x < 0 else ""
        x = abs(x)
        if x >= 1e12: return f"{sign}${x/1e12:.2f}T"
        if x >= 1e9: return f"{sign}${x/1e9:.2f}B"
        if x >= 1e6: return f"{sign}${x/1e6:.2f}M"
        return f"{sign}${x:,.0f}"
    except:
        return "N/A"

def status_from_score(score):
    if score >= 90: return "🟢 Elite"
    if score >= 80: return "🟢 High Quality"
    if score >= 70: return "🟡 Good / Watch"
    if score >= 60: return "🟠 Speculative"
    return "🔴 High Risk"

portfolio = parse_portfolio(tickers_input)
if refresh:
    st.cache_data.clear()

if portfolio.empty:
    st.warning("Please enter tickers and weights in the sidebar.")
    st.stop()

with st.spinner("Fetching live financial data..."):
    live = fetch_all(portfolio["Ticker"].tolist())

df = portfolio.merge(live, on="Ticker", how="left")
scores = calculate_scores(df)
df = df.merge(scores, on="Ticker", how="left")
df["Dollar Allocation"] = portfolio_value * df["Weight %"] / 100
df["Status"] = df["Total Score /100"].apply(status_from_score)
df["Net Debt"] = df["Total Debt"] - df["Cash"]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Terminal",
    "📊 Company Scorecard",
    "⚖️ Valuation & Debt",
    "🚨 Crisis Dashboard",
    "🧠 Alerts"
])

with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Portfolio Value", f"${portfolio_value:,.0f}")
    c2.metric("Holdings", len(df))
    c3.metric("Total Weight", f"{df['Weight %'].sum():.1f}%")
    c4.metric("Weighted Score", f"{(df['Total Score /100'] * df['Weight %']).sum() / max(df['Weight %'].sum(),1):.1f}/100")
    tech_weight = df[df["Sector"].fillna("").str.contains("Technology|Communication|Consumer Cyclical", case=False, regex=True)]["Weight %"].sum()
    c5.metric("Tech/Growth Exposure", f"{tech_weight:.1f}%")

    st.subheader("Portfolio Holdings")
    overview = df[[
        "Ticker","Company","Weight %","Dollar Allocation","Price","1Y Return",
        "Revenue Growth","Forward P/E","PEG","Free Cash Flow","Net Debt","Total Score /100","Status"
    ]].copy()
    st.dataframe(overview, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("100-Point Company Scoring Model")
    st.dataframe(
        df[[
            "Ticker","Company",
            "Revenue Growth Score /20","Earnings Score /20","FCF Score /15",
            "Valuation Score /15","Debt Score /10","Moat /10",
            "Management /5","Market Opportunity /5","Total Score /100","Status"
        ]].sort_values("Total Score /100", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.caption("Qualitative moat, management, and market opportunity scores are starter assumptions. You can edit them in app.py.")

with tab3:
    st.subheader("Valuation Monitor")
    valuation = df[[
        "Ticker","Company","Market Cap","Trailing P/E","Forward P/E","PEG",
        "Price/Sales","Revenue Growth","Earnings Growth","Profit Margin","ROE"
    ]].copy()
    st.dataframe(valuation, use_container_width=True, hide_index=True)

    st.subheader("Debt Monitor")
    debt = df[["Ticker","Company","Total Debt","Cash","Net Debt","Debt/Equity","Debt Score /10"]].copy()
    debt["Debt Warning"] = debt.apply(
        lambda r: "🔴 Heavy debt risk" if pd.notna(r["Debt Score /10"]) and r["Debt Score /10"] <= 3
        else "🟡 Watch" if pd.notna(r["Debt Score /10"]) and r["Debt Score /10"] <= 7
        else "🟢 Strong",
        axis=1
    )
    st.dataframe(debt, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Market Crisis Probability Dashboard")
    st.caption("This version includes a starter manual dashboard. Later, connect FRED/Alpha Vantage APIs for automatic macro data.")

    crisis = pd.DataFrame([
        ["Market Valuations", 20, 13, "Elevated valuations, especially AI/growth"],
        ["Interest Rates", 15, 9, "Watch Fed policy and bond yields"],
        ["Credit Markets", 15, 13, "Credit spreads normal unless widening"],
        ["Corporate Earnings", 15, 14, "AI and mega-cap earnings remain strong"],
        ["Unemployment", 10, 8, "Labor market still important to monitor"],
        ["Consumer Spending", 10, 7, "Watch retail sales and delinquencies"],
        ["Yield Curve", 10, 6, "Inversion or re-steepening can warn of stress"],
        ["Speculation", 5, 3, "AI enthusiasm elevated"],
    ], columns=["Indicator","Max Points","Current Score","Comment"])

    total_score = crisis["Current Score"].sum()
    crisis_probability = max(0, min(100, 100 - total_score))

    c1, c2, c3 = st.columns(3)
    c1.metric("Market Health Score", f"{total_score}/100")
    c2.metric("Crisis Risk Estimate", f"{crisis_probability}%")
    c3.metric("Market Status", "🟡 Watch / Not Panic")

    st.dataframe(crisis, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Portfolio Alerts")
    alerts = []

    for _, r in df.iterrows():
        ticker = r["Ticker"]
        if pd.notna(r.get("Valuation Score /15")) and r["Valuation Score /15"] <= 5:
            alerts.append([ticker, "Valuation", "🔴 Expensive valuation; needs strong growth to justify price."])
        if pd.notna(r.get("Debt Score /10")) and r["Debt Score /10"] <= 3:
            alerts.append([ticker, "Debt", "🔴 Heavy debt or weak net cash position."])
        if pd.notna(r.get("Free Cash Flow")) and r["Free Cash Flow"] < 0:
            alerts.append([ticker, "Cash Flow", "🟡 Negative free cash flow; monitor funding needs."])
        if pd.notna(r.get("Revenue Growth")) and r["Revenue Growth"] < 0.10:
            alerts.append([ticker, "Growth", "🟡 Revenue growth below 10%; monitor slowdown."])

    if alerts:
        st.dataframe(pd.DataFrame(alerts, columns=["Ticker","Alert Type","Message"]), use_container_width=True, hide_index=True)
    else:
        st.success("No major alerts based on the current rules.")

st.divider()
st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    "Educational tool only. Verify important figures with official filings before investing."
)
