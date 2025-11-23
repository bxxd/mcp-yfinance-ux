#!/usr/bin/env python3
"""
Explore yfinance capabilities - what data can we actually get?
"""

import yfinance as yf
from pprint import pprint

def explore_ticker(symbol="AAPL"):
    """Explore what data yfinance provides for a ticker"""
    print(f"\n{'='*60}")
    print(f"EXPLORING: {symbol}")
    print(f"{'='*60}\n")

    ticker = yf.Ticker(symbol)

    # 1. Basic info (what we currently use)
    print("\n1. INFO (current implementation):")
    print("-" * 40)
    info = ticker.info
    print(f"Price: {info.get('regularMarketPrice') or info.get('currentPrice')}")
    print(f"Change %: {info.get('regularMarketChangePercent')}")
    print(f"Market Cap: {info.get('marketCap')}")
    print(f"Volume: {info.get('volume')}")

    # 2. Fast info (alternative to .info, faster)
    print("\n2. FAST_INFO (faster alternative):")
    print("-" * 40)
    try:
        fast = ticker.fast_info
        print(f"Available keys: {list(fast.keys()) if hasattr(fast, 'keys') else dir(fast)}")
        print(f"Last price: {fast.get('lastPrice') if hasattr(fast, 'get') else getattr(fast, 'last_price', None)}")
    except Exception as e:
        print(f"Error: {e}")

    # 3. News
    print("\n3. NEWS:")
    print("-" * 40)
    try:
        news = ticker.news[:3]  # First 3 articles
        for article in news:
            print(f"- {article.get('title')}")
            print(f"  {article.get('link')}")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Earnings
    print("\n4. EARNINGS:")
    print("-" * 40)
    try:
        earnings = ticker.earnings
        print(earnings.tail())
    except Exception as e:
        print(f"Error: {e}")

    # 5. Earnings dates
    print("\n5. EARNINGS DATES (next earnings):")
    print("-" * 40)
    try:
        earnings_dates = ticker.earnings_dates
        if earnings_dates is not None:
            print(earnings_dates.head())
    except Exception as e:
        print(f"Error: {e}")

    # 6. Calendar (upcoming events)
    print("\n6. CALENDAR (upcoming events):")
    print("-" * 40)
    try:
        calendar = ticker.calendar
        pprint(calendar)
    except Exception as e:
        print(f"Error: {e}")

    # 7. Analyst recommendations
    print("\n7. ANALYST RECOMMENDATIONS:")
    print("-" * 40)
    try:
        recommendations = ticker.recommendations
        if recommendations is not None:
            print(recommendations.tail())
    except Exception as e:
        print(f"Error: {e}")

    # 8. Analyst price targets
    print("\n8. ANALYST PRICE TARGETS:")
    print("-" * 40)
    try:
        targets = ticker.analyst_price_targets
        pprint(targets)
    except Exception as e:
        print(f"Error: {e}")

    # 9. Institutional holders
    print("\n9. INSTITUTIONAL HOLDERS:")
    print("-" * 40)
    try:
        holders = ticker.institutional_holders
        if holders is not None:
            print(holders.head())
    except Exception as e:
        print(f"Error: {e}")

    # 10. Insider transactions
    print("\n10. INSIDER TRANSACTIONS:")
    print("-" * 40)
    try:
        insider = ticker.insider_transactions
        if insider is not None:
            print(insider.head())
    except Exception as e:
        print(f"Error: {e}")

    # 11. Options (if available)
    print("\n11. OPTIONS:")
    print("-" * 40)
    try:
        options_dates = ticker.options
        print(f"Available expiration dates: {options_dates[:5] if options_dates else 'None'}")
        if options_dates:
            chain = ticker.option_chain(options_dates[0])
            print(f"\nSample calls:")
            print(chain.calls.head())
    except Exception as e:
        print(f"Error: {e}")

    # 12. Financials
    print("\n12. FINANCIALS (Income Statement):")
    print("-" * 40)
    try:
        financials = ticker.financials
        if financials is not None:
            print(financials.head())
    except Exception as e:
        print(f"Error: {e}")

    # 13. Balance Sheet
    print("\n13. BALANCE SHEET:")
    print("-" * 40)
    try:
        balance = ticker.balance_sheet
        if balance is not None:
            print(balance.head())
    except Exception as e:
        print(f"Error: {e}")

    # 14. Cash Flow
    print("\n14. CASH FLOW:")
    print("-" * 40)
    try:
        cashflow = ticker.cash_flow
        if cashflow is not None:
            print(cashflow.head())
    except Exception as e:
        print(f"Error: {e}")

    # 15. SEC Filings
    print("\n15. SEC FILINGS:")
    print("-" * 40)
    try:
        filings = ticker.sec_filings
        if filings is not None:
            print(filings.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Explore a few different types
    explore_ticker("AAPL")  # Mega cap tech
    # explore_ticker("TSLA")  # High volatility
    # explore_ticker("^GSPC") # Index
    # explore_ticker("BTC-USD") # Crypto
