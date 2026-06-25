import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="Luc Investment Terminal",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Luc Investment Terminal")
st.caption("Portfolio allocation, live market tickers, and investment education dashboard.")

default_portfolio = pd.DataFrame({
    "Ticker": ["NVDA", "TSM", "AVGO", "MSFT", "AMD", "AMZN", "PLTR", "RKLB", "TEM", "CRWV", "QQQM"],
    "Company": ["NVIDIA", "TSMC", "Broadcom", "Microsoft", "AMD", "Amazon", "Palantir", "Rocket Lab", "Tempus AI", "CoreWeave", "Invesco NASDAQ 100 ETF"],
    "Weight %": [22, 20, 13, 13, 10, 10, 5, 2.3, 2.3, 2.4, 0]
})

if "portfolio" not in st.session_state:
    st.session_state.portfolio = default_portfolio.copy()

tab1, tab2, tab3 = st.tabs(["💼 Portfolio Builder", "📊 Live Tickers", "📘 Investment Dictionary"])

with tab1:
    st.subheader("Portfolio Builder")

    total_value = st.number_input(
        "Total portfolio value ($)",
        min_value=0.0,
        value=1500.0,
        step=100.0
    )

    st.write("Add, edit, or remove assets directly in the table below.")

    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker Symbol"),
            "Company": st.column_config.TextColumn("Company Name"),
            "Weight %": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0)
        }
    )

    st.session_state.portfolio = edited_df

    edited_df["Dollar Amount"] = edited_df["Weight %"] / 100 * total_value
    total_weight = edited_df["Weight %"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
    col2.metric("Total Weight", f"{total_weight:.2f}%")
    col3.metric("Number of Assets", len(edited_df))

    if total_weight != 100:
        st.warning(f"Your portfolio weight is {total_weight:.2f}%. It should equal 100%.")
    else:
        st.success("Portfolio weights total 100%.")

    st.subheader("Final Allocation")
    st.dataframe(
        edited_df.style.format({
            "Weight %": "{:.2f}%",
            "Dollar Amount": "${:,.2f}"
        }),
        use_container_width=True
    )

    st.subheader("Portfolio Allocation Chart")
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
    st.subheader("Live Tickers")

    tickers_input = st.text_input(
        "Enter ticker symbols separated by commas",
        value="NVDA,MSFT,TSM,AVGO,AMD,AMZN,PLTR,QQQM"
    )

    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    live_data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get("regularMarketPrice")
            previous_close = info.get("previousClose")
            market_cap = info.get("marketCap")
            name = info.get("shortName", ticker)

            change = None
            if price and previous_close:
                change = ((price - previous_close) / previous_close) * 100

            live_data.append({
                "Ticker": ticker,
                "Name": name,
                "Price": price,
                "Daily Change %": change,
                "Market Cap": market_cap
            })

        except Exception:
            live_data.append({
                "Ticker": ticker,
                "Name": "Data unavailable",
                "Price": None,
                "Daily Change %": None,
                "Market Cap": None
            })

    live_df = pd.DataFrame(live_data)

    st.dataframe(
        live_df.style.format({
            "Price": "${:,.2f}",
            "Daily Change %": "{:.2f}%",
            "Market Cap": "${:,.0f}"
        }),
        use_container_width=True
    )

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
    st.subheader("Investment Dictionary")

    st.markdown("""
### Key Portfolio Terms

**Ticker Symbol**  
A short code used to identify a stock or ETF. Example: **NVDA** means NVIDIA, **MSFT** means Microsoft.

**Stock**  
A small ownership share in a company.

**ETF**  
An exchange-traded fund. It holds many stocks inside one investment. Example: **QQQM** tracks the Nasdaq-100.

**Portfolio**  
The full group of assets you own.

**Portfolio Weight**  
The percentage of your portfolio invested in one asset. Example: if NVIDIA is 22%, then $22 of every $100 is in NVIDIA.

**Dollar Allocation**  
The actual amount of money assigned to each asset.

**Market Cap**  
The total value of a company in the stock market.

**Dividend**  
Money some companies pay to shareholders.

**Growth Stock**  
A company expected to grow revenue and earnings faster than average.

**Valuation**  
How expensive or cheap a stock is compared to its earnings, revenue, or future growth.

**Risk**  
The chance that your investment loses value or performs worse than expected.

**Diversification**  
Spreading money across different companies or sectors to reduce risk.

**Rebalancing**  
Adjusting portfolio weights back to your target percentages.

**Live Ticker**  
A real-time or near-real-time stock symbol showing market price movement.

**Long-Term Investing**  
Buying quality assets and holding them for many years.
""")
