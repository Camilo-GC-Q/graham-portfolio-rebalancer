import argparse
from .data_models import MarketInputs, UserPrefs
from .portfolio import load_holdings
from .target_policy import recommend_equity, next_equity_target
from .rebalance import rebalance_plan
from .reporting import explain

def parse_args():
    ap = argparse.ArgumentParser(prog="graham")
    ap.add_argument("--holdings", required=True, help="Path to holdings CSV")
    # market inputs
    ap.add_argument("--cape", type=float)
    ap.add_argument("--spx200", type=float, help="% vs 200d")
    ap.add_argument("--yc", type=float, help="10y-3m bps")
    ap.add_argument("--vix", type=float)
    ap.add_argument("--hy", type=float, help="HY OAS bps")
    ap.add_argument("--unemp", type=float, help="6m change (pp)")
    # prefs
    ap.add_argument("--tilt", type=int, default=0)
    ap.add_argument("--include-cash", action="store_true")
    # hysteresis
    ap.add_argument("--band", type=int, default=5, help="Hysteresis band in pct points")
    ap.add_argument("--prev-target", type=int, help="Previous equity target to compare against")
    # output
    ap.add_argument("--explain", action="store_true", help="Print human-readable explanation")
    return ap.parse_args()

def main():
    args = parse_args()

    m = MarketInputs(
        cape=args.cape, spx_vs_200d_pct=args.spx200, yc_10y_3m_bps=args.yc,
        vix_level=args.vix, hy_oas_bps=args.hy, unemp_6m_change_pp=args.unemp
    )
    prefs = UserPrefs(risk_tilt_pct=args.tilt, include_cash=args.include_cash)

    # proposed equity from signals
    rec = recommend_equity(m, prefs)  # {'score': s, 'equity_pct': proposed}

    # apply hysteresis if previous target supplied
    if args.prev_target is not None:
        eq_final = next_equity_target(args.prev_target, rec["score"], prefs, band=args.band)
        rec = {"score": rec["score"], "equity_pct": eq_final}  # replace with final
    else:
        eq_final = rec["equity_pct"]

    # plan the rebalance
    df = load_holdings(args.holdings)
    plan = rebalance_plan(df, eq_final, include_cash=prefs.include_cash)

    if args.explain:
        print(explain(rec, plan))
    else:
        print("Recommendation:", rec)
        print("Plan:", plan)

if __name__ == "__main__":
    main()
