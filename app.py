import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="Luc Investment Terminal",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Luc Investment Terminal")
st.caption("Dynamic portfolio builder, live tickers, and fundamental analysis dashboard.")

default_portfolio = pd.DataFrame({
    "Ticker": ["NVDA", "TSM", "AVGO", "MSFT", "AMD", "AMZN", "PLTR", "RKLB", "TEM", "CRWV", "QQQM"],
    "Company": [
        "NVIDIA",
        "TSMC",
        "Broadcom",
        "Microsoft",
        "AMD",
        "Amazon",
        "Palantir",
        "Rocket Lab",
        "Tempus AI",
        "CoreWeave",
        "Invesco NASDAQ 100 ETF"
    ],
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


@st.cache_data(ttl=300)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_price_history(ticker, period):
    try:
        return yf.download(ticker, period=period, progress=False)
    except Exception:
        return pd.DataFrame()


tab1, tab2, tab3 = st.tabs([
    "💼 Portfolio Builder",
    "📊 Live Tickers",
    "🏦 Fundamental Analysis"
])

with tab1:
    st.subheader("💼 Portfolio Builder")

    total_value = st.number_input(
        "Total portfolio value ($)",
        min_value=0.0,
        value=1500.0,
        step=100.0
    )

    st.write("Add, edit, or remove assets below. Other tabs will update automatically.")

    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker Symbol"),
            "Company": st.column_config.TextColumn("Company Name"),
            "Weight %": st.column_config.NumberColumn(
                "Weight %",
                min_value=0.0,
                max_value=100.0,
                step=0.1
            )
        }
    )

    edited_df = clean_portfolio(edited_df)
    st.session_state.portfolio = edited_df

    edited_df["Dollar Amount"] = edited_df["Weight %"] / 100 * total_value
    total_weight = edited_df["Weight %"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
    col2.metric("Total Weight", f"{total_weight:.2f}%")
    col3.metric("Number of Assets", len(edited_df))

    if round(total_weight, 2) != 100:
        st.warning(f"Your portfolio weight is {total_weight:.2f}%. It should equal 100%.")
    else:
        st.success("Portfolio weights total 100%.")

    st.subheader("Final Portfolio Allocation")

    st.dataframe(
        edited_df.style.format({
            "Weight %": "{:.2f}%",
            "Dollar Amount": "${:,.2f}"
        }),
        use_container_width=True
    )

    if not edited_df.empty:
        st.subheader("Allocation Chart")
        st.bar_chart(edited_df.set_index("Ticker")["Dollar Amount"])

    csv = edited_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Portfolio CSV",
        data=csv,
        file_name="luc_portfolio.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("📊 Live Tickers")

    portfolio_df = clean_portfolio(st.session_state.portfolio)
    tickers = portfolio_df["Ticker"].tolist()

    if not tickers:
        st.warning("Add at least one ticker in the Portfolio Builder tab.")
    else:
        live_data = []

        for ticker in tickers:
            info = get_stock_info(ticker)

            price = info.get("regularMarketPrice")
            previous_close = info.get("previousClose")

            daily_change = None
            if price is not None and previous_close is not None and previous_close != 0:
                daily_change = ((price - previous_close) / previous_close) * 100

            live_data.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Price": price,
                "Previous Close": previous_close,
                "Daily Change %": daily_change,
                "Market Cap": info.get("marketCap")
            })

        live_df = pd.DataFrame(live_data)

        st.dataframe(
            live_df.style.format({
                "Price": "${:,.2f}",
                "Previous Close": "${:,.2f}",
                "Daily Change %": "{:.2f}%",
                "Market Cap": "${:,.0f}"
            }),
            use_container_width=True
        )

        selected_ticker = st.selectbox("Choose ticker for chart", tickers)

        period = st.selectbox(
            "Chart period",
            ["1mo", "3mo", "6mo", "1y", "5y"],
            index=3
        )

        price_history = get_price_history(selected_ticker, period)

        if not price_history.empty:
            st.line_chart(price_history["Close"])
        else:
            st.info("No chart data available.")

with tab3:
    st.subheader("🏦 Fundamental Analysis")

    portfolio_df = clean_portfolio(st.session_state.portfolio)
    tickers = portfolio_df["Ticker"].tolist()

    if not tickers:
        st.warning("Add at least one ticker in the Portfolio Builder tab.")
    else:
        fundamentals_data = []

        for ticker in tickers:
            info = get_stock_info(ticker)

            revenue_growth = info.get("revenueGrowth")
            earnings_growth = info.get("earningsGrowth")
            profit_margin = info.get("profitMargins")
            return_on_equity = info.get("returnOnEquity")
            gross_margin = info.get("grossMargins")

            fundamentals_data.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Market Cap": info.get("marketCap"),
                "Revenue Growth %": revenue_growth * 100 if revenue_growth is not None else None,
                "Earnings Growth %": earnings_growth * 100 if earnings_growth is not None else None,
                "Profit Margin %": profit_margin * 100 if profit_margin is not None else None,
                "Debt / Equity": info.get("debtToEquity"),
                "Forward P/E": info.get("forwardPE"),
                "Trailing P/E": info.get("trailingPE"),
                "Price / Sales": info.get("priceToSalesTrailing12Months"),
                "Return on Equity %": return_on_equity * 100 if return_on_equity is not None else None,
                "Free Cash Flow": info.get("freeCashflow"),
                "Total Revenue": info.get("totalRevenue"),
                "Gross Margin %": gross_margin * 100 if gross_margin is not None else None
            })

        fundamentals_df = pd.DataFrame(fundamentals_data)

        st.dataframe(
            fundamentals_df.style.format({
                "Market Cap": "${:,.0f}",
                "Revenue Growth %": "{:.2f}%",
                "Earnings Growth %": "{:.2f}%",
                "Profit Margin %": "{:.2f}%",
                "Debt / Equity": "{:.2f}",
                "Forward P/E": "{:.2f}",
                "Trailing P/E": "{:.2f}",
                "Price / Sales": "{:.2f}",
                "Return on Equity %": "{:.2f}%",
                "Free Cash Flow": "${:,.0f}",
                "Total Revenue": "${:,.0f}",
                "Gross Margin %": "{:.2f}%"
            }),
            use_container_width=True
        )
