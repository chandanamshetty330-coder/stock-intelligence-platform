import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_stock_data(ticker, period='1y'):
    """Fetch live stock data from Yahoo Finance"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    df.reset_index(inplace=True)
    return df

def get_stock_info(ticker):
    """Get company information"""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        'name': info.get('longName', ticker),
        'sector': info.get('sector', 'N/A'),
        'current_price': info.get('currentPrice', 0),
        'market_cap': info.get('marketCap', 0),
        'pe_ratio': info.get('trailingPE', 0),
        'high_52week': info.get('fiftyTwoWeekHigh', 0),
        'low_52week': info.get('fiftyTwoWeekLow', 0),
        'volume': info.get('volume', 0),
        'description': info.get('longBusinessSummary', 'N/A')
    }

def get_multiple_stocks(tickers):
    """Fetch data for multiple stocks"""
    data = {}
    for ticker in tickers:
        try:
            data[ticker] = get_stock_data(ticker, period='1mo')
        except:
            pass
    return data

def get_live_price(ticker):
    """Get live real-time stock price"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d', interval='1m')
        if not data.empty:
            current = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2] if len(data) > 1 else current
            change = current - prev
            change_pct = (change / prev * 100) if prev else 0
            volume = data['Volume'].iloc[-1]
            high = data['High'].max()
            low = data['Low'].min()
            return {
                'price': round(float(current), 2),
                'change': round(float(change), 2),
                'change_pct': round(float(change_pct), 2),
                'volume': int(volume),
                'high': round(float(high), 2),
                'low': round(float(low), 2),
                'timestamp': data.index[-1].strftime('%H:%M:%S'),
                'data': data
            }
    except Exception as e:
        print(f"Live price error: {e}")
        return None

def get_live_chart_data(ticker):
    """Get today's minute-by-minute data"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period='1d', interval='1m')
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        print(f"Live chart error: {e}")
        return None
    
def search_ticker(query):
    """Search for a stock ticker/company by name or symbol using Yahoo Finance"""
    import requests
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"q": query, "quotesCount": 8, "newsCount": 0}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        results = []
        for item in data.get('quotes', []):
            if item.get('quoteType') in ('EQUITY', 'ETF'):
                results.append({
                    'symbol': item.get('symbol', ''),
                    'name': item.get('shortname') or item.get('longname') or item.get('symbol', ''),
                    'exchange': item.get('exchange', '')
                })
        return results
    except Exception as e:
        print(f"Ticker search error: {e}")
        return []

def get_index_data(index_symbol, period='1y'):
    """Fetch data for a major market index"""
    return get_stock_data(index_symbol, period)

def get_custom_range_data(ticker, start_date, end_date):
    """Fetch historical data for a stock between two specific dates"""
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    df.reset_index(inplace=True)
    return df

def get_usd_to_inr_rate():
    """Fetch live USD to INR exchange rate, cached in session to avoid repeated calls"""
    import requests
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        data = response.json()
        return data['rates']['INR']
    except Exception as e:
        print(f"Exchange rate error: {e}")
        return 83.0  # fallback approximate rate

def format_currency(amount, currency='USD', rate=83.0):
    """Format a USD amount in the user's preferred currency"""
    if currency == 'INR':
        converted = amount * rate
        return f"₹{converted:,.2f}"
    return f"${amount:,.2f}"        