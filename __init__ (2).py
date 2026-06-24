import pandas as pd

def crisis_dashboard():
    return pd.DataFrame([
        ["Market Valuations", 20, 13, "Elevated valuations, especially AI/growth"],
        ["Interest Rates", 15, 9, "Watch Fed policy and bond yields"],
        ["Credit Markets", 15, 13, "Credit spreads normal unless widening"],
        ["Corporate Earnings", 15, 14, "Mega-cap earnings remain strong"],
        ["Unemployment", 10, 8, "Labor market still important to monitor"],
        ["Consumer Spending", 10, 7, "Watch retail sales and delinquencies"],
        ["Yield Curve", 10, 6, "Inversion or re-steepening can warn of stress"],
        ["Speculation", 5, 3, "AI enthusiasm elevated"],
    ], columns=["Indicator", "Max Points", "Current Score", "Comment"])

def portfolio_risk_summary(df):
    total_weight = df["Weight"].sum() if "Weight" in df else 0
    ai_exposure = ((df.get("AI Exposure /10", 0) / 10) * df.get("Weight", 0)).sum()
    weighted_score = (df.get("Total Score /100", 0) * df.get("Weight", 0)).sum() / max(total_weight, 1)
    top_position = df["Weight"].max() if "Weight" in df else 0
    return {
        "Total Weight": total_weight,
        "Weighted Score": weighted_score,
        "AI Exposure Weighted %": ai_exposure,
        "Largest Position %": top_position,
    }