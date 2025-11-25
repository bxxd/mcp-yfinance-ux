# Task: Add Black-Scholes Greeks Calculation to Options

**Priority**: Medium (nice-to-have, enhances educational/analysis value)

**Status**: Not started

**Context**: Twitter user wants "real-time option chains, view the Greeks, implied volatility, volume, and open interest"

We have: IV, volume, OI, skew, term structure
We DON'T have: Delta, gamma, vega, theta, rho

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Problem

yfinance doesn't provide greeks (Yahoo Finance doesn't show them on web UI).

Current `ticker_options()` output has no greeks beyond IV.

Users who want to analyze options strategies need:
- Delta (directional exposure)
- Gamma (delta sensitivity)
- Vega (IV sensitivity)
- Theta (time decay)
- Rho (interest rate sensitivity)

## Solution: Black-Scholes Approximation

Calculate greeks ourselves using Black-Scholes model.

**Input data we already have:**
- Stock price (current_price)
- Strike price (from chain)
- Time to expiration (DTE)
- Implied volatility (from yfinance)
- Dividend yield (ticker.info['dividendYield'])

**Need to fetch:**
- Risk-free rate (10Y Treasury from FRED or approximate ~4.5%)

**Limitations:**
- B-S assumes European options (stocks are American)
- Approximation, not exact (exchange calculates differently)
- Good enough for learning/educational use
- NOT for institutional trading (would need Polygon for that)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Implementation Plan

### 1. Create greeks calculation module

**File**: `yfinance_ux/calculations/greeks.py`

```python
"""Black-Scholes greeks calculation."""

from math import exp, log, sqrt
from scipy.stats import norm

def calculate_greeks(
    spot: float,
    strike: float,
    time_to_expiry: float,  # years
    volatility: float,  # annual, as decimal (e.g., 0.25 for 25%)
    risk_free_rate: float,  # annual, as decimal (e.g., 0.045 for 4.5%)
    dividend_yield: float = 0.0,  # annual, as decimal
    option_type: str = "call"  # "call" or "put"
) -> dict[str, float]:
    """
    Calculate Black-Scholes greeks.

    Returns:
        dict with keys: delta, gamma, vega, theta, rho
    """
    # Handle edge cases
    if time_to_expiry <= 0:
        # Expired option
        if option_type == "call":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return {
            "delta": delta,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
        }

    # d1, d2 calculation
    d1 = (log(spot / strike) + (risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry) / (volatility * sqrt(time_to_expiry))
    d2 = d1 - volatility * sqrt(time_to_expiry)

    # Greeks (same formulas for calls/puts except delta/rho)
    if option_type == "call":
        delta = exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        rho = strike * time_to_expiry * exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100  # /100 for 1% change
    else:  # put
        delta = -exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        rho = -strike * time_to_expiry * exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100

    # Gamma (same for calls and puts)
    gamma = exp(-dividend_yield * time_to_expiry) * norm.pdf(d1) / (spot * volatility * sqrt(time_to_expiry))

    # Vega (same for calls and puts) - /100 for 1% volatility change
    vega = spot * exp(-dividend_yield * time_to_expiry) * norm.pdf(d1) * sqrt(time_to_expiry) / 100

    # Theta (different for calls/puts)
    if option_type == "call":
        theta = (
            -spot * norm.pdf(d1) * volatility * exp(-dividend_yield * time_to_expiry) / (2 * sqrt(time_to_expiry))
            - risk_free_rate * strike * exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            + dividend_yield * spot * exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        ) / 365  # Daily theta
    else:
        theta = (
            -spot * norm.pdf(d1) * volatility * exp(-dividend_yield * time_to_expiry) / (2 * sqrt(time_to_expiry))
            + risk_free_rate * strike * exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            - dividend_yield * spot * exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        ) / 365

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
    }
```

### 2. Integrate into options service

**File**: `yfinance_ux/services/options.py`

Add greeks calculation for each strike:

```python
# After fetching option chain
calls["delta"] = calls.apply(
    lambda row: calculate_greeks(
        spot=current_price,
        strike=row["strike"],
        time_to_expiry=dte/365,
        volatility=row["impliedVolatility"],
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        option_type="call"
    )["delta"],
    axis=1
)
# ... same for gamma, vega, theta, rho
```

### 3. Add to formatter output

**File**: `mcp_yfinance_ux/formatters/options.py`

Add greeks columns to top strikes display:

```
TOP POSITIONS BY OI (Top 10)
CALLS
Strike    OI      Vol     Last    IV      Delta   Gamma   Vega    Theta
──────────────────────────────────────────────────────────────────────────
$100   10,000  5,000   $5.20  45.2%   0.65    0.03    0.25   -0.08
...
```

### 4. Risk-free rate source

**Options:**

**A. Hardcode approximate** (simplest, good enough)
```python
RISK_FREE_RATE = 0.045  # 4.5% (update quarterly)
```

**B. Fetch from yfinance** (^TNX = 10Y Treasury)
```python
def get_risk_free_rate() -> float:
    """Fetch 10Y Treasury yield as risk-free rate."""
    try:
        tnx = yf.Ticker("^TNX")
        rate = tnx.fast_info.get("lastPrice", 4.5) / 100  # TNX is in %, convert to decimal
        return rate
    except:
        return 0.045  # Fallback to 4.5%
```

**C. Fetch from FRED** (overkill, requires API key)

**Recommendation**: Option B (fetch ^TNX from yfinance, fallback to 4.5%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Testing

```bash
# Test greeks calculation
./cli options AAPL

# Should show:
# - Delta, gamma, vega, theta, rho for each strike
# - ATM greeks summary
# - Greeks interpretation (if ATM delta ~0.5, etc.)
```

## Dependencies

Add `scipy` to pyproject.toml (for `norm.cdf`, `norm.pdf`):

```toml
[tool.poetry.dependencies]
scipy = "^1.11.0"
```

Already have numpy (scipy depends on it).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Output Example (After Implementation)

```
AAPL US EQUITY                          OPTIONS ANALYSIS
Last: $150.25                           Exp: 2025-01-17 (55d)  |  ATM: $150

POSITIONING (Open Interest)
Calls:  125,000 OI
Puts:   95,000 OI
P/C Ratio:  0.76    ← BULLISH (calls 1.3x puts)

TOP POSITIONS BY OI (Top 10)
CALLS
Strike    OI      Vol     Last    IV      Delta   Gamma   Theta
──────────────────────────────────────────────────────────────────
$150   10,250  5,120   $5.20  28.5%   0.52    0.032   -0.08
$155    8,500  3,200   $2.80  30.1%   0.35    0.028   -0.06
$145   12,100  4,500   $8.10  27.2%   0.68    0.025   -0.09
...

GREEKS SUMMARY (ATM Strike: $150)
Call Delta:   0.52  (52% stock exposure)
Call Gamma:   0.032 (delta changes 3.2% per $1 stock move)
Call Vega:    0.25  (option gains $0.25 per 1% IV increase)
Call Theta:  -0.08  (loses $0.08/day from time decay)

...
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Acceptance Criteria

- [ ] `calculate_greeks()` function in `yfinance_ux/calculations/greeks.py`
- [ ] Unit tests for greeks calculation
- [ ] Greeks added to option chain dataframes (calls/puts)
- [ ] Greeks displayed in formatter output (top strikes + ATM summary)
- [ ] Risk-free rate fetched from ^TNX with fallback
- [ ] Documentation updated (DEVELOPER.md)
- [ ] `make all` passes (lint + test)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Alternative: Polygon.io (Don't Do This Yet)

If users demand real-time + exchange-calculated greeks:

**Polygon.io Options API:**
- Real-time options chains
- Exchange-calculated greeks (accurate)
- Historical options data
- Options flow / block trades

**Cost:** $200/mo starter, $1000/mo real-time

**When to do this:** Only if users prove they need it (actual demand).

**For now:** B-S approximation is good enough for educational/learning use case.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## References

- Black-Scholes formula: https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
- Greeks calculation: https://en.wikipedia.org/wiki/Greeks_(finance)
- scipy.stats.norm: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Created: November 23, 2025
Priority: Medium (enhances educational value, not critical)
Estimate: 2-3 hours implementation + testing
