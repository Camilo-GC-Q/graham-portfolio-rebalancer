import os
import datetime as dt
import pandas as pd
import yfinance as yf

from .data_models import MarketInputs
from dotenv import load_dotenv

# Lazy imports to keep optional deps optional
def _import_yf():
    import yfinance as yf
    return yf

def _import_fred():
    from fredapi import Fred
    return Fred

load_dotenv()  # reads .env if present

# ---- FRED helpers ----
def _fred_client():
    Fred = _import_fred()
    key = os.getenv("FRED_API_KEY")
    return Fred(api_key=key)

def _fred_latest(series_id: str, months_back: int = 24) -> float | None:
    """
    Get the latest non-NaN value from a FRED series (as float).
    months_back limits how far we pull to keep it snappy.
    """
    fred = _fred_client()
    end = dt.date.today()
    start = end - dt.timedelta(days=months_back * 31)
    s = fred.get_series(series_id, observation_start=start, observation_end=end)
    if s is None or len(s.dropna()) == 0:
        return None
    return float(s.dropna().to_numpy()[-1])

def _fred_value_and_prior(series_id: str, months_back: int = 24, lag_months: int = 6) -> tuple[float | None, float | None]:
    fred = _fred_client()
    end = dt.date.today()
    start = end - dt.timedelta(days=max(months_back, lag_months + 1) * 31)
    s = fred.get_series(series_id, observation_start=start, observation_end=end).dropna()
    if len(s) == 0:
        return None, None
    latest = float(s.iloc[-1])
    # find approx 6 months ago (by index position)
    prior_idx = max(0, len(s) - 1 - lag_months)
    prior = float(s.iloc[prior_idx])
    return latest, prior

# ---- Yahoo Finance helpers ----
def _yf_last_close(ticker: str, lookback_days: int = 400) -> float | None:
    yf = _import_yf()
    end = dt.date.today()
    start = end - dt.timedelta(days=lookback_days)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return None
    return float(df["Close"].to_numpy()[-1])


def _yf_sma_pct_vs(ticker: str, window: int = 200, lookback_days: int = 480) -> float | None:
    yf = _import_yf()
    end = dt.date.today()
    start = end - dt.timedelta(days=lookback_days)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if df is None or df.empty or len(df) < window + 5:
        return None
    sma = df["Close"].rolling(window).mean()
    last = float(df["Close"].to_numpy()[-1])
    last_sma = float(sma.to_numpy()[-1])
    if pd.isna(last_sma) or last_sma == 0:
        return None
    return 100.0 * (last / last_sma - 1.0)

def fetch_forward_pe_spy() -> float | None:
    """
    Try to get SPY forward P/E from yfinance. Returns None if unavailable.
    """
    try:
        t = yf.Ticker("SPY")
        # Prefer the newer .get_info() where available
        info = None
        try:
            info = t.get_info()
        except Exception:
            info = t.info  # fallback; yfinance may deprecate .info eventually
        if not info:
            return None
      
        fpe = info.get("forwardPE") or info.get("trailingPE")  # keys can vary
        if fpe is None:
            return None
        fpe = float(fpe)
        return fpe if fpe > 0 else None
    except Exception:
        return None

# ---- Public API ----
def fetch_market_inputs_live(include_cape: bool = False) -> MarketInputs:
    """
    Pulls live-ish signals:
      - spx_vs_200d_pct: from Yahoo ^GSPC
      - vix_level: from Yahoo ^VIX
      - yc_10y_3m_bps: FRED DGS10 - DGS3MO (in basis points)
      - hy_oas_bps: FRED BAMLH0A0HYM2 (in bps)
      - unemp_6m_change_pp: FRED UNRATE last minus ~6 months prior (pp)
    """
    # Yahoo
    spx_vs_200d_pct = _yf_sma_pct_vs("^GSPC", window=200)
    vix_level = _yf_last_close("^VIX")
    

    # FRED (percents to bps where needed)
    dgs10 = _fred_latest("DGS10")     # 10y Treasury, %
    dgs3m = _fred_latest("DGS3MO")    # 3m Treasury, %
    yc_10y_3m_bps = None
    if dgs10 is not None and dgs3m is not None:
        yc_10y_3m_bps = (dgs10 - dgs3m) * 100.0  # % → bps

    hy_oas_pct = _fred_latest("BAMLH0A0HYM2")  # HY OAS, %
    hy_oas_bps = hy_oas_pct * 100.0 if hy_oas_pct is not None else None

    unrate_now, unrate_prior = _fred_value_and_prior("UNRATE", months_back=24, lag_months=6)
    unemp_6m_change_pp = None
    if unrate_now is not None and unrate_prior is not None:
        unemp_6m_change_pp = unrate_now - unrate_prior  # already in percentage points
        
    # Forward P/E via SPY
    fpe = fetch_forward_pe_spy()
    ey = 100.0 / fpe if fpe and fpe > 0 else None

    # CAPE: left None by default (can be added later via a durable source)
    cape = None

    return MarketInputs(
        cape=cape,
        spx_vs_200d_pct=spx_vs_200d_pct,
        yc_10y_3m_bps=yc_10y_3m_bps,
        vix_level=vix_level,
        hy_oas_bps=hy_oas_bps,
        unemp_6m_change_pp=unemp_6m_change_pp,
        forward_pe=fpe,
        earnings_yield_pct=ey
    )
