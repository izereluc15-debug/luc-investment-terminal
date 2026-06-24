import pandas as pd
import json
from pathlib import Path

def load_quality_scores(path="src/data/quality_scores.json"):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return {}

def score_revenue_growth(x):
    if pd.isna(x): return 8
    if x >= 0.30: return 20
    if x >= 0.20: return 17
    if x >= 0.10: return 13
    if x >= 0.00: return 8
    return 2

def score_earnings_growth(x, margin):
    if pd.notna(x):
        if x >= 0.30: return 20
        if x >= 0.20: return 17
        if x >= 0.10: return 13
        if x >= 0.00: return 8
        return 2
    if pd.notna(margin):
        if margin >= 0.30: return 18
        if margin >= 0.20: return 15
        if margin >= 0.10: return 12
        if margin >= 0.00: return 7
        return 2
    return 8

def score_fcf(x):
    if pd.isna(x): return 6
    if x > 10_000_000_000: return 15
    if x > 1_000_000_000: return 12
    if x > 0: return 9
    return 3

def score_valuation(pe, peg, ps):
    if pd.notna(peg):
        if peg < 1: return 15
        if peg < 1.5: return 13
        if peg < 2.5: return 9
        return 5
    if pd.notna(pe):
        if pe < 20: return 13
        if pe < 35: return 10
        if pe < 60: return 7
        return 4
    if pd.notna(ps):
        if ps < 5: return 10
        if ps < 10: return 7
        return 4
    return 6

def score_debt(debt, cash, debt_equity):
    if pd.notna(debt) and pd.notna(cash):
        if debt <= cash: return 10
        if debt <= cash * 2: return 7
        return 3
    if pd.notna(debt_equity):
        if debt_equity < 50: return 9
        if debt_equity < 100: return 6
        return 3
    return 6

def status_from_score(score):
    if score >= 95: return "🟢 Exceptional Buy"
    if score >= 90: return "🟢 Strong Buy"
    if score >= 80: return "🟢 Hold & Add on Dips"
    if score >= 70: return "🟡 Hold"
    if score >= 60: return "🟠 Watch Closely"
    return "🔴 Avoid / High Risk"

def add_scores(df):
    quality = load_quality_scores()
    rows = []
    for _, r in df.iterrows():
        ticker = r.get("Ticker")
        q = quality.get(ticker, {"moat": 7, "management": 4, "market_opportunity": 4, "ai_exposure": 5})
        rev = score_revenue_growth(r.get("Revenue Growth"))
        earn = score_earnings_growth(r.get("Earnings Growth"), r.get("Profit Margin"))
        fcf = score_fcf(r.get("Free Cash Flow"))
        val = score_valuation(r.get("Forward P/E"), r.get("PEG"), r.get("Price/Sales"))
        debt = score_debt(r.get("Total Debt"), r.get("Cash"), r.get("Debt/Equity"))
        total = rev + earn + fcf + val + debt + q["moat"] + q["management"] + q["market_opportunity"]
        rows.append({
            "Ticker": ticker,
            "Revenue Score /20": rev,
            "Earnings Score /20": earn,
            "FCF Score /15": fcf,
            "Valuation Score /15": val,
            "Debt Score /10": debt,
            "Moat /10": q["moat"],
            "Management /5": q["management"],
            "Market Opportunity /5": q["market_opportunity"],
            "AI Exposure /10": q.get("ai_exposure", 5),
            "Total Score /100": min(total, 100),
            "Investment Rating": status_from_score(min(total, 100)),
        })
    return df.merge(pd.DataFrame(rows), on="Ticker", how="left")