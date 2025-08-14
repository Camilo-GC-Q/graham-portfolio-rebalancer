import sys  
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from graham.data_models import MarketInputs, UserPrefs
from graham.portfolio import load_holdings
from graham.target_policy import recommend_equity, next_equity_target
from graham.rebalance import rebalance_plan
from graham.reporting import explain
from graham.market_signals import fetch_market_inputs_live
from graham.scoring import score_breakdown



STATE_PATH = Path(__file__).resolve().parent / "data" / "state.json"

def _read_prev_target(path=STATE_PATH):
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        v = data.get("prev_target")
        return int(v) if v is not None else None
    except Exception:
        return None

def _write_prev_target(value: int, path=STATE_PATH):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"prev_target": int(value)}, indent=2))
    except Exception:
        pass

CONFIG = {
    "holdings_path": "data/holdings_sample.csv",

    # Choose "manual" or "live"
    "market_source": "live",   # <- set to "live" to auto-fetch, "manual" to use values below

    # If using manual, fill these:
    "market": {
        "cape": None,
        "spx_vs_200d_pct": 2.0,
        "yc_10y_3m_bps": -50.0,
        "vix_level": 18.0,
        "hy_oas_bps": 390.0,
        "unemp_6m_change_pp": 0.1,
        "forward_pe": None,  
        "earnings_yield_pct": None 
    },

    "prefs": {"risk_tilt_pct": 0, "min_equity": 25, "max_equity": 75, "step": 5, "include_cash": True},

    "hysteresis_band": 5,
    "previous_target": None,

    "print_json_also": False
}

def main():
    # 0) Build inputs & prefs
    if CONFIG["market_source"] == "live":
        m = fetch_market_inputs_live(include_cape=CONFIG.get("include_cape", False))
    else:
        m = MarketInputs(**CONFIG["market"])
    prefs = UserPrefs(**CONFIG["prefs"])

    try:
        from graham.scoring import score_breakdown
        bd = score_breakdown(m)
        print("— Score breakdown —")
        for k, v in bd.items():
            if k == "total_score":
                continue
            print(f"{k:>20}: value={v['value']!r}  contrib={v['contrib']:+.2f}")
        print(f"{'TOTAL':>20}: {bd['total_score']:+.2f}\n")
    except Exception:
        pass

    rec = recommend_equity(m, prefs)     # {'score': s, 'equity_pct': eq}
    print(f"Proposed equity % (no hysteresis): {rec['equity_pct']}")

    prev = CONFIG.get("previous_target") or _read_prev_target()
    band = CONFIG.get("hysteresis_band", 5)
    if prev is not None:
        final_eq = next_equity_target(prev, rec["score"], prefs, band=band)
        print(f"Previous target: {prev} | Band: ±{band}pp | Final (after hysteresis): {final_eq}\n")
    else:
        final_eq = rec["equity_pct"]
        print(f"No previous target found; using proposed {final_eq}\n")

    df = load_holdings(CONFIG["holdings_path"])

    plan = rebalance_plan(df, final_eq, include_cash=prefs.include_cash)

    print(explain({"score": rec["score"], "equity_pct": final_eq}, plan))

    _write_prev_target(final_eq)

    if CONFIG.get("print_json_also", False):
        print("\n--- JSON ---")
        print(json.dumps({"inputs": m.__dict__, "recommendation": {"score": rec["score"], "equity_pct": final_eq}, "plan": plan},
                         default=float, indent=2))

if __name__ == "__main__":
    main()