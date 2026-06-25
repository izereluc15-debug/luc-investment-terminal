import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Luc Investment Terminal V2", page_icon="📈", layout="wide")

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

DOW_TICKERS = [
    "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
    "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK",
    "MSFT", "NKE", "NVDA", "PG", "SHW", "TRV", "UNH", "V", "VZ", "WMT"
]

ACQUISITIONS = {
    "NVDA": "Mellanox Technologies, Run:ai, Bright Computing.",
    "MSFT": "LinkedIn, GitHub, Activision Blizzard, Nuance Communications.",
    "AMZN": "Whole Foods, MGM Studios, Zoox, Ring, Twitch.",
    "AVGO": "VMware, CA Technologies, Symantec Enterprise Security, Brocade.",
    "AMD": "Xilinx, Pensando.",
    "PLTR": "No major public acquisition history found in this app dataset.",
    "TSM": "Mostly organic growth; no major acquisition-led strategy.",
    "QQQM": "ETF, not a company."
}


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    DEFAULT_PORTFOLIO.to_csv(PORTFOLIO_FILE, index=False)
    return DEFAULT_PORTFOLIO.copy()


def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)


def clean_portfolio(df):
    df = df.copy()
    required = ["Ticker", "Company", "Weight %", "Shares", "Average Cost"]
    for col in required:
        if col not in df.columns:
            df[col] = 0 if col in ["Weight %", "Shares", "Average Cost"] else ""

    df["Ticker"] = df["Ticker"].fillna("").astype(str).str.upper().str.strip()
    df["Company"] = df["Company"].fillna("").astype(str).str.strip()

    for col in ["Weight %", "Shares", "Average Cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df[df["Ticker"] != ""]


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


def number(x):
    try:
        return f"{float(x):.2f}"
    except Exception:
        return "N/A"


@st.cache_data(ttl=300)
def stock_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


@st.cache_data(ttl=300)
def stock_news(ticker):
    try:
        return yf.Ticker(ticker).news
    except Exception:
        return []


@st.cache_data(ttl=600)
def stock_history(ticker, period="1y"):
    try:
        return yf.download(ticker, period=period, auto_adjust=True, progress=False)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_sp500_tickers():
    try:
        table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        return table["Symbol"].str.replace(".", "-", regex=False).tolist()
    except Exception:
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "JPM", "LLY"]


@st.cache_data(ttl=86400)
def calculate_returns(tickers, period):
    results = []

    for ticker in tickers:
        try:
            hist = yf.download(
                ticker,
                period=period,
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if hist is None or hist.empty or "Close" not in hist.columns:
                continue

            close_prices = hist["Close"].dropna()

            if close_prices.empty or len(close_prices) < 2:
                continue

            start_price = float(close_prices.iloc[0])
            current_price = float(close_prices.iloc[-1])

            if start_price <= 0:
                continue

            return_pct = ((current_price - start_price) / start_price) * 100
            info = stock_info(ticker)

            results.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Return %": return_pct,
                "Start Price": start_price,
                "Current Price": current_price
            })

        except Exception:
            continue

    columns = ["Rank", "Ticker", "Company", "Return %", "Start Price", "Current Price"]

    if not results:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(results)
    df = df.sort_values("Return %", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)

    return df


def get_earnings_row(ticker):
    info = stock_info(ticker)

    return {
        "Ticker": ticker,
        "Company": info.get("shortName", ticker),
        "Upcoming Earnings Date": info.get("earningsDate", "N/A"),
        "Previous EPS": number(info.get("trailingEps")),
        "Estimated EPS": number(info.get("forwardEps")),
        "EPS Surprise %": "N/A",
        "Revenue Estimate": big_money(info.get("revenuePerShare")) if info.get("revenuePerShare") else "N/A"
    }


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
        "📰 News & Index Performers",
        "📊 Company Overview",
        "📅 Earnings Calendar",
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
    c4.metric("Unallocated", percent(100 - portfolio["Weight %"].sum()))

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
            "Debt / Equity": number(info.get("debtToEquity")),
            "Forward P/E": number(info.get("forwardPE")),
            "Trailing P/E": number(info.get("trailingPE")),
            "Price / Sales": number(info.get("priceToSalesTrailing12Months")),
            "ROE": percent(info.get("returnOnEquity") * 100 if info.get("returnOnEquity") is not None else None),
            "Free Cash Flow": big_money(info.get("freeCashflow")),
            "Total Revenue": big_money(info.get("totalRevenue"))
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


elif page == "📰 News & Index Performers":
    st.subheader("📰 News & Top Index Performers")

    index_choice = st.selectbox(
        "Choose index",
        ["S&P 500", "Dow Jones"]
    )

    period_label = st.selectbox(
        "Choose performance period",
        ["3 months", "6 months", "9 months", "12 months", "24 months"]
    )

    period_map = {
        "3 months": "3mo",
        "6 months": "6mo",
        "9 months": "9mo",
        "12 months": "1y",
        "24 months": "2y"
    }

    top_n = st.selectbox(
        "Number of top performers",
        [10, 15, 20, 25],
        index=0
    )

    if index_choice == "S&P 500":
        index_tickers = get_sp500_tickers()
    else:
        index_tickers = DOW_TICKERS

    st.info(
        f"Scanning {index_choice} companies over the past {period_label}. "
        "Stocks with missing Yahoo Finance data are skipped."
    )

    performers = calculate_returns(index_tickers, period_map[period_label])

    if performers.empty:
        st.warning(
            "Could not load performer data. Yahoo Finance may be unavailable or rate-limited."
        )
    else:
        top_performers = performers.head(top_n).copy()

        top_performers["Return %"] = top_performers["Return %"].apply(percent)
        top_performers["Start Price"] = top_performers["Start Price"].apply(money)
        top_performers["Current Price"] = top_performers["Current Price"].apply(money)

        st.subheader(f"Top {top_n} {index_choice} performers — past {period_label}")
        st.dataframe(top_performers, use_container_width=True)

        csv = top_performers.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Top Performers CSV",
            data=csv,
            file_name=f"{index_choice.lower().replace(' ', '_')}_{period_label.replace(' ', '_')}_top_performers.csv",
            mime="text/csv"
        )

    st.divider()

    st.subheader("Portfolio News")

    if tickers:
        news_ticker = st.selectbox("Choose ticker for news", tickers)
        news_items = stock_news(news_ticker)

        if news_items:
            for item in news_items[:8]:
                title = item.get("title", "No title")
                publisher = item.get("publisher", "Unknown source")
                link = item.get("link", "")

                st.markdown(f"**{title}**")
                st.caption(publisher)

                if link:
                    st.link_button("Open article", link)

                st.divider()
        else:
            st.info("No news available for this ticker.")
    else:
        st.warning("Add tickers in the Portfolio page first.")


elif page == "📊 Company Overview":
    st.subheader("Company Overview")

    if not tickers:
        st.warning("Add tickers in the Portfolio page first.")
    else:
        selected = st.selectbox("Click / choose a ticker", tickers)
        info = stock_info(selected)

        st.header(info.get("shortName", selected))

        st.write(info.get("longBusinessSummary", "No company description available."))

        c1, c2, c3 = st.columns(3)
        c1.metric("Industry", info.get("industry", "N/A"))
        c2.metric("Sector", info.get("sector", "N/A"))
        c3.metric("Country", info.get("country", "N/A"))

        overview = {
            "Ticker": selected,
            "Company": info.get("shortName", selected),
            "Industry": info.get("industry", "N/A"),
            "Previous Acquisitions": ACQUISITIONS.get(selected, "Not available in Yahoo Finance. Add manually later."),
            "52-Week High": money(info.get("fiftyTwoWeekHigh")),
            "52-Week Low": money(info.get("fiftyTwoWeekLow")),
            "Dividend Rate": money(info.get("dividendRate")),
            "Dividend Yield": percent(info.get("dividendYield") * 100 if info.get("dividendYield") else None),
            "Payout Ratio": percent(info.get("payoutRatio") * 100 if info.get("payoutRatio") else None),
            "Institutional Ownership": percent(info.get("heldPercentInstitutions") * 100 if info.get("heldPercentInstitutions") else None),
            "Insider Ownership": percent(info.get("heldPercentInsiders") * 100 if info.get("heldPercentInsiders") else None),
            "Website": info.get("website", "N/A")
        }

        st.dataframe(pd.DataFrame(overview.items(), columns=["Metric", "Value"]), use_container_width=True)


elif page == "📅 Earnings Calendar":
    st.subheader("Earnings Calendar")

    earnings_rows = []

    for ticker in tickers:
        earnings_rows.append(get_earnings_row(ticker))

    if earnings_rows:
        st.dataframe(pd.DataFrame(earnings_rows), use_container_width=True)
    else:
        st.warning("No portfolio tickers found.")

    st.caption("Some earnings fields may show N/A because free Yahoo Finance data is incomplete for certain tickers.")


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
