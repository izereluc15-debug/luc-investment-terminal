import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="Luc Investment Terminal",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Luc Investment Terminal")
st.caption("Portfolio builder, live tickers, and fundamental analysis dashboard.")

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

    st.write("Add, edit, or remove assets directly in the table.")

    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
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

    st.subheader("Allocation Chart")

    if not edited_df.empty:
        chart_df = edited_df.set_index("Ticker")["Dollar Amount"]
        st.bar_chart(chart_df)

    csv = edited_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Portfolio CSV",
        data=csv,
        file_name="luc_portfolio.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("📊 Live Tickers")

    tickers_input = st.text_input(
        "Enter ticker symbols separated by commas",
        value="NVDA,MSFT,TSM,AVGO,AMD,AMZN,PLTR,QQQM"
    )

    tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]

    live_data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

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

        except Exception:
            live_data.append({
                "Ticker": ticker,
                "Company": "Data unavailable",
                "Price": None,
                "Previous Close": None,
                "Daily Change %": None,
                "Market Cap": None
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

    if tickers:
        selected_ticker = st.selectbox("Choose ticker for price chart", tickers)

        period = st.selectbox(
            "Chart period",
            ["1mo", "3mo", "6mo", "1y", "5y"],
            index=3
        )

        try:
            price_history = yf.download(selected_ticker, period=period, progress=False)

            if not price_history.empty:
                st.line_chart(price_history["Close"])
            else:
                st.info("No chart data available.")

        except Exception:
            st.error("Could not load chart data.")

with tab3:
    st.subheader("🏦 Fundamental Analysis")

    fundamentals_input = st.text_input(
        "Enter ticker symbols for fundamentals",
        value="NVDA,MSFT,TSM,AVGO,AMD,AMZN,PLTR,QQQM"
    )

    fundamental_tickers = [
        ticker.strip().upper()
        for ticker in fundamentals_input.split(",")
        if ticker.strip()
    ]

    fundamentals_data = []

    for ticker in fundamental_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            revenue_growth = info.get("revenueGrowth")
            earnings_growth = info.get("earningsGrowth")
            profit_margin = info.get("profitMargins")
            return_on_equity = info.get("returnOnEquity")

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
                "Gross Margins %": info.get("grossMargins") * 100 if info.get("grossMargins") is not None else None
            })

        except Exception:
            fundamentals_data.append({
                "Ticker": ticker,
                "Company": "Data unavailable",
                "Market Cap": None,
                "Revenue Growth %": None,
                "Earnings Growth %": None,
                "Profit Margin %": None,
                "Debt / Equity": None,
                "Forward P/E": None,
                "Trailing P/E": None,
                "Price / Sales": None,
                "Return on Equity %": None,
                "Free Cash Flow": None,
                "Total Revenue": None,
                "Gross Margins %": None
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
            "Gross Margins %": "{:.2f}%"
        }),
        use_container_width=True
    )
