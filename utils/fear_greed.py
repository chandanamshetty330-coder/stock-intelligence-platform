import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def calculate_fear_greed_index():
    """Calculate Fear & Greed Index from multiple indicators"""
    try:
        scores = {}

        # 1. Market Momentum (S&P 500 vs 125-day MA)
        sp500 = yf.Ticker("^GSPC")
        sp500_data = sp500.history(period="1y")
        if not sp500_data.empty:
            current = sp500_data['Close'].iloc[-1]
            ma125 = sp500_data['Close'].rolling(125).mean().iloc[-1]
            momentum = ((current - ma125) / ma125) * 100
            momentum_score = min(max((momentum + 10) * 5, 0), 100)
            scores['momentum'] = momentum_score

        # 2. Stock Price Strength (52-week highs vs lows)
        strength_score = 50
        try:
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="1y")
            if not spy_data.empty:
                high_52 = spy_data['High'].max()
                low_52 = spy_data['Low'].min()
                current_spy = spy_data['Close'].iloc[-1]
                position = (current_spy - low_52) / (high_52 - low_52) * 100
                strength_score = position
        except:
            pass
        scores['strength'] = strength_score

        # 3. Market Volatility (VIX-like measure)
        volatility_score = 50
        try:
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="3mo")
            if not spy_hist.empty:
                returns = spy_hist['Close'].pct_change().dropna()
                vol = returns.std() * np.sqrt(252) * 100
                volatility_score = max(0, min(100, 100 - (vol - 10) * 3))
        except:
            pass
        scores['volatility'] = volatility_score

        # 4. Market Momentum - RSI based
        rsi_score = 50
        try:
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="3mo")
            if not spy_data.empty:
                delta = spy_data['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_current = rsi.iloc[-1]
                rsi_score = rsi_current
        except:
            pass
        scores['rsi'] = rsi_score

        # 5. Safe Haven Demand (Stocks vs Bonds)
        safe_haven_score = 50
        try:
            tlt = yf.Ticker("TLT")
            spy = yf.Ticker("SPY")
            tlt_data = tlt.history(period="1mo")
            spy_data = spy.history(period="1mo")
            if not tlt_data.empty and not spy_data.empty:
                tlt_return = (tlt_data['Close'].iloc[-1] /
                             tlt_data['Close'].iloc[0] - 1) * 100
                spy_return = (spy_data['Close'].iloc[-1] /
                             spy_data['Close'].iloc[0] - 1) * 100
                diff = spy_return - tlt_return
                safe_haven_score = min(max((diff + 5) * 10, 0), 100)
        except:
            pass
        scores['safe_haven'] = safe_haven_score

        # Calculate weighted average
        weights = {
            'momentum': 0.25,
            'strength': 0.25,
            'volatility': 0.25,
            'rsi': 0.15,
            'safe_haven': 0.10
        }

        total_score = sum(scores.get(k, 50) * v
                         for k, v in weights.items())
        total_score = round(total_score, 1)

        # Determine sentiment
        if total_score >= 75:
            sentiment = "Extreme Greed"
            color = "#00C853"
            emoji = "🤑"
            description = "Investors are extremely greedy — market may be overvalued!"
        elif total_score >= 55:
            sentiment = "Greed"
            color = "#64DD17"
            emoji = "😀"
            description = "Investors are greedy — market showing bullish sentiment"
        elif total_score >= 45:
            sentiment = "Neutral"
            color = "#FFD600"
            emoji = "😐"
            description = "Market sentiment is neutral — wait and watch"
        elif total_score >= 25:
            sentiment = "Fear"
            color = "#FF6D00"
            emoji = "😨"
            description = "Investors are fearful — possible buying opportunity!"
        else:
            sentiment = "Extreme Fear"
            color = "#FF1744"
            emoji = "😱"
            description = "Investors in extreme fear — strong buying opportunity!"

        return {
            'score': total_score,
            'sentiment': sentiment,
            'color': color,
            'emoji': emoji,
            'description': description,
            'components': scores,
            'signal': 'BUY' if total_score < 30 else
                     'SELL' if total_score > 70 else 'HOLD'
        }

    except Exception as e:
        print(f"Fear Greed error: {e}")
        return {
            'score': 50,
            'sentiment': 'Neutral',
            'color': '#FFD600',
            'emoji': '😐',
            'description': 'Could not calculate index',
            'components': {},
            'signal': 'HOLD'
        }

def get_historical_fear_greed():
    """Generate historical fear greed data"""
    try:
        spy = yf.Ticker("SPY")
        data = spy.history(period="1y")
        if data.empty:
            return None

        dates = []
        scores = []

        # Calculate rolling fear greed
        for i in range(60, len(data), 5):
            subset = data.iloc[:i]
            # Simple RSI based score
            delta = subset['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            score = rsi.iloc[-1]
            if not np.isnan(score):
                dates.append(subset.index[-1])
                scores.append(round(float(score), 1))

        return pd.DataFrame({'Date': dates, 'Score': scores})
    except Exception as e:
        print(f"Historical FG error: {e}")
        return None