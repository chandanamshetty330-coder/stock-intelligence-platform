import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.stock_data import (get_stock_data, get_stock_info,
                               get_live_price, get_live_chart_data,
                               search_ticker, get_index_data,
                               get_custom_range_data,
                               get_usd_to_inr_rate, format_currency)
from utils.sentiment import get_overall_sentiment
from utils.prediction import (predict_future, calculate_metrics,
                               train_lstm_model, predict_future_lstm)
from utils.auth import (is_authenticated, get_current_user, sign_out,
                        save_portfolio, get_portfolio, delete_portfolio_item,
                        save_alert, get_alerts,
                        save_watchlist, get_watchlist, delete_watchlist_item,
                        save_trade, get_trade_history, delete_trade_item,
                        get_profile, upsert_profile, upload_avatar,
                        update_display_name, change_password, delete_account)
from utils.comparison import (get_comparison_data, get_normalized_prices,
                               get_performance_metrics, get_correlation_matrix)
from utils.fear_greed import calculate_fear_greed_index, get_historical_fear_greed
from utils.pdf_report import generate_stock_report, save_report
from app.login import show_login_page
from utils.notifications import send_alert_email

# Page config
st.set_page_config(
    page_title="AI Stock Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'app_theme' not in st.session_state:
    st.session_state.app_theme = 'Dark'

if st.session_state.app_theme == 'Light':
    theme_css = """
    <style>
        .stApp { background-color: #ffffff; color: #1a1a1a; }
        [data-testid="stSidebar"] { background-color: #f0f2f6; }
        .stMarkdown, .stMarkdown p, label, .stSelectbox label { color: #1a1a1a !important; }
        [data-testid="stMetricValue"] { color: #1a1a1a !important; }
        [data-testid="stMetricLabel"] { color: #444444 !important; }
    </style>
    """
else:
    theme_css = """
    <style>
        .stApp { background-color: #0e1117; color: #fafafa; }
    </style>
    """
st.markdown(theme_css, unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00C853, #1565C0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .user-badge {
        background: linear-gradient(135deg, #1e1e2e, #2d2d44);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        border: 1px solid #00C853;
        color: #00C853;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Popular stocks
STOCKS = {
    'Apple (AAPL)': 'AAPL',
    'Tesla (TSLA)': 'TSLA',
    'Google (GOOGL)': 'GOOGL',
    'Microsoft (MSFT)': 'MSFT',
    'Amazon (AMZN)': 'AMZN',
    'Infosys (INFY)': 'INFY',
    'TCS (TCS.NS)': 'TCS.NS',
    'Wipro (WIPRO.NS)': 'WIPRO.NS',
    'HDFC Bank (HDFCBANK.NS)': 'HDFCBANK.NS',
    'Reliance (RELIANCE.NS)': 'RELIANCE.NS'
}

# ==========================================
# AUTHENTICATION CHECK
# ==========================================
if not is_authenticated():
    show_login_page()
    st.stop()

# Get current user
# Get current user
user = get_current_user()
user_id = user.id
user_name = user.user_metadata.get('full_name', 'User')
user_email = user.email

# Load currency preference and exchange rate once per session
if 'user_currency' not in st.session_state:
    profile_check = get_profile(user_id) or {}
    st.session_state.user_currency = profile_check.get('currency', 'USD')
if 'inr_rate' not in st.session_state:
    st.session_state.inr_rate = get_usd_to_inr_rate()

user_currency = st.session_state.user_currency
inr_rate = st.session_state.inr_rate

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("## 📈 AI Stock Intelligence")
st.sidebar.markdown("---")

st.sidebar.markdown(f"""
<div class="user-badge">
    👤 {user_name}<br>
    <small>{user_email}</small>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

page = st.sidebar.radio("🧭 Navigation", [
    "🏠 Dashboard",
    "🔴 Live Predictions",
    "📊 Stock Analysis",
    "📈 Stock Comparison",
    "🕰️ Market History",
    "😱 Fear & Greed Index",
    "🤖 AI Predictions",
    "📰 News Sentiment",
    "⭐ Watchlist",
    "💼 My Portfolio",
    "📜 Trade History",
    "🚨 Price Alerts",
    "👤 My Profile"
])

st.sidebar.markdown("---")
st.sidebar.markdown("**🔍 Search Any Stock**")

search_query = st.sidebar.text_input(
    "Type a company name or ticker",
    placeholder="e.g. Netflix, TSLA, Infosys",
    key="stock_search_box")

if 'search_results' not in st.session_state:
    st.session_state.search_results = {}
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = 'AAPL'
    st.session_state.active_name = 'Apple (AAPL)'

if search_query:
    with st.sidebar:
        with st.spinner("Searching..."):
            found = search_ticker(search_query)
        if found:
            options = {f"{r['name']} ({r['symbol']})": r['symbol'] for r in found}
            st.session_state.search_results = options
            picked = st.selectbox("Select a match", list(options.keys()), key="search_pick")
            if st.button("✅ Use this stock", use_container_width=True):
                st.session_state.active_ticker = options[picked]
                st.session_state.active_name = picked
                st.rerun()
        else:
            st.warning("No matches found. Try a different name.")

st.sidebar.markdown(f"**Currently viewing:** {st.session_state.active_name}")

selected_stock_name = st.session_state.active_name
selected_ticker = st.session_state.active_ticker

st.sidebar.markdown("---")
period = st.sidebar.selectbox(
    "📅 Time Period",
    ['1mo', '3mo', '6mo', '1y', '2y'],
    index=3
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("**Model:** LSTM + VADER")
st.sidebar.markdown("**DB:** Supabase")

# ==========================================
# PAGE 1 — DASHBOARD
# ==========================================
if page == "🏠 Dashboard":
    st.markdown('<p class="main-header">🤖 AI Stock Intelligence Platform</p>',
                unsafe_allow_html=True)
    st.markdown(f"**Welcome back, {user_name}!** 👋 Real-time stock analysis powered by ML & NLP")
    st.markdown("---")

    with st.spinner(f"Loading {selected_stock_name} data..."):
        info = get_stock_info(selected_ticker)
        df = get_stock_data(selected_ticker, period)
        df = calculate_metrics(df)

    col1, col2, col3, col4 = st.columns(4)
    current_price = info.get('current_price', 0)
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price * 100) if prev_price else 0

    with col1:
        st.metric("💰 Current Price",
                  format_currency(current_price, user_currency, inr_rate),
                  f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
    with col2:
        st.metric("📊 52W High", format_currency(info.get('high_52week', 0), user_currency, inr_rate))
    with col3:
        st.metric("📉 52W Low", format_currency(info.get('low_52week', 0), user_currency, inr_rate))
    with col4:
        market_cap = info.get('market_cap', 0)
        st.metric("🏢 Market Cap",
                  f"${market_cap/1e9:.1f}B" if market_cap > 1e9
                  else f"${market_cap/1e6:.1f}M")

    st.markdown("---")
    st.subheader(f"📈 {selected_stock_name} Price Chart")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Price'
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['MA20'],
        name='MA20', line=dict(color='orange', width=1)
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['MA50'],
        name='MA50', line=dict(color='blue', width=1)
    ))
    fig.update_layout(
        title=f"{selected_stock_name} - Candlestick Chart",
        yaxis_title="Price (USD)", xaxis_title="Date",
        height=500, template='plotly_dark',
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Trading Volume")
        fig_vol = px.bar(df, x='Date', y='Volume',
                         color='Volume', color_continuous_scale='Greens',
                         template='plotly_dark')
        fig_vol.update_layout(height=300)
        st.plotly_chart(fig_vol, use_container_width=True)

    with col2:
        st.subheader("📈 Daily Returns")
        fig_ret = px.line(df, x='Date', y='Daily_Return',
                          template='plotly_dark',
                          color_discrete_sequence=['#00C853'])
        fig_ret.add_hline(y=0, line_dash="dash", line_color="white")
        fig_ret.update_layout(height=300)
        st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("---")
    st.subheader("🏢 Company Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Company:** {info.get('name', 'N/A')}")
        st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
        st.markdown(f"**P/E Ratio:** {info.get('pe_ratio', 'N/A')}")
    with col2:
        st.markdown(f"**Volume:** {info.get('volume', 0):,}")
        st.markdown(f"**Ticker:** {selected_ticker}")
    with st.expander("📖 Company Description"):
        st.write(info.get('description', 'N/A'))

    # ==========================================
    # PDF REPORT DOWNLOAD
    # ==========================================
    st.markdown("---")
    st.subheader("📄 Download Stock Report")
    st.info("Generate a comprehensive PDF report with price analysis, sentiment, predictions and more!")

    if st.button("📥 Generate PDF Report", type="secondary",
                 use_container_width=True):
        with st.spinner("⏳ Generating PDF report... Please wait..."):
            try:
                company_name = selected_stock_name.split('(')[0].strip()
                sentiment_data = get_overall_sentiment(company_name)
                fear_greed_data = calculate_fear_greed_index()
                portfolio_data = get_portfolio(user_id)

                pdf = generate_stock_report(
                    stock_name=selected_stock_name,
                    ticker=selected_ticker,
                    stock_info=info,
                    df=df,
                    sentiment_data=sentiment_data,
                    fear_greed=fear_greed_data,
                    portfolio=portfolio_data
                )
                pdf_bytes = save_report(pdf)

                filename = f"{selected_ticker}_report_{datetime.now().strftime('%Y%m%d')}.pdf"

                st.download_button(
                    label="📥 Click Here to Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success(f"✅ PDF Report generated successfully! File: {filename}")

            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")

# ==========================================
# PAGE 2 — LIVE PREDICTIONS
# ==========================================
elif page == "🔴 Live Predictions":
    st.markdown("## 🔴 Live Stock Predictions")
    st.markdown("**Real-time price updates every 60 seconds**")
    st.markdown("---")

    refresh_rate = st.sidebar.slider(
        "🔄 Refresh Rate (seconds)", 10, 120, 60)

    live_data = get_live_price(selected_ticker)

    if live_data:
        price_color = "green" if live_data['change'] >= 0 else "red"
        arrow = "▲" if live_data['change'] >= 0 else "▼"

        st.markdown(f"""
        <div style='background: #1e1e2e; border-radius: 15px;
                    padding: 1.5rem; border: 2px solid {price_color};
                    text-align: center; margin-bottom: 1rem;'>
            <h1 style='color: white; margin: 0;'>{selected_stock_name}</h1>
            <h1 style='color: {price_color}; font-size: 3rem; margin: 0;'>
                ${live_data['price']:.2f}
            </h1>
            <h3 style='color: {price_color}; margin: 0;'>
                {arrow} {live_data['change']:+.2f}
                ({live_data['change_pct']:+.2f}%)
            </h3>
            <p style='color: #888; margin: 0;'>
                Last updated: {live_data['timestamp']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Live Price", f"${live_data['price']:.2f}",
                     f"{live_data['change']:+.2f}")
        with col2:
            st.metric("📈 Day High", f"${live_data['high']:.2f}")
        with col3:
            st.metric("📉 Day Low", f"${live_data['low']:.2f}")
        with col4:
            st.metric("📊 Volume", f"{live_data['volume']:,}")

        st.markdown("---")
        st.subheader("📈 Live Price Chart (Today - 1 Min)")
        chart_data = get_live_chart_data(selected_ticker)

        if chart_data is not None and not chart_data.empty:
            fig_live = go.Figure()
            fig_live.add_trace(go.Candlestick(
                x=chart_data['Datetime'],
                open=chart_data['Open'],
                high=chart_data['High'],
                low=chart_data['Low'],
                close=chart_data['Close'],
                name='Live Price'
            ))
            fig_live.add_trace(go.Bar(
                x=chart_data['Datetime'],
                y=chart_data['Volume'],
                name='Volume',
                yaxis='y2',
                opacity=0.3,
                marker_color='rgba(0, 200, 83, 0.5)'
            ))
            fig_live.update_layout(
                title=f"🔴 LIVE — {selected_stock_name} (1-Minute Chart)",
                height=500, template='plotly_dark',
                xaxis_rangeslider_visible=False,
                yaxis2=dict(overlaying='y', side='right', showgrid=False)
            )
            st.plotly_chart(fig_live, use_container_width=True)

            st.subheader("📊 Price Movement Today")
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=chart_data['Datetime'],
                y=chart_data['Close'],
                mode='lines', name='Price',
                line=dict(color='#00C853' if live_data['change'] >= 0
                         else '#FF1744', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 200, 83, 0.1)' if live_data['change'] >= 0
                         else 'rgba(255, 23, 68, 0.1)'
            ))
            fig_line.update_layout(
                height=300, template='plotly_dark',
                yaxis_title="Price ($)"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")
        st.subheader("🤖 Live AI Signal")

        if chart_data is not None and len(chart_data) > 10:
            recent_prices = chart_data['Close'].tail(10).values
            momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            avg_volume = chart_data['Volume'].tail(10).mean()
            current_volume = chart_data['Volume'].iloc[-1]
            volume_signal = current_volume > avg_volume * 1.5

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 10-Min Momentum", f"{momentum:+.2f}%",
                         "Bullish" if momentum > 0 else "Bearish")
            with col2:
                st.metric("📊 Volume Signal",
                         "HIGH 🔥" if volume_signal else "Normal",
                         "Above average" if volume_signal else "Normal")
            with col3:
                st.metric("⚡ Today's Change", f"{live_data['change_pct']:+.2f}%")

            st.markdown("### 🎯 AI Trading Signal")
            if momentum > 0.5 and live_data['change'] > 0:
                st.success(f"""
                🟢 **STRONG BUY SIGNAL**
                - Price UP {live_data['change_pct']:+.2f}% today
                - 10-min momentum: +{momentum:.2f}%
                - {'High volume confirms trend! 🔥' if volume_signal else 'Normal volume'}
                """)
            elif momentum < -0.5 and live_data['change'] < 0:
                st.error(f"""
                🔴 **STRONG SELL SIGNAL**
                - Price DOWN {live_data['change_pct']:+.2f}% today
                - 10-min momentum: {momentum:.2f}%
                - {'High volume confirms downtrend! ⚠️' if volume_signal else 'Normal volume'}
                """)
            else:
                st.warning(f"""
                🟡 **HOLD / NEUTRAL SIGNAL**
                - Price change: {live_data['change_pct']:+.2f}% today
                - 10-min momentum: {momentum:+.2f}%
                - Market consolidating
                """)

        st.markdown("---")
        st.info(f"🔄 Auto-refreshing every {refresh_rate} seconds...")
        time.sleep(refresh_rate)
        st.rerun()

    else:
        st.error("❌ Could not fetch live data. Market may be closed.")
        st.info("💡 Live data available during market hours (US: 9:30 AM - 4:00 PM EST | India: 9:15 AM - 3:30 PM IST)")

# ==========================================
# PAGE 3 — STOCK ANALYSIS
# ==========================================
elif page == "📊 Stock Analysis":
    st.markdown("## 📊 Technical Analysis")
    st.markdown("---")

    with st.spinner("Loading technical indicators..."):
        df = get_stock_data(selected_ticker, period)
        df = calculate_metrics(df)

    st.subheader("📉 RSI (Relative Strength Index)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df['Date'], y=df['RSI'],
        name='RSI', line=dict(color='purple', width=2)
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",
                      annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green",
                      annotation_text="Oversold (30)")
    fig_rsi.update_layout(height=300, template='plotly_dark')
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.subheader("📊 Bollinger Bands")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(
        x=df['Date'], y=df['Close'],
        name='Price', line=dict(color='white', width=2)
    ))
    fig_bb.add_trace(go.Scatter(
        x=df['Date'], y=df['BB_upper'],
        name='Upper Band', line=dict(color='red', width=1, dash='dash')
    ))
    fig_bb.add_trace(go.Scatter(
        x=df['Date'], y=df['BB_lower'],
        name='Lower Band', line=dict(color='green', width=1, dash='dash'),
        fill='tonexty', fillcolor='rgba(0,100,80,0.1)'
    ))
    fig_bb.add_trace(go.Scatter(
        x=df['Date'], y=df['BB_middle'],
        name='Middle Band', line=dict(color='orange', width=1)
    ))
    fig_bb.update_layout(height=400, template='plotly_dark')
    st.plotly_chart(fig_bb, use_container_width=True)

    st.subheader("📊 MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(
        x=df['Date'], y=df['MACD'],
        name='MACD', line=dict(color='#00C853', width=2)
    ))
    fig_macd.add_trace(go.Scatter(
        x=df['Date'], y=df['Signal'],
        name='Signal', line=dict(color='#FF6D00', width=2)
    ))
    fig_macd.add_hline(y=0, line_dash="dash", line_color="white")
    fig_macd.update_layout(height=300, template='plotly_dark')
    st.plotly_chart(fig_macd, use_container_width=True)

    st.subheader("📋 Statistical Summary")
    stats = df[['Open', 'High', 'Low', 'Close', 'Volume']].describe()
    st.dataframe(stats.style.background_gradient(cmap='Greens'),
                 use_container_width=True)

# ==========================================
# PAGE 4 — STOCK COMPARISON
# ==========================================
elif page == "📈 Stock Comparison":
    st.markdown("## 📈 Stock Comparison")
    st.markdown("**Compare multiple stocks side by side**")
    st.markdown("---")

    st.subheader("🔍 Select Stocks to Compare")
    col1, col2, col3 = st.columns(3)
    with col1:
        stock1 = st.selectbox("Stock 1", list(STOCKS.keys()), index=0)
    with col2:
        stock2 = st.selectbox("Stock 2", list(STOCKS.keys()), index=1)
    with col3:
        stock3 = st.selectbox("Stock 3", list(STOCKS.keys()), index=2)

    comp_period = st.selectbox("📅 Comparison Period",
                               ['1mo', '3mo', '6mo', '1y', '2y'], index=3)

    if st.button("🔍 Compare Stocks", type="primary",
                 use_container_width=True):
        tickers = [STOCKS[stock1], STOCKS[stock2], STOCKS[stock3]]
        names = [stock1, stock2, stock3]

        with st.spinner("Fetching data for all stocks..."):
            data = get_comparison_data(tickers, comp_period)

        if data:
            st.markdown("---")
            st.subheader("📋 Performance Comparison")
            metrics_df = get_performance_metrics(data)

            if not metrics_df.empty:
                best = metrics_df.loc[
                    metrics_df['Return_Value'].idxmax(), 'Ticker']
                st.success(f"🏆 Best Performer: **{best}** with return of "
                          f"{metrics_df['Return_Value'].max():+.2f}%")
                display_metrics = metrics_df.drop('Return_Value', axis=1)
                st.dataframe(display_metrics, use_container_width=True)

            st.markdown("---")
            st.subheader("📈 Normalized Price Comparison (Base = 100)")
            normalized = get_normalized_prices(data)
            fig_norm = go.Figure()
            colors = ['#00C853', '#FF6D00', '#1565C0']

            for i, (ticker, values) in enumerate(normalized.items()):
                dates = data[ticker]['Date'].values[:len(values)]
                fig_norm.add_trace(go.Scatter(
                    x=dates, y=values, name=ticker,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))

            fig_norm.add_hline(y=100, line_dash="dash",
                              line_color="white", opacity=0.5)
            fig_norm.update_layout(
                title="Normalized Price Performance",
                height=400, template='plotly_dark',
                yaxis_title="Normalized Price (Base=100)"
            )
            st.plotly_chart(fig_norm, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Individual Price Charts")
            for i, (ticker, df) in enumerate(data.items()):
                if not df.empty:
                    fig_ind = go.Figure()
                    fig_ind.add_trace(go.Scatter(
                        x=df['Date'], y=df['Close'],
                        name=ticker,
                        line=dict(color=colors[i % len(colors)], width=2),
                        fill='tozeroy'
                    ))
                    fig_ind.update_layout(
                        title=f"{names[i]} Price",
                        height=250, template='plotly_dark'
                    )
                    st.plotly_chart(fig_ind, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Volume Comparison")
            fig_vol = go.Figure()
            for i, (ticker, df) in enumerate(data.items()):
                if not df.empty:
                    fig_vol.add_trace(go.Bar(
                        x=df['Date'], y=df['Volume'],
                        name=ticker,
                        marker_color=colors[i % len(colors)],
                        opacity=0.7
                    ))
            fig_vol.update_layout(
                title="Trading Volume Comparison",
                height=350, template='plotly_dark',
                barmode='group'
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            st.markdown("---")
            st.subheader("🔥 Correlation Heatmap")
            corr_matrix = get_correlation_matrix(data)
            if not corr_matrix.empty:
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.index,
                    colorscale='RdYlGn',
                    zmin=-1, zmax=1,
                    text=corr_matrix.values.round(2),
                    texttemplate="%{text}",
                    textfont={"size": 16}
                ))
                fig_corr.update_layout(
                    title="Stock Correlation Matrix",
                    height=400, template='plotly_dark'
                )
                st.plotly_chart(fig_corr, use_container_width=True)

            st.markdown("---")
            st.subheader("📈 Daily Returns Comparison")
            fig_ret = go.Figure()
            for i, (ticker, df) in enumerate(data.items()):
                if not df.empty:
                    returns = df['Close'].pct_change() * 100
                    fig_ret.add_trace(go.Scatter(
                        x=df['Date'], y=returns, name=ticker,
                        line=dict(color=colors[i % len(colors)], width=1)
                    ))
            fig_ret.add_hline(y=0, line_dash="dash", line_color="white")
            fig_ret.update_layout(
                title="Daily Returns (%)",
                height=350, template='plotly_dark'
            )
            st.plotly_chart(fig_ret, use_container_width=True)
    else:
        st.info("👆 Select 3 stocks and click 'Compare Stocks'!")

# ==========================================
# PAGE 5 — FEAR & GREED INDEX
# ==========================================
elif page == "🕰️ Market History":
    st.markdown("## 🕰️ Market History")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📊 Major Indices", "📅 Custom Date Range Lookup"])

    with tab1:
        st.subheader("📊 Major Market Indices Over Time")

        INDICES = {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'Dow Jones': '^DJI',
            'NIFTY 50': '^NSEI',
            'SENSEX': '^BSESN',
            'FTSE 100': '^FTSE'
        }

        selected_indices = st.multiselect(
            "Select indices to compare",
            list(INDICES.keys()),
            default=['S&P 500', 'NIFTY 50'])

        index_period = st.selectbox(
            "Time Period", ['1mo', '6mo', '1y', '2y', '5y'], index=2)

        if selected_indices:
            with st.spinner("Loading index data..."):
                fig_idx = go.Figure()
                colors = ['#00C853', '#FF6D00', '#1565C0', '#D500F9', '#FFD600', '#00B8D4']
                summary_rows = []

                for i, idx_name in enumerate(selected_indices):
                    df_idx = get_index_data(INDICES[idx_name], index_period)
                    if not df_idx.empty:
                        normalized = (df_idx['Close'] / df_idx['Close'].iloc[0]) * 100
                        fig_idx.add_trace(go.Scatter(
                            x=df_idx['Date'], y=normalized,
                            name=idx_name,
                            line=dict(color=colors[i % len(colors)], width=2)
                        ))
                        total_return = ((df_idx['Close'].iloc[-1] - df_idx['Close'].iloc[0])
                                        / df_idx['Close'].iloc[0]) * 100
                        summary_rows.append({
                            'Index': idx_name,
                            'Start': f"{df_idx['Close'].iloc[0]:,.2f}",
                            'Current': f"{df_idx['Close'].iloc[-1]:,.2f}",
                            'Return': f"{total_return:+.2f}%"
                        })

                fig_idx.add_hline(y=100, line_dash="dash", line_color="white", opacity=0.4)
                fig_idx.update_layout(
                    title="Index Performance (Normalized, Base=100)",
                    height=450, template='plotly_dark',
                    yaxis_title="Normalized Value"
                )
                st.plotly_chart(fig_idx, use_container_width=True)

                if summary_rows:
                    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
        else:
            st.info("👆 Select at least one index above.")

    with tab2:
        st.subheader("📅 Custom Date Range Lookup")
        st.markdown(f"Looking up: **{selected_stock_name}**")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date",
                                       value=datetime(2024, 1, 1))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())

        if st.button("🔍 Fetch Historical Data", type="primary"):
            if start_date >= end_date:
                st.error("⚠️ Start date must be before end date!")
            else:
                with st.spinner("Fetching historical data..."):
                    hist_df = get_custom_range_data(
                        selected_ticker, str(start_date), str(end_date))

                if hist_df is not None and not hist_df.empty:
                    st.success(f"✅ Found {len(hist_df)} trading days between {start_date} and {end_date}")

                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Candlestick(
                        x=hist_df['Date'], open=hist_df['Open'],
                        high=hist_df['High'], low=hist_df['Low'],
                        close=hist_df['Close'], name='Price'
                    ))
                    fig_hist.update_layout(
                        title=f"{selected_stock_name} — {start_date} to {end_date}",
                        height=450, template='plotly_dark',
                        xaxis_rangeslider_visible=False
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

                    period_start = hist_df['Close'].iloc[0]
                    period_end = hist_df['Close'].iloc[-1]
                    period_return = ((period_end - period_start) / period_start) * 100
                    period_high = hist_df['High'].max()
                    period_low = hist_df['Low'].min()

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Start Price", f"${period_start:.2f}")
                    with c2:
                        st.metric("End Price", f"${period_end:.2f}")
                    with c3:
                        st.metric("Period Return", f"{period_return:+.2f}%")
                    with c4:
                        st.metric("Period High/Low", f"${period_high:.2f} / ${period_low:.2f}")

                    st.markdown("---")
                    st.subheader("📋 Data Table")
                    display_hist = hist_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
                    display_hist['Date'] = display_hist['Date'].dt.strftime('%Y-%m-%d')
                    st.dataframe(display_hist, use_container_width=True)

                    csv = display_hist.to_csv(index=False)
                    st.download_button(
                        "📥 Download as CSV", csv,
                        file_name=f"{selected_ticker}_history_{start_date}_to_{end_date}.csv",
                        mime="text/csv")
                else:
                    st.error("❌ No data found for that date range.")

elif page == "😱 Fear & Greed Index":
    st.markdown("## 😱 Fear & Greed Index")
    st.markdown("**Market sentiment indicator — Updated in real time**")
    st.markdown("---")

    with st.spinner("Calculating Fear & Greed Index..."):
        fg_data = calculate_fear_greed_index()

    score = fg_data['score']
    sentiment = fg_data['sentiment']
    color = fg_data['color']
    emoji = fg_data['emoji']

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{emoji} {sentiment}", 'font': {'size': 24}},
        delta={'reference': 50,
               'increasing': {'color': '#00C853'},
               'decreasing': {'color': '#FF1744'}},
        gauge={
            'axis': {'range': [0, 100],
                    'tickvals': [0, 25, 50, 75, 100],
                    'ticktext': ['0', '25', '50', '75', '100']},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'steps': [
                {'range': [0, 25], 'color': '#FF1744'},
                {'range': [25, 45], 'color': '#FF6D00'},
                {'range': [45, 55], 'color': '#FFD600'},
                {'range': [55, 75], 'color': '#64DD17'},
                {'range': [75, 100], 'color': '#00C853'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig_gauge.update_layout(
        height=400, template='plotly_dark',
        font={'color': 'white'}
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Score", f"{score}/100")
    with col2:
        st.metric("😱 Sentiment", f"{emoji} {sentiment}")
    with col3:
        signal = fg_data['signal']
        if signal == 'BUY':
            st.metric("🎯 Signal", "🟢 BUY")
        elif signal == 'SELL':
            st.metric("🎯 Signal", "🔴 SELL")
        else:
            st.metric("🎯 Signal", "🟡 HOLD")

    st.markdown(f"""
    <div style='background: #1e1e2e; border-radius: 10px;
                padding: 1rem; border-left: 4px solid {color};
                margin: 1rem 0;'>
        <p style='color: white; margin: 0; font-size: 1.1rem;'>
            {fg_data['description']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Sentiment Scale")
    scale_df = pd.DataFrame({
        'Zone': ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'],
        'Range': ['0-25', '25-45', '45-55', '55-75', '75-100'],
        'Signal': ['Strong Buy **', 'Buy *', 'Hold ~', 'Sell *', 'Strong Sell **']
    })
    st.dataframe(scale_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Index Components")
    components = fg_data['components']
    if components:
        comp_names = {
            'momentum': '📈 Market Momentum',
            'strength': '💪 Price Strength',
            'volatility': '📊 Market Volatility',
            'rsi': '⚡ RSI Indicator',
            'safe_haven': '🏦 Safe Haven Demand'
        }
        col1, col2 = st.columns(2)
        comp_list = list(components.items())
        for i, (key, value) in enumerate(comp_list):
            col = col1 if i % 2 == 0 else col2
            with col:
                label = comp_names.get(key, key)
                comp_sentiment = (
                    "Extreme Greed 🤑" if value >= 75 else
                    "Greed 😀" if value >= 55 else
                    "Neutral 😐" if value >= 45 else
                    "Fear 😨" if value >= 25 else
                    "Extreme Fear 😱"
                )
                st.metric(label, f"{value:.1f}/100", comp_sentiment)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=[comp_names.get(k, k) for k in components.keys()],
            y=list(components.values()),
            marker_color=[
                '#00C853' if v >= 55 else
                '#FFD600' if v >= 45 else
                '#FF1744'
                for v in components.values()
            ]
        ))
        fig_comp.add_hline(y=50, line_dash="dash",
                          line_color="white", opacity=0.5)
        fig_comp.update_layout(
            title="Fear & Greed Components",
            height=350, template='plotly_dark',
            yaxis_title="Score (0-100)",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Historical Fear & Greed (1 Year)")
    with st.spinner("Loading historical data..."):
        hist_data = get_historical_fear_greed()

    if hist_data is not None:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=hist_data['Date'], y=hist_data['Score'],
            mode='lines', name='Fear & Greed Score',
            line=dict(width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 200, 83, 0.1)'
        ))
        fig_hist.add_hline(y=75, line_dash="dash", line_color="#00C853",
                          annotation_text="Extreme Greed")
        fig_hist.add_hline(y=25, line_dash="dash", line_color="#FF1744",
                          annotation_text="Extreme Fear")
        fig_hist.add_hline(y=50, line_dash="dash",
                          line_color="white", opacity=0.3)
        fig_hist.update_layout(
            title="Historical Fear & Greed Index",
            height=400, template='plotly_dark',
            yaxis_title="Score", yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    st.subheader(f"💡 Impact on {selected_stock_name}")
    if score < 30:
        st.success(f"""
        🟢 **Buying Opportunity for {selected_stock_name}!**
        - Market is in Extreme Fear ({score}/100)
        - Warren Buffett: *"Be greedy when others are fearful"*
        """)
    elif score > 70:
        st.error(f"""
        🔴 **Caution for {selected_stock_name}!**
        - Market is in Extreme Greed ({score}/100)
        - Warren Buffett: *"Be fearful when others are greedy"*
        """)
    else:
        st.warning(f"""
        🟡 **Neutral Sentiment for {selected_stock_name}**
        - Market sentiment is {sentiment} ({score}/100)
        - No strong signal — follow your investment strategy
        """)
    st.caption("⚠️ For educational purposes only. Not financial advice.")

# ==========================================
# PAGE 6 — AI PREDICTIONS
# ==========================================
elif page == "🤖 AI Predictions":
    st.markdown("## 🤖 AI Price Predictions")
    st.markdown("**Powered by Real LSTM Neural Network**")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("📅 Predict how many days ahead?", 3, 30, 7)
    with col2:
        epochs = st.slider("🧠 Training Epochs", 5, 50, 20)

    st.info("💡 More epochs = better accuracy but slower training")

    if st.button("🚀 Train LSTM & Predict", type="primary",
                 use_container_width=True):

        with st.spinner("📥 Fetching 2 years of stock data..."):
            df = get_stock_data(selected_ticker, '2y')

        st.markdown("### 🧠 Training LSTM Neural Network")
        progress_bar = st.progress(0)
        status_text = st.empty()
        train_losses = []

        def update_progress(epoch, total, loss):
            progress = epoch / total
            progress_bar.progress(float(progress))
            status_text.text(
                f"Training: Epoch {epoch}/{total} | Loss: {loss:.6f}")
            train_losses.append(loss)

        model_data = train_lstm_model(
            df, epochs=epochs,
            progress_callback=update_progress)

        if model_data:
            progress_bar.progress(1.0)
            status_text.text("✅ Training Complete!")

            st.markdown("### 📊 Model Performance")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Accuracy", f"{model_data['accuracy']:.2f}%")
            with col2:
                st.metric("📉 MAE", f"${model_data['mae']:.2f}")
            with col3:
                st.metric("📊 RMSE", f"${model_data['rmse']:.2f}")
            with col4:
                st.metric("📈 MAPE", f"{model_data['mape']:.2f}%")

            st.markdown("### 📉 Training Loss")
            loss_df = pd.DataFrame({
                'Epoch': range(1, len(model_data['train_losses']) + 1),
                'Loss': model_data['train_losses']
            })
            fig_loss = px.line(loss_df, x='Epoch', y='Loss',
                              title='LSTM Training Loss Over Epochs',
                              template='plotly_dark',
                              color_discrete_sequence=['#00C853'])
            st.plotly_chart(fig_loss, use_container_width=True)

            st.markdown("### 🎯 Actual vs Predicted")
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                y=model_data['test_actual'],
                name='Actual Price',
                line=dict(color='#00C853', width=2)
            ))
            fig_comp.add_trace(go.Scatter(
                y=model_data['test_pred'],
                name='LSTM Predicted',
                line=dict(color='#FF6D00', width=2, dash='dash')
            ))
            fig_comp.update_layout(
                title='Actual vs LSTM Predicted Prices',
                height=400, template='plotly_dark'
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            st.markdown(f"### 🔮 {days}-Day Future Prediction")
            pred_df = predict_future_lstm(model_data, df, days=days)

            if pred_df is not None:
                fig_pred = go.Figure()
                recent_df = df.tail(60)
                fig_pred.add_trace(go.Scatter(
                    x=recent_df['Date'], y=recent_df['Close'],
                    name='Historical Price',
                    line=dict(color='#00C853', width=2)
                ))
                fig_pred.add_trace(go.Scatter(
                    x=pred_df['Date'], y=pred_df['Predicted_Price'],
                    name='LSTM Prediction',
                    line=dict(color='#FF6D00', width=2, dash='dash'),
                    mode='lines+markers'
                ))
                fig_pred.add_trace(go.Scatter(
                    x=pred_df['Date'], y=pred_df['Upper_Bound'],
                    fill=None, mode='lines',
                    line=dict(color='rgba(255,109,0,0.2)'),
                    name='Upper Bound'
                ))
                fig_pred.add_trace(go.Scatter(
                    x=pred_df['Date'], y=pred_df['Lower_Bound'],
                    fill='tonexty', mode='lines',
                    line=dict(color='rgba(255,109,0,0.2)'),
                    fillcolor='rgba(255,109,0,0.1)',
                    name='Lower Bound'
                ))
                fig_pred.update_layout(
                    title=f"🔮 {selected_stock_name} — {days}-Day LSTM Prediction",
                    height=500, template='plotly_dark',
                    yaxis_title="Price ($)"
                )
                st.plotly_chart(fig_pred, use_container_width=True)

                st.markdown("### 📋 Predicted Prices Table")
                display_pred = pred_df.copy()
                display_pred['Date'] = display_pred['Date'].dt.strftime('%Y-%m-%d')
                display_pred['Predicted_Price'] = display_pred['Predicted_Price'].round(2)
                display_pred['Upper_Bound'] = display_pred['Upper_Bound'].round(2)
                display_pred['Lower_Bound'] = display_pred['Lower_Bound'].round(2)
                st.dataframe(display_pred, use_container_width=True)

                current = df['Close'].iloc[-1]
                predicted = pred_df['Predicted_Price'].iloc[-1]
                change = ((predicted - current) / current) * 100

                st.markdown("---")
                st.markdown("### 💡 AI Insight")
                if change > 2:
                    st.success(f"📈 LSTM predicts **{selected_stock_name}** will go **UP by {change:.2f}%** in {days} days! Consider **BUYING** 🟢")
                elif change < -2:
                    st.error(f"📉 LSTM predicts **{selected_stock_name}** will go **DOWN by {abs(change):.2f}%** in {days} days! Consider **SELLING** 🔴")
                else:
                    st.warning(f"➡️ LSTM predicts **{selected_stock_name}** will stay **STABLE** ({change:.2f}%) in {days} days! **HOLD** 🟡")
        else:
            st.error("❌ LSTM training failed! Try reducing epochs.")
    else:
        st.info("👆 Click 'Train LSTM & Predict' to start AI prediction!")
        with st.spinner("Loading preview..."):
            df = get_stock_data(selected_ticker, '1y')
            pred_df = predict_future(df, days=7)

        if pred_df is not None:
            fig_prev = go.Figure()
            recent_df = df.tail(30)
            fig_prev.add_trace(go.Scatter(
                x=recent_df['Date'], y=recent_df['Close'],
                name='Recent Price',
                line=dict(color='#00C853', width=2)
            ))
            fig_prev.add_trace(go.Scatter(
                x=pred_df['Date'], y=pred_df['Predicted_Price'],
                name='Quick Prediction',
                line=dict(color='#FF6D00', width=2, dash='dash')
            ))
            fig_prev.update_layout(
                title='Quick Preview (Train LSTM for better accuracy)',
                height=400, template='plotly_dark'
            )
            st.plotly_chart(fig_prev, use_container_width=True)

# ==========================================
# PAGE 7 — NEWS SENTIMENT
# ==========================================
elif page == "📰 News Sentiment":
    st.markdown("## 📰 News Sentiment Analysis")
    st.markdown("---")

    company_name = selected_stock_name.split('(')[0].strip()

    with st.spinner(f"Fetching latest news for {company_name}..."):
        sentiment_data = get_overall_sentiment(company_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Sentiment", sentiment_data['overall'])
    with col2:
        st.metric("Sentiment Score", f"{sentiment_data['score']:.3f}")
    with col3:
        st.metric("🟢 Positive News", sentiment_data['positive_count'])
    with col4:
        st.metric("🔴 Negative News", sentiment_data['negative_count'])

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Sentiment Distribution")
        fig_pie = px.pie(
            values=[sentiment_data['positive_count'],
                   sentiment_data['negative_count'],
                   sentiment_data['neutral_count']],
            names=['Positive', 'Negative', 'Neutral'],
            color_discrete_map={
                'Positive': '#00C853',
                'Negative': '#FF1744',
                'Neutral': '#FFD600'
            },
            template='plotly_dark'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("📈 Sentiment Scores by Source")
        news_df = pd.DataFrame(sentiment_data['news'])
        if not news_df.empty:
            fig_bar = px.bar(
                news_df.head(10), x='score', y='source',
                orientation='h', color='score',
                color_continuous_scale='RdYlGn',
                template='plotly_dark'
            )
            fig_bar.update_layout(height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("📰 Latest News Articles")
    for news in sentiment_data['news']:
        with st.expander(f"{news['emoji']} {news['title'][:80]}..."):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Sentiment:** {news['emoji']} {news['sentiment']}")
            with col2:
                st.markdown(f"**Score:** {news['score']:.3f}")
            with col3:
                st.markdown(f"**Source:** {news['source']}")
            st.markdown(f"[Read Full Article]({news['url']})")
            st.markdown(f"*Published: {news['published'][:10]}*")

# ==========================================
# PAGE 8 — MY PORTFOLIO
# ==========================================
elif page == "⭐ Watchlist":
    st.markdown("## ⭐ Watchlist")
    st.markdown("---")

    st.info("Track stocks you're interested in without buying them yet!")

    col1, col2 = st.columns(2)
    with col1:
        watch_stock = st.selectbox("Select Stock", list(STOCKS.keys()), key="watch_select")
    with col2:
        st.write("")
        st.write("")
        if st.button("⭐ Add to Watchlist", type="primary"):
            info = get_stock_info(STOCKS[watch_stock])
            current_price = info.get('current_price') or 0
            result = save_watchlist(user_id, STOCKS[watch_stock],
                                    watch_stock, current_price)
            if result['success']:
                st.success(f"✅ Added {watch_stock} to watchlist!")
                st.rerun()
            else:
                st.error(f"❌ Failed to add! Debug: {result.get('error')}")

    st.markdown("---")
    watchlist = get_watchlist(user_id)

    if watchlist:
        st.subheader("👀 Your Watched Stocks")
        for item in watchlist:
            try:
                info = get_stock_info(item['ticker'])
                current_price = info.get('current_price', 0)
                added_price = float(item.get('added_price', 0)) or current_price
                change = current_price - added_price
                change_pct = (change / added_price * 100) if added_price else 0

                col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
                with col1:
                    st.markdown(f"**{item['stock_name']}**")
                with col2:
                    st.markdown(f"Added at: ${added_price:.2f}")
                with col3:
                    st.markdown(f"Now: ${current_price:.2f}")
                with col4:
                    if change >= 0:
                        st.success(f"+{change_pct:.2f}%")
                    else:
                        st.error(f"{change_pct:.2f}%")
                with col5:
                    if st.button("🗑️", key=f"del_watch_{item['id']}"):
                        result = delete_watchlist_item(item['id'])
                        if not result['success']:
                            st.error(f"Delete failed: {result.get('error')}")
                        else:
                            st.rerun()
            except Exception as e:
                st.error(f"Watchlist item error: {e}")
    else:
        st.info("📭 Your watchlist is empty. Add stocks above!")

elif page == "💼 My Portfolio":
    st.markdown("## 💼 My Portfolio")
    st.markdown("---")

    st.info("Your portfolio is saved to the cloud — accessible from anywhere!")

    col1, col2, col3 = st.columns(3)
    with col1:
        port_stock = st.selectbox("Select Stock", list(STOCKS.keys()))
    with col2:
        quantity = st.number_input("Quantity", min_value=1, value=10)
    with col3:
        buy_price = st.number_input("Buy Price ($)", min_value=0.0, value=100.0)

    if st.button("➕ Add to Portfolio", type="primary"):
        result = save_portfolio(user_id, STOCKS[port_stock],
                               port_stock, quantity, buy_price)
        if result['success']:
            st.success(f"✅ Added {port_stock} to portfolio!")
            st.rerun()
        else:
            st.error("❌ Failed to save!")

    st.markdown("---")
    portfolio = get_portfolio(user_id)

    if portfolio:
        st.subheader("📊 Your Portfolio")
        portfolio_data = []
        total_invested = 0
        total_current = 0

        for item in portfolio:
            try:
                info = get_stock_info(item['ticker'])
                current_price = info.get('current_price', item['buy_price'])
                invested = item['quantity'] * item['buy_price']
                current_value = item['quantity'] * current_price
                pnl = current_value - invested
                pnl_pct = (pnl / invested) * 100
                portfolio_data.append({
                    'ID': item['id'],
                    'Stock': item['stock_name'],
                    'Quantity': item['quantity'],
                    'Buy Price': f"${item['buy_price']:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Invested': f"${invested:.2f}",
                    'Current Value': f"${current_value:.2f}",
                    'P&L': f"${pnl:+.2f}",
                    'P&L %': f"{pnl_pct:+.2f}%",
                    'Status': '🟢 Profit' if pnl > 0 else '🔴 Loss'
                })
                total_invested += invested
                total_current += current_value
            except:
                pass

        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Invested", f"${total_invested:.2f}")
        with col2:
            st.metric("📈 Current Value", f"${total_current:.2f}")
        with col3:
            st.metric("💹 Total P&L", f"${total_pnl:+.2f}",
                     f"{total_pnl_pct:+.2f}%")

        port_df = pd.DataFrame(portfolio_data)
        st.dataframe(port_df.drop('ID', axis=1), use_container_width=True)

        st.subheader("🥧 Portfolio Distribution")
        fig_port = px.pie(
            values=[item['quantity'] * item['buy_price'] for item in portfolio],
            names=[item['stock_name'] for item in portfolio],
            template='plotly_dark'
        )
        st.plotly_chart(fig_port, use_container_width=True)

        st.subheader("🗑️ Remove Stock")
        stock_to_delete = st.selectbox(
            "Select stock to remove",
            [item['stock_name'] for item in portfolio]
        )
        if st.button("🗑️ Remove", type="secondary"):
            item_to_delete = next(
                (item for item in portfolio
                 if item['stock_name'] == stock_to_delete), None)
            if item_to_delete:
                result = delete_portfolio_item(item_to_delete['id'])
                if result['success']:
                    st.success("✅ Removed successfully!")
                    st.rerun()
    else:
        st.info("📭 Your portfolio is empty. Add some stocks above!")

# ==========================================
# PAGE 9 — PRICE ALERTS
# ==========================================
elif page == "📜 Trade History":
    st.markdown("## 📜 Trade History")
    st.markdown("---")

    st.info("Log every buy/sell trade to build a complete record of your activity!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_stock = st.selectbox("Select Stock", list(STOCKS.keys()), key="trade_select")
    with col2:
        trade_type = st.selectbox("Trade Type", ["Buy", "Sell"])
    with col3:
        trade_qty = st.number_input("Quantity", min_value=1, value=10, key="trade_qty")
    with col4:
        trade_price = st.number_input("Price ($)", min_value=0.0, value=100.0, key="trade_price")

    trade_notes = st.text_input("Notes (optional)", placeholder="e.g. Earnings play, long-term hold")

    if st.button("📝 Log Trade", type="primary", use_container_width=True):
        result = save_trade(user_id, STOCKS[trade_stock], trade_stock,
                            trade_type, trade_qty, trade_price, trade_notes)
        if result['success']:
            st.success(f"✅ Logged {trade_type} of {trade_qty} {trade_stock} @ ${trade_price:.2f}")
            st.rerun()
        else:
            st.error("❌ Failed to log trade!")

    st.markdown("---")
    trades = get_trade_history(user_id)

    if trades:
        st.subheader("📋 Your Trades")

        total_bought = sum(t['total_value'] for t in trades if t['trade_type'] == 'Buy')
        total_sold = sum(t['total_value'] for t in trades if t['trade_type'] == 'Sell')

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💵 Total Bought", f"${total_bought:,.2f}")
        with col2:
            st.metric("💰 Total Sold", f"${total_sold:,.2f}")
        with col3:
            st.metric("📊 Total Trades", len(trades))

        st.markdown("---")

        trade_data = []
        for t in trades:
            trade_data.append({
                'ID': t['id'],
                'Date': t['created_at'][:10],
                'Stock': t['stock_name'],
                'Type': t['trade_type'],
                'Quantity': t['quantity'],
                'Price': f"${t['price']:.2f}",
                'Total': f"${t['total_value']:.2f}",
                'Notes': t.get('notes', '') or '-'
            })

        trade_df = pd.DataFrame(trade_data)
        st.dataframe(trade_df.drop('ID', axis=1), use_container_width=True)

        st.subheader("🗑️ Remove a Trade")
        trade_options = {f"{t['stock_name']} - {t['trade_type']} - {t['created_at'][:10]}": t['id']
                         for t in trades}
        selected_trade = st.selectbox("Select trade to remove", list(trade_options.keys()))
        if st.button("🗑️ Delete Trade", type="secondary"):
            delete_trade_item(trade_options[selected_trade])
            st.success("✅ Trade removed!")
            st.rerun()
    else:
        st.info("📭 No trades logged yet. Add one above!")

elif page == "🚨 Price Alerts":
    st.markdown("## 🚨 Price Alerts")
    st.markdown("---")

    st.info("Set price alerts and get notified when stocks hit your target!")

    col1, col2, col3 = st.columns(3)
    with col1:
        alert_stock = st.selectbox("Select Stock", list(STOCKS.keys()))
    with col2:
        alert_price = st.number_input("Alert Price ($)", min_value=0.0, value=100.0)
    with col3:
        alert_type = st.selectbox("Alert Type", ["Above", "Below"])

    if st.button("🔔 Set Alert", type="primary"):
        result = save_alert(user_id, STOCKS[alert_stock],
                           alert_price, alert_type)
        if result['success']:
            st.success(f"✅ Alert set for {alert_stock} at ${alert_price}!")
            st.rerun()
        else:
            st.error("❌ Failed to set alert!")

    st.markdown("---")
    alerts = get_alerts(user_id)

    if alerts:
        st.subheader("🔔 Your Active Alerts")

        if 'notified_alerts' not in st.session_state:
            st.session_state.notified_alerts = set()

        for alert in alerts:
            try:
                info = get_stock_info(alert['ticker'])
                current_price = info.get('current_price', 0)
                triggered = (
                    (alert['alert_type'] == 'Above' and
                     current_price >= alert['alert_price']) or
                    (alert['alert_type'] == 'Below' and
                     current_price <= alert['alert_price'])
                )
                col1, col2, col3, col4, col5 = st.columns([1.5, 2, 1.5, 1.5, 1.5])
                with col1:
                    st.markdown(f"**{alert['ticker']}**")
                with col2:
                    st.markdown(f"Alert: ${alert['alert_price']} ({alert['alert_type']})")
                with col3:
                    st.markdown(f"Current: ${current_price:.2f}")
                with col4:
                    if triggered:
                        st.error("🚨 TRIGGERED!")
                    else:
                        st.success("✅ Active")
                with col5:
                    if triggered and alert['id'] not in st.session_state.notified_alerts:
                        email_result = send_alert_email(
                            user_email, alert['ticker'], alert['ticker'],
                            alert['alert_price'], alert['alert_type'], current_price)
                        if email_result['success']:
                            st.session_state.notified_alerts.add(alert['id'])
                            st.success("📧 Email sent!")
                        else:
                            st.error(f"Email failed: {email_result.get('error')}")
                    elif alert['id'] in st.session_state.notified_alerts:
                        st.caption("📧 Already notified")
            except Exception as e:
                st.error(f"Alert error: {e}")
    else:
        st.info("📭 No alerts set. Add some alerts above!")

# ==========================================
# PAGE 10 — MY PROFILE
# ==========================================
elif page == "👤 My Profile":
    st.markdown("## 👤 My Profile")
    st.markdown("---")

    profile = get_profile(user_id) or {}
    avatar_url = profile.get('avatar_url')

    col1, col2 = st.columns([1, 3])
    with col1:
        if avatar_url:
            st.image(avatar_url, width=120)
        else:
            st.markdown("### 👤")
    with col2:
        st.subheader(user_name)
        st.markdown(f"**Email:** {user_email}")
        st.markdown(f"**Phone:** {profile.get('phone') or 'Not set'}")
        st.markdown(f"**User ID:** {str(user_id)[:8]}...")
        st.markdown(f"**Member since:** {datetime.now().strftime('%B %Y')}")

    st.markdown("---")
    st.subheader("📊 Your Stats")
    portfolio = get_portfolio(user_id)
    alerts = get_alerts(user_id)
    watchlist_items = get_watchlist(user_id)
    trades = get_trade_history(user_id)

    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        st.metric("💼 Portfolio Stocks", len(portfolio))
    with scol2:
        st.metric("🔔 Active Alerts", len(alerts))
    with scol3:
        st.metric("⭐ Watchlist", len(watchlist_items))
    with scol4:
        st.metric("📜 Trades Logged", len(trades))

    st.markdown("---")
    st.subheader("✏️ Edit Profile")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["👤 Profile Info", "🖼️ Profile Picture", "🔒 Password", "🎨 Preferences"])

    with tab1:
        with st.form("edit_profile_form"):
            new_name = st.text_input("Full Name", value=user_name)
            new_phone = st.text_input("Phone Number",
                                      value=profile.get('phone') or '',
                                      placeholder="+91 98765 43210")
            new_bio = st.text_area("Bio",
                                   value=profile.get('bio') or '',
                                   placeholder="Tell us a bit about yourself")
            submit_profile = st.form_submit_button(
                "💾 Save Profile", type="primary", use_container_width=True)

        if submit_profile:
            name_result = update_display_name(new_name)
            profile_result = upsert_profile(
                user_id, full_name=new_name, phone=new_phone, bio=new_bio)
            if name_result['success'] and profile_result['success']:
                # Refresh the session user so the new name shows immediately
                st.session_state.user.user_metadata['full_name'] = new_name
                st.success("✅ Profile updated!")
                st.rerun()
            else:
                err = name_result.get('error') or profile_result.get('error')
                st.error(f"❌ Failed to update: {err}")

    with tab2:
        st.markdown("Upload a profile picture (JPG or PNG, under 5MB)")
        uploaded_file = st.file_uploader(
            "Choose an image", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            st.image(uploaded_file, width=150)
            if st.button("📤 Upload Picture", type="primary"):
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1].lower()
                result = upload_avatar(user_id, file_bytes, file_ext)
                if result['success']:
                    profile_result = upsert_profile(user_id, avatar_url=result['url'])
                    if profile_result['success']:
                        st.success(f"✅ Profile picture updated! URL: {result['url']}")
                        st.rerun()
                    else:
                        st.error(f"❌ Saved to storage but failed to link to profile: {profile_result.get('error')}")
                else:
                    st.error(f"❌ Upload failed: {result.get('error')}")

    with tab3:
        with st.form("change_password_form"):
            new_password = st.text_input(
                "New Password", type="password", placeholder="Min 6 characters")
            confirm_password = st.text_input(
                "Confirm New Password", type="password")
            submit_password = st.form_submit_button(
                "🔒 Update Password", type="primary", use_container_width=True)

        if submit_password:
            if not new_password or len(new_password) < 6:
                st.error("⚠️ Password must be at least 6 characters!")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords don't match!")
            else:
                result = change_password(new_password)
                if result['success']:
                    st.success("✅ Password changed successfully!")
                else:
                    st.error(f"❌ Failed: {result.get('error')}")

    with tab4:
        st.markdown("**🏠 Default Dashboard Stock**")
        default_stock_pick = st.selectbox(
            "Stock to show when you open the app",
            list(STOCKS.keys()),
            index=list(STOCKS.keys()).index(profile.get('default_stock_name'))
            if profile.get('default_stock_name') in STOCKS else 0)

        st.markdown("**💱 Preferred Currency Display**")
        currency_pick = st.radio(
            "Currency", ["USD", "INR"],
            index=0 if profile.get('currency', 'USD') == 'USD' else 1,
            horizontal=True)
        st.caption("Note: this saves your preference; live conversion display across all pages is a future enhancement.")

        st.markdown("**🎨 Theme**")
        theme_choice = st.radio(
            "Choose display theme", ["Dark", "Light"],
            index=0 if st.session_state.app_theme == 'Dark' else 1,
            horizontal=True, key="theme_radio")
        if theme_choice != st.session_state.app_theme:
            st.session_state.app_theme = theme_choice
            st.rerun()

        st.markdown("**🔔 Notifications**")
        notify_alerts = st.checkbox("Notify me when price alerts trigger", value=True)
        notify_news = st.checkbox("Notify me about major news sentiment shifts", value=False)
        st.caption("Note: actual email/push delivery is a future enhancement — these are saved as preferences for now.")

        if st.button("💾 Save Preferences", type="primary"):
            result = upsert_profile(
                user_id,
                default_stock=STOCKS[default_stock_pick],
                default_stock_name=default_stock_pick,
                currency=currency_pick)
            if result['success']:
                st.session_state.user_currency = currency_pick
                st.success("✅ Preferences saved!")
                st.rerun()
            else:
                st.error(f"❌ Failed: {result.get('error')}")

        st.markdown("---")
        st.subheader("📤 Export Your Data")
        st.markdown("Download everything you've stored in this app as CSV files.")

        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            port_export = get_portfolio(user_id)
            if port_export:
                port_csv = pd.DataFrame(port_export).to_csv(index=False)
                st.download_button("📥 Portfolio CSV", port_csv,
                                   file_name="my_portfolio.csv", mime="text/csv")
            else:
                st.caption("No portfolio data yet")
        with exp_col2:
            trade_export = get_trade_history(user_id)
            if trade_export:
                trade_csv = pd.DataFrame(trade_export).to_csv(index=False)
                st.download_button("📥 Trade History CSV", trade_csv,
                                   file_name="my_trade_history.csv", mime="text/csv")
            else:
                st.caption("No trades logged yet")
        with exp_col3:
            watch_export = get_watchlist(user_id)
            if watch_export:
                watch_csv = pd.DataFrame(watch_export).to_csv(index=False)
                st.download_button("📥 Watchlist CSV", watch_csv,
                                   file_name="my_watchlist.csv", mime="text/csv")
            else:
                st.caption("No watchlist items yet")

        st.markdown("---")
        st.subheader("⚠️ Danger Zone")
        with st.expander("🗑️ Delete My Account Data"):
            st.warning("This permanently deletes your portfolio, trades, watchlist, alerts, and profile. This cannot be undone.")
            confirm_delete = st.text_input(
                "Type DELETE to confirm", key="confirm_delete_input")
            if st.button("🗑️ Permanently Delete My Data", type="secondary"):
                if confirm_delete == "DELETE":
                    result = delete_account(user_id)
                    if result['success']:
                        st.success("✅ Your data has been deleted. Logging you out...")
                        sign_out()
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
                else:
                    st.error("⚠️ Please type DELETE exactly to confirm.")

    st.markdown("---")
    if st.button("🚪 Logout", type="primary", use_container_width=True):
        sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("**🤖 AI Stock Intelligence Platform** | Built with ❤️ using Python, Streamlit, Supabase & ML | Chandana M")