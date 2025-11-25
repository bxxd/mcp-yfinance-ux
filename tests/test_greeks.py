#!/usr/bin/env python3
"""Test greeks calculation module."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yfinance_ux.calculations.greeks import calculate_greeks


def test_atm_call_greeks() -> None:
    """Test ATM call option greeks."""
    # ATM call: spot = strike
    greeks = calculate_greeks(
        spot=100.0,
        strike=100.0,
        time_to_expiry=0.25,  # 3 months
        volatility=0.25,  # 25% IV
        risk_free_rate=0.045,  # 4.5%
        dividend_yield=0.0,
        option_type="call",
    )

    # ATM call delta should be around 0.5 (slightly higher with positive risk-free rate)
    assert 0.45 < greeks["delta"] < 0.65, f"ATM call delta {greeks['delta']} not near 0.5"

    # Gamma should be positive
    assert greeks["gamma"] > 0, "Gamma should be positive"

    # Vega should be positive
    assert greeks["vega"] > 0, "Vega should be positive"

    # Theta should be negative (time decay)
    assert greeks["theta"] < 0, "Theta should be negative"

    print(f"✓ ATM call greeks: delta={greeks['delta']:.3f}, gamma={greeks['gamma']:.3f}, "
          f"vega={greeks['vega']:.3f}, theta={greeks['theta']:.3f}")


def test_atm_put_greeks() -> None:
    """Test ATM put option greeks."""
    greeks = calculate_greeks(
        spot=100.0,
        strike=100.0,
        time_to_expiry=0.25,  # 3 months
        volatility=0.25,  # 25% IV
        risk_free_rate=0.045,
        dividend_yield=0.0,
        option_type="put",
    )

    # ATM put delta should be around -0.5 (slightly less negative with positive risk-free rate)
    assert -0.65 < greeks["delta"] < -0.35, f"ATM put delta {greeks['delta']} not near -0.5"

    # Gamma should be positive (same as call)
    assert greeks["gamma"] > 0, "Gamma should be positive"

    # Vega should be positive (same as call)
    assert greeks["vega"] > 0, "Vega should be positive"

    # Theta should be negative
    assert greeks["theta"] < 0, "Theta should be negative"

    print(f"✓ ATM put greeks: delta={greeks['delta']:.3f}, gamma={greeks['gamma']:.3f}, "
          f"vega={greeks['vega']:.3f}, theta={greeks['theta']:.3f}")


def test_itm_call_greeks() -> None:
    """Test ITM call option greeks."""
    # ITM call: spot > strike
    greeks = calculate_greeks(
        spot=110.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.25,
        risk_free_rate=0.045,
        dividend_yield=0.0,
        option_type="call",
    )

    # ITM call delta should be > 0.5
    assert greeks["delta"] > 0.5, "ITM call delta should be > 0.5"

    print(f"✓ ITM call delta: {greeks['delta']:.3f} (> 0.5)")


def test_otm_call_greeks() -> None:
    """Test OTM call option greeks."""
    # OTM call: spot < strike
    greeks = calculate_greeks(
        spot=90.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.25,
        risk_free_rate=0.045,
        dividend_yield=0.0,
        option_type="call",
    )

    # OTM call delta should be < 0.5
    assert greeks["delta"] < 0.5, "OTM call delta should be < 0.5"

    print(f"✓ OTM call delta: {greeks['delta']:.3f} (< 0.5)")


def test_expired_option() -> None:
    """Test greeks for expired option."""
    # Expired ITM call
    greeks = calculate_greeks(
        spot=110.0,
        strike=100.0,
        time_to_expiry=0.0,  # Expired
        volatility=0.25,
        risk_free_rate=0.045,
        dividend_yield=0.0,
        option_type="call",
    )

    # Expired ITM call should have delta = 1
    assert greeks["delta"] == 1.0, "Expired ITM call delta should be 1.0"
    assert greeks["gamma"] == 0.0, "Expired option gamma should be 0"
    assert greeks["vega"] == 0.0, "Expired option vega should be 0"
    assert greeks["theta"] == 0.0, "Expired option theta should be 0"

    print("✓ Expired option greeks correct")


def test_put_call_parity() -> None:
    """Test that put-call parity holds for greeks."""
    spot = 100.0
    strike = 100.0
    dte = 0.25
    vol = 0.25
    rfr = 0.045
    div = 0.0

    call_greeks = calculate_greeks(
        spot=spot,
        strike=strike,
        time_to_expiry=dte,
        volatility=vol,
        risk_free_rate=rfr,
        dividend_yield=div,
        option_type="call",
    )

    put_greeks = calculate_greeks(
        spot=spot,
        strike=strike,
        time_to_expiry=dte,
        volatility=vol,
        risk_free_rate=rfr,
        dividend_yield=div,
        option_type="put",
    )

    # Call delta - Put delta should be close to 1 (adjusted for dividends)
    delta_diff = call_greeks["delta"] - put_greeks["delta"]
    expected_diff = 1.0  # For non-dividend stocks
    assert abs(delta_diff - expected_diff) < 0.01, \
        f"Put-call parity: delta diff {delta_diff:.3f} should be near {expected_diff}"

    # Gamma should be the same
    assert abs(call_greeks["gamma"] - put_greeks["gamma"]) < 0.001, \
        "Gamma should be same for call and put"

    # Vega should be the same
    assert abs(call_greeks["vega"] - put_greeks["vega"]) < 0.001, \
        "Vega should be same for call and put"

    print(f"✓ Put-call parity: delta diff={delta_diff:.3f}, "
          f"gamma same={abs(call_greeks['gamma'] - put_greeks['gamma']) < 0.001}")


if __name__ == "__main__":
    print("Testing greeks calculation module...\n")

    test_atm_call_greeks()
    test_atm_put_greeks()
    test_itm_call_greeks()
    test_otm_call_greeks()
    test_expired_option()
    test_put_call_parity()

    print("\nAll greeks tests passed! ✓")
