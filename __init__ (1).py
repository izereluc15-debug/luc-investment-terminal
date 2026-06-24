import pandas as pd
import math

def simple_dcf_value(fcf, growth_rate=0.12, discount_rate=0.10, terminal_growth=0.03, years=10, shares_outstanding=None):
    if fcf is None or pd.isna(fcf) or fcf <= 0:
        return None
    cashflows = []
    for year in range(1, years + 1):
        future_fcf = fcf * ((1 + growth_rate) ** year)
        pv = future_fcf / ((1 + discount_rate) ** year)
        cashflows.append(pv)
    terminal_fcf = fcf * ((1 + growth_rate) ** years) * (1 + terminal_growth)
    terminal_value = terminal_fcf / max(discount_rate - terminal_growth, 0.01)
    terminal_pv = terminal_value / ((1 + discount_rate) ** years)
    enterprise_value = sum(cashflows) + terminal_pv
    if shares_outstanding and shares_outstanding > 0:
        return enterprise_value / shares_outstanding
    return enterprise_value

def peg_fair_pe(growth_rate):
    if growth_rate is None or pd.isna(growth_rate):
        return None
    growth_pct = growth_rate * 100
    return min(max(growth_pct, 10), 50)

def valuation_signal(row):
    val_score = row.get("Valuation Score /15")
    if pd.isna(val_score): return "⚪ Unknown"
    if val_score >= 13: return "🟢 Attractive"
    if val_score >= 9: return "🟡 Fair"
    if val_score >= 6: return "🟠 Expensive"
    return "🔴 Very Expensive"