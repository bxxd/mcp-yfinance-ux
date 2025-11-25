"""Black-Scholes greeks calculation."""

from math import exp, log, sqrt
from typing import TypedDict

from scipy.stats import norm


class Greeks(TypedDict):
    """Greeks for an option position."""

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def calculate_greeks(
    spot: float,
    strike: float,
    time_to_expiry: float,  # years
    volatility: float,  # annual, as decimal (e.g., 0.25 for 25%)
    risk_free_rate: float,  # annual, as decimal (e.g., 0.045 for 4.5%)
    dividend_yield: float = 0.0,  # annual, as decimal
    option_type: str = "call",  # "call" or "put"
) -> Greeks:
    """
    Calculate Black-Scholes greeks.

    Args:
        spot: Current stock price
        strike: Option strike price
        time_to_expiry: Time to expiration in years
        volatility: Implied volatility as decimal (0.25 = 25%)
        risk_free_rate: Risk-free rate as decimal (0.045 = 4.5%)
        dividend_yield: Dividend yield as decimal (0.02 = 2%)
        option_type: "call" or "put"

    Returns:
        Dict with keys: delta, gamma, vega, theta, rho

    Note:
        - Uses Black-Scholes model (European options)
        - American options may have different greeks (early exercise premium)
        - Approximation for educational/analysis use
    """
    # Handle edge cases
    if time_to_expiry <= 0:
        # Expired option
        if option_type == "call":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return Greeks(
            delta=delta,
            gamma=0.0,
            vega=0.0,
            theta=0.0,
            rho=0.0,
        )

    # d1, d2 calculation
    d1 = (
        log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry
    ) / (volatility * sqrt(time_to_expiry))
    d2 = d1 - volatility * sqrt(time_to_expiry)

    # Greeks (same formulas for calls/puts except delta/rho)
    if option_type == "call":
        delta = exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        rho = (
            strike
            * time_to_expiry
            * exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(d2)
            / 100
        )  # /100 for 1% change
    else:  # put
        delta = -exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        rho = (
            -strike
            * time_to_expiry
            * exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(-d2)
            / 100
        )

    # Gamma (same for calls and puts)
    gamma = exp(-dividend_yield * time_to_expiry) * norm.pdf(d1) / (
        spot * volatility * sqrt(time_to_expiry)
    )

    # Vega (same for calls and puts) - /100 for 1% volatility change
    vega = (
        spot
        * exp(-dividend_yield * time_to_expiry)
        * norm.pdf(d1)
        * sqrt(time_to_expiry)
        / 100
    )

    # Theta (different for calls/puts)
    if option_type == "call":
        theta = (
            -spot
            * norm.pdf(d1)
            * volatility
            * exp(-dividend_yield * time_to_expiry)
            / (2 * sqrt(time_to_expiry))
            - risk_free_rate
            * strike
            * exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(d2)
            + dividend_yield
            * spot
            * exp(-dividend_yield * time_to_expiry)
            * norm.cdf(d1)
        ) / 365  # Daily theta
    else:
        theta = (
            -spot
            * norm.pdf(d1)
            * volatility
            * exp(-dividend_yield * time_to_expiry)
            / (2 * sqrt(time_to_expiry))
            + risk_free_rate
            * strike
            * exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(-d2)
            - dividend_yield
            * spot
            * exp(-dividend_yield * time_to_expiry)
            * norm.cdf(-d1)
        ) / 365

    return Greeks(
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta,
        rho=rho,
    )
