import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Luc Investment Terminal", page_icon="📈", layout="wide")

st.title("📈 Luc Investment Terminal")
st.caption("Dynamic portfolio builder, live tickers, and fundamental analysis dashboard.")

default_portfolio = pd.DataFrame({
    "Ticker": ["NVDA", "TSM", "AVGO", "MSFT", "AMD", "AMZN", "PLTR", "RKLB", "TEM", "CRWV", "QQQM"],
    "Company": ["NVIDIA", "TSMC", "Broadcom", "Microsoft", "AMD", "Amazon", "Palantir", "Rocket Lab", "Tempus AI", "CoreWeave", "Invesco NASDAQ 100 ETF"],
    "Weight %": [22, 20, 13, 13, 10, 10, 5, 2.3, 2.3, 2.4, 0]
})

if "portfolio" not in st.session_state:
    st.session_state.portfolio = default_portfolio.copy()


def clean_portfolio(df):
    df = df.copy()
    df = df.dropna(subset=["Ticker"])
    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
    df["Company"] = df["Company"].fillna("").astype(str).str.strip()
    df["Weight %"] = pd.to_numeric(df["Weight %"], errors="coerce").fillna(0)
    df = df[df["Ticker"] != ""]
    return df


def money(x):
    try:
        return f"${float(x):,.2f}"
    except:
        return "N/A"


def money_big(x):
    try:
        return f"${float(x):,.0f}"
    except:
        return "N/A"


def percent(x):
    try:
        return f"{float(x):.2f}%"
    except:
        return "N/A"


def number(x):
    try:
        return f"{float(x):.2f}"
    except:
        return "N/A"


@st.cache_data(ttl=300)
def get_stock_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except:
        return {}


@st.cache_data(ttl=300)
def get_price_history(ticker, period):
    try:
        return yf.download(ticker, period=period, progress=False, auto_adjust=True)
    except:
        return pd.DataFrame()


tab1, tab2, tab3 = st.tabs([
    "💼 Portfolio Builder",
    "📊 Live Tickers",
    "🏦 Fundamental Analysis"
])

with tab1:
    st.subheader("💼 Portfolio Builder")

    total_value = st.number_input("Total portfolio value ($)", min_value=0.0, value=1500.0, step=100.0)

    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor"
    )

    edited_df = clean_portfolio(edited_df)
    st.session_state.portfolio = edited_df

    edited_df["Dollar Amount"] = edited_df["Weight %"] / 100 * total_value
    total_weight = edited_df["Weight %"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", money(total_value))
    col2.metric("Total Weight", percent(total_weight))
    col3.metric("Number of Assets", len(edited_df))

    if round(total_weight, 2) != 100:
        st.warning(f"Your portfolio weight is {total_weight:.2f}%. It should equal 100%.")
    else:
        st.success("Portfolio weights total 100%.")

    display_portfolio = edited_df.copy()
    display_portfolio["Weight %"] = display_portfolio["Weight %"].apply(percent)
    display_portfolio["Dollar Amount"] = display_portfolio["Dollar Amount"].apply(money)

    st.dataframe(display_portfolio, use_container_width=True)

    if not edited_df.empty:
        st.bar_chart(edited_df.set_index("Ticker")["Dollar Amount"])

with tab2:
    st.subheader("📊 Live Tickers")

    portfolio_df = clean_portfolio(st.session_state.portfolio)
    tickers = portfolio_df["Ticker"].tolist()

    if not tickers:
        st.warning("Add at least one ticker in Portfolio Builder.")
    else:
        live_data = []

        for ticker in tickers:
            info = get_stock_info(ticker)
            price = info.get("regularMarketPrice")
            previous_close = info.get("previousClose")

            daily_change = None
            if price is not None and previous_close not in [None, 0]:
                daily_change = ((price - previous_close) / previous_close) * 100

            live_data.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Price": money(price),
                "Previous Close": money(previous_close),
                "Daily Change %": percent(daily_change),
                "Market Cap": money_big(info.get("marketCap"))
            })

        st.dataframe(pd.DataFrame(live_data), use_container_width=True)

        selected_ticker = st.selectbox("Choose ticker for chart", tickers)
        period = st.selectbox("Chart period", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)

        price_history = get_price_history(selected_ticker, period)

        if not price_history.empty and "Close" in price_history.columns:
            st.line_chart(price_history["Close"])
        else:
            st.info("No chart data available.")

with tab3:
    st.subheader("🏦 Fundamental Analysis")

    portfolio_df = clean_portfolio(st.session_state.portfolio)
    tickers = portfolio_df["Ticker"].tolist()

    if not tickers:
        st.warning("Add at least one ticker in Portfolio Builder.")
    else:
        fundamentals_data = []

        for ticker in tickers:
            info = get_stock_info(ticker)

            fundamentals_data.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Market Cap": money_big(info.get("marketCap")),
                "Revenue Growth %": percent(info.get("revenueGrowth") * 100 if info.get("revenueGrowth") is not None else None),
                "Earnings Growth %": percent(info.get("earningsGrowth") * 100 if info.get("earningsGrowth") is not None else None),
                "Profit Margin %": percent(info.get("profitMargins") * 100 if info.get("profitMargins") is not None else None),
                "Debt / Equity": number(info.get("debtToEquity")),
                "Forward P/E": number(info.get("forwardPE")),
                "Trailing P/E": number(info.get("trailingPE")),
                "Price / Sales": number(info.get("priceToSalesTrailing12Months")),
                "Return on Equity %": percent(info.get("returnOnEquity") * 100 if info.get("returnOnEquity") is not None else None),
                "Free Cash Flow": money_big(info.get("freeCashflow")),
                "Total Revenue": money_big(info.get("totalRevenue")),
                "Gross Margin %": percent(info.get("grossMargins") * 100 if info.get("grossMargins") is not None else None)
            })

        st.dataframe(pd.DataFrame(fundamentals_data), use_container_width=True)
