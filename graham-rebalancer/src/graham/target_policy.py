from .data_models import UserPrefs, MarketInputs
from .scoring import score_market


def map_score_to_equity(score: float, prefs: UserPrefs) -> int:
    """
    Maps a market score (roughly in [-3, +3]) to an equity percentage in [min_equity, max_equity].
    Applies user tilt, bounds, and rounding.
    """
    
    lo, hi = prefs.min_equity, prefs.max_equity
    
    # Normalize score from [-3, +3] -> [0, 1]
    norm = (score + 3.0) / 6.0
    norm = max(0.0, min(1.0, norm)) # clip to [0, 1]
    
    # Interpolate between min and max equity
    equity = lo + norm * (hi - lo)
    
    # Apply user tilt
    equity += prefs.risk_tilt_pct
    
    # Clip again to bounds
    equity = max(lo, min(hi, equity))
    
    # Round to nearest step
    return int(round(equity / prefs.step) * prefs.step)

def recommend_equity(m: MarketInputs, prefs: UserPrefs) -> dict:
    """
    End-to-end helper: market inputs -> score -> equity target (%).
    """
    s = score_market(m)
    equity = map_score_to_equity(s, prefs)
    return {"score": s, "equity_pct": equity}

def apply_hysteresis(prev_target: int, new_target: int, band: int = 5) -> int:
    """
    If the absolute change is smaller than `band` percentage points,
    keep the previous target; otherwise accept the new one.
    Example: prev=60, new=62, band=5 → 60; prev=60, new=67 → 67
    """
    return prev_target if abs(new_target - prev_target) < band else new_target


def next_equity_target(prev_target: int, score: float, prefs: "UserPrefs", band: int = 5) -> int:
    """
    Convenience: map the score to equity % (Graham band + tilt + rounding),
    then apply hysteresis vs. the last target.
    """
    proposed = map_score_to_equity(score, prefs)
    return apply_hysteresis(prev_target, proposed, band=band)
