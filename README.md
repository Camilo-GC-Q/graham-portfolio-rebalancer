# Graham Portfolio Rebalancer

A Python tool for portfolio rebalancing inspired by Benjamin Graham’s "Intelligent Investor" principles.  
Targets equity allocations between 25%–75% based on **market conditions**, using live financial data and a configurable scoring system.

**Features:**
- Live data from Yahoo Finance (`yfinance`) and FRED (`fredapi`)
- Valuation metric via S&P 500 earnings yield (trailing P/E fallback)
- Hysteresis to reduce unnecessary trades
- Flexible manual input for backtesting or custom scenarios
- Clear score breakdown explaining each factor’s contribution
- Supports or excludes cash from allocation targets

---

## 📊 How It Works

The rebalancer evaluates multiple market signals, each contributing a score between -0.5 and +0.5:

| Signal              | Description |
|---------------------|-------------|
| **Earnings yield** (`earnings_yield_pct`) | Inverse of S&P 500 P/E. Low yields reduce equity exposure. |
| **S&P 500 vs. 200-day SMA** (`spx_vs_200d_pct`) | Trend indicator. Above average = bullish. |
| **Yield curve (10Y–3M)** (`yc_10y_3m_bps`) | Inversion often signals recession risk. |
| **VIX level** (`vix_level`) | High volatility = defensive tilt. |
| **High-yield OAS** (`hy_oas_bps`) | Credit stress indicator. |
| **Unemployment 6-month change** (`unemp_6m_change_pp`) | Rising unemployment = defensive tilt. |

The total score is mapped to an equity target:
- **Score = -3 → 25% equities**
- **Score = +3 → 75% equities**
- Steps rounded to your chosen increment (default 5%)

Hysteresis is applied so the target only changes if it differs from the last target by more than the set band (default ±5%).

---

## Installation

Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/Camilo-GC-Q/graham-portfolio-rebalancer.git
cd graham-rebalancer
python3 -m venv .venv
source .venv/bin/activate

