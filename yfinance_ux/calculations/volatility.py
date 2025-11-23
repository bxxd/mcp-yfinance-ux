"""
Volatility calculations for factor decomposition.

Idiosyncratic volatility (stock-specific risk) via factor regression.
Separates total volatility into market beta and idiosyncratic components.
"""

import numpy as np

from yfinance_ux.fetcher import fetch_ticker_and_market


def calculate_idio_vol(symbol: str) -> dict[str, float | None]:
    """Calculate idiosyncratic volatility (stock-specific risk after removing market exposure)"""
    try:
        # Fetch ticker and market data in parallel (12 months)
        hist_ticker, hist_market = fetch_ticker_and_market(symbol, months=12)

        min_history_len = 30
        if hist_ticker.empty or hist_market.empty:
            return {"idio_vol": None, "total_vol": None}

        if len(hist_ticker) < min_history_len or len(hist_market) < min_history_len:
            return {"idio_vol": None, "total_vol": None}

        # Calculate daily returns
        ticker_returns = hist_ticker["Close"].pct_change().dropna()
        market_returns = hist_market["Close"].pct_change().dropna()

        # Align dates (intersection)
        common_dates = ticker_returns.index.intersection(market_returns.index)
        ticker_returns = ticker_returns.loc[common_dates]
        market_returns = market_returns.loc[common_dates]

        if len(ticker_returns) < min_history_len:
            return {"idio_vol": None, "total_vol": None}

        # Total volatility (annualized)
        total_vol = float(ticker_returns.std() * np.sqrt(252) * 100)  # Convert to percentage

        # Linear regression: decompose returns into market (beta) and stock-specific (alpha)
        beta, alpha = np.polyfit(market_returns, ticker_returns, 1)

        # Residuals = idiosyncratic component (stock-specific risk)
        residuals = ticker_returns - (alpha + beta * market_returns)

        # Idiosyncratic volatility (annualized)
        idio_vol = float(residuals.std() * np.sqrt(252) * 100)  # Convert to percentage

        return {
            "idio_vol": idio_vol,
            "total_vol": total_vol,
        }
    except Exception:
        return {"idio_vol": None, "total_vol": None}
