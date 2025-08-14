

def _fmt(x):
    return f"${x:,.2f}"

def explain(rec: dict, plan: dict) -> str:
    """
    Human-readable summary of the recommendation and plan.
    """
    lines = []
    lines.append(f"Equity target: {rec['equity_pct']}% (score={rec['score']:.2f})")
    lines.append(f"Investable total: {_fmt(float(plan['investable_total']))}")
    lines.append(
        "Stocks: "
        f"current {_fmt(float(plan['current_stock$']))} → "
        f"target {_fmt(float(plan['target_stock$']))} → "
        f"trade {_fmt(float(plan['stock_to_buy(+)sell(-)$']))}"
    )
    lines.append(
        "Bonds:  "
        f"current {_fmt(float(plan['current_bond$']))} → "
        f"target {_fmt(float(plan['target_bond$']))} → "
        f"trade {_fmt(float(plan['bond_to_buy(+)sell(-)$']))}"
    )
    return "\n".join(lines)

