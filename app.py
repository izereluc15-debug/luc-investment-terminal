# app.py
import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Luc Investment Terminal V2",
    page_icon="📈",
    layout="wide"
)

DATA_DIR = "data"
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.csv")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_PORTFOLIO = pd.DataFrame({
    "Ticker": ["NVDA", "TSM", "AVGO", "MSFT", "AMD", "AMZN", "PLTR", "RKLB", "TEM", "CRWV", "QQQM"],
    "Company": ["NVIDIA", "TSMC", "Broadcom", "Microsoft", "AMD", "Amazon", "Palantir", "Rocket Lab", "Tempus AI", "CoreWeave", "Invesco NASDAQ 100 ETF"],
    "Weight %": [22, 20, 13, 13, 10, 10, 5, 2.3, 2.3, 2.4, 0],
    "Shares": [0.0] * 11,
    "Average Cost": [0.0] * 11
})


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    DEFAULT_PORTFOLIO.to_csv(PORTFOLIO_FILE, index=False)
    return DEFAULT_PORTFOLIO.copy()


def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)


def clean_portfolio(df):
    df = df.copy()
    df["Ticker"] = df["Ticker"].fillna("").astype(str).str.upper().str.strip()
    df["Company"] = df["Company"].fillna("").astype(str).str.strip()
    for col in ["Weight %", "Shares", "Average Cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df[df["Ticker"] != ""]
    return df


@st.cache_data(ttl=300)
def stock_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


@st.cache_data(ttl=300)
def stock_history(ticker, period="1y"):
    try:
        return yf.download(ticker, period=period, auto_adjust=True, progress=False)
    except Exception:
        return pd.DataFrame()


def money(x):
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return "N/A"


def big_money(x):
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return "N/A"


def percent(x):
    try:
        return f"{float(x):.2f}%"
    except Exception:
        return "N/A"


if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

st.sidebar.title("📈 Luc Terminal V2")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "💼 Portfolio",
        "📊 Live Market",
        "🏦 Fundamentals",
        "🔎 Company Details",
        "📈 Simulator",
        "⚙️ Settings"
    ]
)

portfolio = clean_portfolio(st.session_state.portfolio)
tickers = portfolio["Ticker"].tolist()

st.title("📈 Luc Investment Terminal V2")

if page == "🏠 Dashboard":
    st.subheader("Portfolio Dashboard")

    total_value = st.number_input("Portfolio value ($)", min_value=0.0, value=1500.0, step=100.0)

    portfolio["Dollar Amount"] = portfolio["Weight %"] / 100 * total_value

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio Value", money(total_value))
    c2.metric("Assets", len(portfolio))
    c3.metric("Total Weight", percent(portfolio["Weight %"].sum()))
    c4.metric("Cash / Unallocated", percent(100 - portfolio["Weight %"].sum()))

    st.dataframe(portfolio, use_container_width=True)

    if not portfolio.empty:
        st.bar_chart(portfolio.set_index("Ticker")["Dollar Amount"])


elif page == "💼 Portfolio":
    st.subheader("Portfolio Builder")

    edited = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor"
    )

    edited = clean_portfolio(edited)
    st.session_state.portfolio = edited
    save_portfolio(edited)

    st.success("Portfolio saved automatically.")

    st.dataframe(edited, use_container_width=True)

    csv = edited.to_csv(index=False).encode("utf-8")
    st.download_button("Download Portfolio CSV", csv, "portfolio.csv", "text/csv")


elif page == "📊 Live Market":
    st.subheader("Live Market")

    rows = []

    for ticker in tickers:
        info = stock_info(ticker)
        price = info.get("regularMarketPrice")
        previous = info.get("previousClose")

        change = None
        if price is not None and previous not in [None, 0]:
            change = ((price - previous) / previous) * 100

        rows.append({
            "Ticker": ticker,
            "Company": info.get("shortName", ticker),
            "Price": money(price),
            "Previous Close": money(previous),
            "Daily Change": percent(change),
            "Market Cap": big_money(info.get("marketCap"))
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    if tickers:
        selected = st.selectbox("Select ticker", tickers)
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)
        hist = stock_history(selected, period)

        if not hist.empty and "Close" in hist.columns:
            st.line_chart(hist["Close"])


elif page == "🏦 Fundamentals":
    st.subheader("Fundamental Analysis")

    rows = []

    for ticker in tickers:
        info = stock_info(ticker)

        rows.append({
            "Ticker": ticker,
            "Company": info.get("shortName", ticker),
            "Market Cap": big_money(info.get("marketCap")),
            "Revenue Growth": percent(info.get("revenueGrowth") * 100 if info.get("revenueGrowth") is not None else None),
            "Earnings Growth": percent(info.get("earningsGrowth") * 100 if info.get("earningsGrowth") is not None else None),
            "Profit Margin": percent(info.get("profitMargins") * 100 if info.get("profitMargins") is not None else None),
            "Gross Margin": percent(info.get("grossMargins") * 100 if info.get("grossMargins") is not None else None),
            "Debt / Equity": info.get("debtToEquity"),
            "Forward P/E": info.get("forwardPE"),
            "Trailing P/E": info.get("trailingPE"),
            "Price / Sales": info.get("priceToSalesTrailing12Months"),
            "ROE": percent(info.get("returnOnEquity") * 100 if info.get("returnOnEquity") is not None else None),
            "Free Cash Flow": big_money(info.get("freeCashflow")),
            "Total Revenue": big_money(info.get("totalRevenue"))
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


elif page == "🔎 Company Details":
    st.subheader("Company Details")

    if tickers:
        selected = st.selectbox("Choose company", tickers)
        info = stock_info(selected)

        st.header(info.get("shortName", selected))
        st.write(info.get("longBusinessSummary", "No company description available."))

        c1, c2, c3 = st.columns(3)
        c1.metric("Sector", info.get("sector", "N/A"))
        c2.metric("Industry", info.get("industry", "N/A"))
        c3.metric("Employees", info.get("fullTimeEmployees", "N/A"))

        details = {
            "Ticker": selected,
            "Website": info.get("website"),
            "Country": info.get("country"),
            "City": info.get("city"),
            "Market Cap": big_money(info.get("marketCap")),
            "Enterprise Value": big_money(info.get("enterpriseValue")),
            "52 Week High": money(info.get("fiftyTwoWeekHigh")),
            "52 Week Low": money(info.get("fiftyTwoWeekLow")),
            "Dividend Yield": percent(info.get("dividendYield") * 100 if info.get("dividendYield") else None),
            "Analyst Target Price": money(info.get("targetMeanPrice"))
        }

        st.dataframe(pd.DataFrame(details.items(), columns=["Metric", "Value"]), use_container_width=True)


elif page == "📈 Simulator":
    st.subheader("Portfolio Growth Simulator")

    initial = st.number_input("Initial investment ($)", min_value=0.0, value=1500.0, step=100.0)
    monthly = st.number_input("Monthly contribution ($)", min_value=0.0, value=100.0, step=50.0)
    annual_return = st.number_input("Expected annual return (%)", min_value=0.0, value=10.0, step=0.5)
    years = st.slider("Years", 1, 40, 10)

    monthly_return = (1 + annual_return / 100) ** (1 / 12) - 1
    balance = initial
    records = []

    for year in range(1, years + 1):
        for month in range(12):
            balance = balance * (1 + monthly_return) + monthly
        records.append({"Year": year, "Projected Value": balance})

    sim_df = pd.DataFrame(records)

    st.metric("Projected Final Value", money(balance))
    st.line_chart(sim_df.set_index("Year")["Projected Value"])
    st.dataframe(sim_df, use_container_width=True)


elif page == "⚙️ Settings":
    st.subheader("Settings")

    st.write("Portfolio data is saved in:")

    st.code(PORTFOLIO_FILE)

    if st.button("Reset portfolio to default"):
        st.session_state.portfolio = DEFAULT_PORTFOLIO.copy()
        save_portfolio(DEFAULT_PORTFOLIO)
        st.success("Portfolio reset successfully. Refresh the page.")

    uploaded = st.file_uploader("Import portfolio CSV", type=["csv"])

    if uploaded is not None:
        imported = pd.read_csv(uploaded)
        imported = clean_portfolio(imported)
        st.session_state.portfolio = imported
        save_portfolio(imported)
        st.success("Imported and saved successfully.")
