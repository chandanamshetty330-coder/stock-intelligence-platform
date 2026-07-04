from fpdf import FPDF
import pandas as pd
from datetime import datetime
import re

def clean(text):
    """Remove emojis and special chars for PDF, and break up long unspaced tokens"""
    if not text:
        return ''
    text = str(text)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F9FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"
        u"\U00002500-\U00002BEF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text).strip()
    text = text.encode('latin-1', 'ignore').decode('latin-1')
    def break_long(match):
        word = match.group(0)
        return ' '.join(word[i:i+15] for i in range(0, len(word), 15))
    text = re.sub(r'\S{20,}', break_long, text)
    return text


class StockReportPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 30, 46)
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(0, 200, 83)
        self.cell(0, 15, 'AI Stock Intelligence Platform', align='C', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, 'Professional Stock Analysis Report', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10,
                 f'Page {self.page_no()} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Built by Chandana',
                 align='C')

    def section_title(self, title):
        self.ln(5)
        self.set_fill_color(0, 200, 83)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 8, f'  {clean(title)}', fill=True, ln=True)
        self.ln(3)

    def add_metric_row(self, label, value, color=None):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(80, 80, 80)
        self.safe_cell(80, 7, clean(label))
        self.set_font('Helvetica', '', 10)
        if color == 'green':
            self.set_text_color(0, 150, 60)
        elif color == 'red':
            self.set_text_color(200, 0, 0)
        else:
            self.set_text_color(0, 0, 0)
        self.cell(0, 7, clean(str(value)), ln=True)
        self.set_text_color(0, 0, 0)

    def add_divider(self):
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def safe_cell(self, w, h, txt, border=0, ln=0, align='', fill=False):
        txt = clean(str(txt))
        if w > 0:
            while txt and self.get_string_width(txt) > (w - 2):
                txt = txt[:-1]
            if not txt:
                txt = ''
        self.cell(w, h, txt, border=border, ln=ln, align=align, fill=fill)

    def safe_multicell(self, h, txt, align='J'):
        txt = clean(str(txt))
        if not txt:
            return
        usable_w = self.w - self.l_margin - self.r_margin
        if usable_w <= 1:
            usable_w = 180
        self.multi_cell(usable_w, h, txt, align=align)


def generate_stock_report(stock_name, ticker, stock_info,
                          df, sentiment_data, pred_df=None,
                          portfolio=None, fear_greed=None):

    pdf = StockReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(30, 30, 46)
    pdf.ln(5)
    pdf.cell(0, 15, clean(stock_name), align='C', ln=True)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Ticker: {ticker}', align='C', ln=True)
    pdf.cell(0, 8, f'Report Date: {datetime.now().strftime("%B %d, %Y")}', align='C', ln=True)
    pdf.ln(5)
    pdf.add_divider()

    pdf.section_title('1. Company Overview')
    pdf.add_metric_row('Company Name:', stock_info.get('name', 'N/A'))
    pdf.add_metric_row('Sector:', stock_info.get('sector', 'N/A'))
    pdf.add_metric_row('Ticker Symbol:', ticker)
    pdf.add_metric_row('P/E Ratio:', str(round(stock_info.get('pe_ratio', 0), 2)))

    market_cap = stock_info.get('market_cap', 0)
    if market_cap > 1e9:
        market_cap_str = f"${market_cap/1e9:.1f}B"
    else:
        market_cap_str = f"${market_cap/1e6:.1f}M"
    pdf.add_metric_row('Market Cap:', market_cap_str)

    description = stock_info.get('description', 'N/A')
    if description and description != 'N/A':
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, 'Business Description:', ln=True)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        desc = clean(description[:500] + '...' if len(description) > 500 else description)
        pdf.safe_multicell(5, desc)

    pdf.section_title('2. Price Analysis')
    current_price = stock_info.get('current_price', 0)
    high_52w = stock_info.get('high_52week', 0)
    low_52w = stock_info.get('low_52week', 0)

    pdf.add_metric_row('Current Price:', f"${current_price:.2f}")
    pdf.add_metric_row('52-Week High:', f"${high_52w:.2f}")
    pdf.add_metric_row('52-Week Low:', f"${low_52w:.2f}")

    if not df.empty:
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        total_return = ((end_price - start_price) / start_price) * 100
        avg_price = df['Close'].mean()
        volatility = df['Close'].pct_change().std() * (252**0.5) * 100

        color = 'green' if total_return > 0 else 'red'
        pdf.add_metric_row('1-Year Return:', f"{total_return:+.2f}%", color)
        pdf.add_metric_row('Average Price (1Y):', f"${avg_price:.2f}")
        pdf.add_metric_row('Annual Volatility:', f"{volatility:.2f}%")
        pdf.add_metric_row('Latest Volume:', f"{int(df['Volume'].iloc[-1]):,}")

    pdf.section_title('3. Technical Indicators')

    if not df.empty and 'RSI' in df.columns:
        rsi = df['RSI'].iloc[-1]
        ma20 = df['MA20'].iloc[-1] if 'MA20' in df.columns else 0
        ma50 = df['MA50'].iloc[-1] if 'MA50' in df.columns else 0

        pdf.add_metric_row('RSI (14-day):', f"{rsi:.1f}" if not pd.isna(rsi) else 'N/A')

        if not pd.isna(rsi):
            if rsi > 70:
                rsi_signal = 'OVERBOUGHT - Consider Selling'
                rsi_color = 'red'
            elif rsi < 30:
                rsi_signal = 'OVERSOLD - Consider Buying'
                rsi_color = 'green'
            else:
                rsi_signal = 'NEUTRAL'
                rsi_color = None
            pdf.add_metric_row('RSI Signal:', rsi_signal, rsi_color)

        pdf.add_metric_row('20-Day MA:', f"${ma20:.2f}" if ma20 else 'N/A')
        pdf.add_metric_row('50-Day MA:', f"${ma50:.2f}" if ma50 else 'N/A')

        if ma20 and current_price:
            if current_price > ma20:
                pdf.add_metric_row('Price vs MA20:', 'ABOVE - Bullish Signal', 'green')
            else:
                pdf.add_metric_row('Price vs MA20:', 'BELOW - Bearish Signal', 'red')

    pdf.section_title('4. News Sentiment Analysis')
    overall = clean(sentiment_data.get('overall', 'N/A'))
    score = sentiment_data.get('score', 0)
    positive = sentiment_data.get('positive_count', 0)
    negative = sentiment_data.get('negative_count', 0)
    neutral = sentiment_data.get('neutral_count', 0)

    pdf.add_metric_row('Overall Sentiment:', overall)
    pdf.add_metric_row('Sentiment Score:', f"{score:.3f}")
    pdf.add_metric_row('Positive Articles:', str(positive))
    pdf.add_metric_row('Negative Articles:', str(negative))
    pdf.add_metric_row('Neutral Articles:', str(neutral))

    news_list = sentiment_data.get('news', [])
    if news_list:
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 7, 'Recent News Headlines:', ln=True)

        for i, news in enumerate(news_list[:5]):
            title = clean(news.get('title', ''))[:80]
            source = clean(news.get('source', ''))
            sent = clean(news.get('sentiment', ''))

            if sent == 'Positive':
                pdf.set_text_color(0, 150, 60)
            elif sent == 'Negative':
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(100, 100, 0)

            pdf.set_font('Helvetica', '', 9)
            line = clean(f"{i+1}. [{sent}] {title} - {source}")
            pdf.safe_multicell(5, line)
            pdf.set_text_color(0, 0, 0)

    if pred_df is not None and not pred_df.empty:
        pdf.section_title('5. AI Price Predictions (LSTM Model)')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        pdf.safe_multicell(5, 'LSTM Neural Network predictions based on historical data. For informational purposes only.')
        pdf.ln(3)

        pdf.set_fill_color(0, 200, 83)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 8, 'Date', fill=True, border=1)
        pdf.cell(50, 8, 'Predicted Price', fill=True, border=1)
        pdf.cell(40, 8, 'Upper Bound', fill=True, border=1)
        pdf.cell(40, 8, 'Lower Bound', fill=True, border=1, ln=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        fill = False
        for _, row in pred_df.iterrows():
            pdf.set_fill_color(240, 240, 240)
            date_str = str(row['Date'])[:10]
            pred_price = f"${float(row['Predicted_Price']):.2f}"
            upper = f"${float(row['Upper_Bound']):.2f}"
            lower = f"${float(row['Lower_Bound']):.2f}"
            pdf.safe_cell(60, 7, date_str, border=1, fill=fill)
            pdf.safe_cell(50, 7, pred_price, border=1, fill=fill)
            pdf.safe_cell(40, 7, upper, border=1, fill=fill)
            pdf.safe_cell(40, 7, lower, border=1, ln=True, fill=fill)
            fill = not fill

    if fear_greed:
        pdf.section_title('6. Market Fear & Greed Index')
        fg_score = fear_greed.get('score', 50)
        fg_sentiment = clean(fear_greed.get('sentiment', 'Neutral'))
        fg_signal = clean(fear_greed.get('signal', 'HOLD'))
        fg_desc = clean(fear_greed.get('description', ''))

        pdf.add_metric_row('Fear & Greed Score:', f"{fg_score}/100")
        pdf.add_metric_row('Market Sentiment:', fg_sentiment)
        signal_color = ('green' if fg_signal == 'BUY' else 'red' if fg_signal == 'SELL' else None)
        pdf.add_metric_row('Trading Signal:', fg_signal, signal_color)
        pdf.ln(3)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(80, 80, 80)
        pdf.safe_multicell(5, fg_desc)

    if portfolio and len(portfolio) > 0:
        pdf.section_title('7. Portfolio Summary')
        pdf.set_fill_color(0, 200, 83)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(50, 8, 'Stock', fill=True, border=1)
        pdf.cell(20, 8, 'Qty', fill=True, border=1)
        pdf.cell(30, 8, 'Buy Price', fill=True, border=1)
        pdf.cell(30, 8, 'Curr Price', fill=True, border=1)
        pdf.cell(30, 8, 'P&L', fill=True, border=1)
        pdf.cell(30, 8, 'Status', fill=True, border=1, ln=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 8)
        fill = False
        for item in portfolio:
            pdf.set_fill_color(240, 240, 240)
            buy_price = float(item.get('buy_price', 0))
            qty = int(item.get('quantity', 0))
            curr_price = buy_price * 1.1
            pnl = (curr_price - buy_price) * qty
            status = 'Profit' if pnl > 0 else 'Loss'
            pdf.safe_cell(50, 7, str(item.get('stock_name', ''))[:20], border=1, fill=fill)
            pdf.safe_cell(20, 7, str(qty), border=1, fill=fill)
            pdf.safe_cell(30, 7, f"${buy_price:.2f}", border=1, fill=fill)
            pdf.safe_cell(30, 7, f"${curr_price:.2f}", border=1, fill=fill)
            pdf.safe_cell(30, 7, f"${pnl:+.2f}", border=1, fill=fill)
            pdf.safe_cell(30, 7, status, border=1, ln=True, fill=fill)
            fill = not fill

    pdf.section_title('8. Disclaimer')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.safe_multicell(5,
        'This report is generated by AI Stock Intelligence Platform for educational '
        'and informational purposes only. The information does not constitute financial '
        'advice or investment recommendations. Past performance is not indicative of '
        'future results. Always consult a qualified financial advisor before making '
        'investment decisions.')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0, 200, 83)
    pdf.cell(0, 7, 'Report generated by AI Stock Intelligence Platform | Built by Chandana', align='C', ln=True)

    return pdf


def save_report(pdf, filename='stock_report.pdf'):
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    return bytes(pdf_output)