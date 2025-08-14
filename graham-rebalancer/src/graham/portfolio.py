
import pandas as pd

def load_holdings(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "market_value" not in df.columns:
        if {"quantity", "price"}.issubset(df.columns):
            df["market_value"] = df["quantity"] * df["price"]
        else:
            raise ValueError("DataFrame must contain 'market_value' or both 'quantity' and 'price' columns.")
    return df

def weights_by_class(df: pd.DataFrame, include_cash: bool = True) -> dict:
    g = df.groupby("asset_class")["market_value"].sum()
    total = g.sum() if include_cash else g.drop(labels=["Cash"], errors = "ignore").sum()
    w = (g / total * 100).to_dict()
    w["TOTAL"] = float(total)
    return w

