# Luc's Investment Terminal V2

A self-updating Streamlit investment dashboard built for long-term stock analysis.

## What it includes

- Portfolio overview
- Live market data using yfinance
- 100-point company scoring model
- Valuation monitor
- Debt monitor
- Crisis dashboard
- Portfolio alerts
- Streamlit Cloud deployment support

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy online with Streamlit Community Cloud

1. Create a GitHub account if you do not already have one.
2. Create a new GitHub repository, for example:

   `luc-investment-terminal`

3. Upload these files into the repository:

   - `app.py`
   - `requirements.txt`
   - `README.md`

4. Go to Streamlit Community Cloud.
5. Click **New app**.
6. Choose your GitHub repository.
7. Set the main file path as:

   `app.py`

8. Click **Deploy**.

Your dashboard will get a public link like:

`https://your-app-name.streamlit.app`

## Important note

This app is educational and should not be treated as financial advice. Some figures from Yahoo Finance may be missing or delayed. For professional-grade accuracy, future versions should connect to SEC filings, FRED macro data, Financial Modeling Prep, Alpha Vantage, or Polygon.