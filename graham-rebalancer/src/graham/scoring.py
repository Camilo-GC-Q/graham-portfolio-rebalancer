from .data_models import MarketInputs

def score_market(m: MarketInputs) -> float:
    """ 
    Returns a signed score. Higher -> more equity, lower -> less equity.
    Rough target range is about [-3, +3], but we clip/scale later.
    """
    
    s = 0.0
    
    # - Valution (CAPE): cheaper is better
    if m.cape is not None:
        if m.cape < 15:
            s += 1.0
        elif m.cape <= 22:
            s += 0.3
        elif m.cape <= 28:
            s -= -0.3
        else:
            s -= 1.0
            
    # - Trend (S&P vs 200d): above = mild tailwind; below = caution
    if m.spx_vs_200d_pct is not None:
        s += 0.5 if m.spx_vs_200d_pct >= 0 else -0.5
        
    # - Yield Curve (10y - 3m, bps): inverted = caution
    if m.yc_10y_3m_bps is not None:
        if m.yc_10y_3m_bps < 0:
            s += -0.5
        elif m.yc_10y_3m_bps < 50:
            s += -0.1
        else:
            s += 0.2
            
    # - Volatility (VIX): high = caution
    if m.vix_level is not None:
        if m.vix_level < 15:
            s += 0.25
        elif m.vix_level > 25:
            s += -0.5
        # 15 - 25 is neutral (0)
        
    # - Credit spreads (HY OAS, bps): wide spreads = stress
    if m.hy_oas_bps is not None:
        if m.hy_oas_bps < 350:
            s += 0.25
        elif m.hy_oas_bps > 500:
            s += -0.5
            # in-between is neutral 
            
    # Labor (unemployment 6m change, pp): rising unemployment = caution
    if m.unemp_6m_change_pp is not None:
        if m.unemp_6m_change_pp < -0.2:
            s += 0.25
        elif m.unemp_6m_change_pp >= 0.2:
            s += -0.25
            # small changes are neutral
            
    # if m.forward_pe is not None:
    #     fpe = float(m.forward_pe)
    #     if fpe < 15:      
    #         s += 1.0   # cheap
    #     elif fpe <= 18:   
    #         s += 0.3   # somewhat reasonable
    #     elif fpe <= 22:   
    #         s -= 0.3   # a bit rich
    #     else:             
    #         s -= 1.0   # expensive
            
    if m.earnings_yield_pct is not None:
        ey = float(m.earnings_yield_pct)  # e.g., 5.5 means 5.5%
        if ey >= 6.0:       
            s += 1.0    # attractive vs bonds
        elif ey >= 4.5:     
            s += 0.3
        elif ey >= 3.5:     
            s += -0.3
        else:               
            s += -1.0   # expensive / low yield

    return s


def score_breakdown(m: MarketInputs) -> dict:
    """
    Return a per-signal breakdown with raw values and contributions.
    Works with either valuation input:
      - earnings_yield_pct (preferred, if present)
      - forward_pe (fallback)
    """
    parts = {}
    total = 0.0

    # --- Valuation: Earnings Yield (%) preferred ---
    if m.earnings_yield_pct is not None:
        ey = float(m.earnings_yield_pct)  # e.g., 5.5 means 5.5%
        if ey >= 6.0:      c =  +1.0   # cheap vs bonds
        elif ey >= 4.5:    c =  +0.3
        elif ey >= 3.5:    c =  -0.3
        else:              c =  -1.0   # expensive / low yield
        parts["earnings_yield_pct"] = {"value": ey, "contrib": c}
        total += c

    # # --- Valuation: Forward P/E (used only if EY missing) ---
    # elif m.forward_pe is not None:
    #     fpe = float(m.forward_pe)
    #     if fpe < 15:       c =  +1.0   # cheap
    #     elif fpe <= 18:    c =  +0.3
    #     elif fpe <= 22:    c =  -0.3
    #     else:              c =  -1.0   # expensive
    #     parts["forward_pe"] = {"value": fpe, "contrib": c}
    #     total += c

    # --- Trend (S&P vs 200d, %) ---
    if m.spx_vs_200d_pct is not None:
        c = 0.5 if m.spx_vs_200d_pct >= 0 else -0.5
        parts["spx_vs_200d_pct"] = {"value": float(m.spx_vs_200d_pct), "contrib": c}
        total += c

    # --- Yield curve (10y-3m, bps) ---
    if m.yc_10y_3m_bps is not None:
        yc = float(m.yc_10y_3m_bps)
        if yc < 0:         c = -0.5
        elif yc < 50:      c = -0.1
        else:              c = +0.2
        parts["yc_10y_3m_bps"] = {"value": yc, "contrib": c}
        total += c

    # --- VIX level ---
    if m.vix_level is not None:
        vx = float(m.vix_level)
        if vx < 15:        c = +0.25
        elif vx > 25:      c = -0.5
        else:              c =  0.0
        parts["vix_level"] = {"value": vx, "contrib": c}
        total += c

    # --- HY OAS (bps) ---
    if m.hy_oas_bps is not None:
        hy = float(m.hy_oas_bps)
        if hy < 350:       c = +0.25
        elif hy > 500:     c = -0.5
        else:              c =  0.0
        parts["hy_oas_bps"] = {"value": hy, "contrib": c}
        total += c

    # --- Unemployment Δ 6m (pp) ---
    if m.unemp_6m_change_pp is not None:
        du = float(m.unemp_6m_change_pp)
        if du <= -0.2:     c = +0.25
        elif du >=  0.2:   c = -0.25
        else:              c =  0.0
        parts["unemp_6m_change_pp"] = {"value": du, "contrib": c}
        total += c

    parts["total_score"] = total
    return parts
