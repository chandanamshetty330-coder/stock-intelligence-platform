import yfinance as yf
import pandas as pd
import numpy as np

def get_comparison_data(tickers, period='1y'):
    """Get data for multiple stocks for comparison"""
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            df.reset_index(inplace=True)
            data[ticker] = df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    return data

def get_normalized_prices(data):
    """Normalize prices to 100 for comparison"""
    normalized = {}
    for ticker, df in data.items():
        if not df.empty:
            first_price = df['Close'].iloc[0]
            normalized[ticker] = (df['Close'] / first_price * 100).values
    return normalized

def get_performance_metrics(data):
    """Calculate performance metrics for each stock"""
    metrics = []
    for ticker, df in data.items():
        if not df.empty:
            start_price = df['Close'].iloc[0]
            end_price = df['Close'].iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            daily_returns = df['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100
            sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
            max_price = df['High'].max()
            min_price = df['Low'].min()
            avg_volume = df['Volume'].mean()

            metrics.append({
                'Ticker': ticker,
                'Start Price': f"${start_price:.2f}",
                'Current Price': f"${end_price:.2f}",
                'Total Return': f"{total_return:+.2f}%",
                'Volatility': f"{volatility:.2f}%",
                'Sharpe Ratio': f"{sharpe:.2f}",
                '52W High': f"${max_price:.2f}",
                '52W Low': f"${min_price:.2f}",
                'Avg Volume': f"{avg_volume:,.0f}",
                'Return_Value': total_return
            })
    return pd.DataFrame(metrics)

def get_correlation_matrix(data):
    """Calculate correlation between stocks"""
    prices = {}
    for ticker, df in data.items():
        if not df.empty:
            prices[ticker] = df['Close'].values[:min(
                len(df), min(len(d) for d in data.values()))]
    
    min_len = min(len(v) for v in prices.values())
    price_df = pd.DataFrame(
        {k: v[:min_len] for k, v in prices.items()})
    return price_df.corr()