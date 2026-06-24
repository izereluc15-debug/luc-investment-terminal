import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_stock_data(tickers):
    rows = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")
            one_year_return = None
            if hist is not None and len(hist) > 5 and "Close" in hist:
                first = hist["Close"].iloc[0]
                last = hist["Close"].iloc[-1]
                if first:
                    one_year_return = (last / first) - 1

            rows.append({
                "Ticker": ticker,
                "Company": info.get("shortName", ticker),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "Previous Close": info.get("previousClose"),
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
                "Dividend Yield": info.get("dividendYield"),
            })
        except Exception as e:
            rows.append({"Ticker": ticker, "Company": ticker, "Error": str(e)})
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def get_price_history(ticker, period="5y"):
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()