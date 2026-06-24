import pandas as pd

def generate_alerts(df):
    alerts = []
    for _, r in df.iterrows():
        ticker = r.get("Ticker")
        company = r.get("Company", ticker)

        if pd.notna(r.get("Valuation Score /15")) and r["Valuation Score /15"] <= 5:
            alerts.append([ticker, company, "Valuation", "🔴 Valuation is very demanding; growth must remain exceptional."])
        if pd.notna(r.get("Debt Score /10")) and r["Debt Score /10"] <= 3:
            alerts.append([ticker, company, "Debt", "🔴 Heavy debt risk or weak net cash position."])
        if pd.notna(r.get("Free Cash Flow")) and r["Free Cash Flow"] < 0:
            alerts.append([ticker, company, "Cash Flow", "🟡 Negative free cash flow; monitor funding needs."])
        if pd.notna(r.get("Revenue Growth")) and r["Revenue Growth"] < 0.10:
            alerts.append([ticker, company, "Growth", "🟡 Revenue growth below 10%; watch for slowdown."])
        if pd.notna(r.get("Total Score /100")) and r["Total Score /100"] < 70:
            alerts.append([ticker, company, "Quality", "🟠 Total score below 70; position should remain small/speculative."])
    if not alerts:
        return pd.DataFrame(columns=["Ticker", "Company", "Type", "Alert"])
    return pd.DataFrame(alerts, columns=["Ticker", "Company", "Type", "Alert"])