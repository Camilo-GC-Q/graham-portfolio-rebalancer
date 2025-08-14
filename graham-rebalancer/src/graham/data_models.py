from dataclasses import dataclass
from typing import Optional

@dataclass
class MarketInputs:
    cape: Optional[float] = None
    spx_vs_200d_pct: Optional[float] = None
    yc_10y_3m_bps: Optional[float] = None
    vix_level: Optional[float] = None
    hy_oas_bps: Optional[float] = None
    unemp_6m_change_pp: Optional[float] = None
    forward_pe: Optional[float] = None           # SP500 forward P/E via SPY
    earnings_yield_pct: Optional[float] = None   # = 100 / forward_pe

@dataclass
class UserPrefs:
    risk_tilt_pct: int = 0
    min_equity: int = 25
    max_equity: int = 75
    step: int = 5
    include_cash: bool = True
    
    