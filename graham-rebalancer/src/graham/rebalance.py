import pandas as pd
from .portfolio import weights_by_class

def rebalance_plan(df: pd.DataFrame, equity_pct: int, include_cash: bool = True) -> dict:
    """
    Given a portfolio DataFrame and target equity %, returns the dollar
    amounts to buy/sell in stocks and bonds to reach the target.
    """
    
    # Calculate current weights
    w = weights_by_class(df, include_cash=include_cash)
    investable = float(w["TOTAL"])
    
    # Current $ amounts
    cur_stock = float(df.loc[df["asset_class"] == "Stock", "market_value"].sum())
    cur_bond = float(df.loc[df["asset_class"] == "Bond", "market_value"].sum())
    
    # Target $ amounts based on equity percentage
    target_stock = investable * (equity_pct / 100.0)
    target_bond = investable - target_stock
    
    return {
        "investable_total": investable,
        "equity_target_pct": int(equity_pct),
        "current_stock$": cur_stock,
        "current_bond$": cur_bond,
        "target_stock$": target_stock,
        "target_bond$": target_bond,
        "stock_to_buy(+)sell(-)$": target_stock - cur_stock,
        "bond_to_buy(+)sell(-)$": target_bond - cur_bond
    }