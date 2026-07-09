# 📈 AI Stock Intelligence Platform

A full-featured, cloud-connected stock market intelligence platform built with Streamlit, Supabase, and a custom-trained LSTM neural network — combining real-time market data, AI-driven predictions, sentiment analysis, and portfolio management into one product.

🔗 **Live Demo:** [stock-intelligence-platform-10ng.onrender.com](https://stock-intelligence-platform-10ng.onrender.com)

> ⚠️ Hosted on Render's free tier — the app may take 30–50 seconds to wake up on first load if it's been inactive.

## 🚀 Features

- **🔐 Authentication** — Secure signup/login via Supabase Auth
- **🔴 Live Predictions** — Real-time price tracking with AI trading signals
- **📊 Stock Analysis** — RSI, Bollinger Bands, MACD, moving averages
- **📈 Stock Comparison** — Compare up to 3 stocks side-by-side with correlation analysis
- **🕰️ Market History** — Major index tracking + custom date-range historical lookup
- **😱 Fear & Greed Index** — Real-time market sentiment scoring
- **🤖 AI Predictions** — Custom-trained LSTM neural network for price forecasting
- **📰 News Sentiment** — NLP-based sentiment analysis on live financial news
- **🔍 Dynamic Stock Search** — Search and track any publicly traded company
- **⭐ Watchlist** — Track stocks without buying
- **💼 Portfolio Management** — Track holdings, P&L, and performance
- **📜 Trade History** — Full buy/sell activity log
- **🚨 Price Alerts** — Real-time alerts with **live email notifications**
- **👤 Profile & Settings** — Editable profile, photo upload, currency (USD/INR), theme toggle, data export, account deletion
- **📄 PDF Reports** — Auto-generated, professional stock analysis reports

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Database & Auth | Supabase (PostgreSQL) |
| Storage | Supabase Storage |
| ML Model | PyTorch (LSTM) |
| NLP | VADER Sentiment |
| Market Data | Yahoo Finance API |
| Email | Resend |
| Visualization | Plotly |
| PDF Generation | fpdf2 |

## 📦 Setup

1. Clone the repo and install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
RESEND_API_KEY=your_resend_api_key

3. Run the app:
```bash
cd app
streamlit run main.py
```

## 🗄️ Database Schema

Tables required in Supabase: `profiles`, `portfolio`, `alerts`, `watchlist`, `trade_history` — all secured with Row Level Security policies.

## 🔮 Planned Enhancements

- Full currency conversion across all pages (currently on Dashboard)
- Complete light-mode styling across all pages
- Scheduled background alert monitoring (currently checked on page load)
- Push notification delivery alongside email

## 👩‍💻 Built By

Chandana M