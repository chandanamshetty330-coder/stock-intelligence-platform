import os
import resend
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv('RESEND_API_KEY')

def send_alert_email(to_email, stock_name, ticker, alert_price, alert_type, current_price):
    """Send an email notification when a price alert triggers"""
    try:
        direction = "risen above" if alert_type == "Above" else "fallen below"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;
                    background: #0e1117; color: #fafafa; padding: 2rem; border-radius: 10px;">
            <h2 style="color: #00C853;">🚨 Price Alert Triggered!</h2>
            <p><strong>{stock_name} ({ticker})</strong> has {direction} your target price.</p>
            <table style="width: 100%; margin: 1rem 0;">
                <tr><td style="padding: 4px 0;">Your Alert:</td>
                    <td style="text-align: right;">${alert_price:.2f} ({alert_type})</td></tr>
                <tr><td style="padding: 4px 0;">Current Price:</td>
                    <td style="text-align: right; color: #00C853; font-weight: bold;">${current_price:.2f}</td></tr>
            </table>
            <p style="color: #888; font-size: 0.85rem;">
                Sent by AI Stock Intelligence Platform
            </p>
        </div>
        """
        response = resend.Emails.send({
            "from": "AI Stock Intelligence <onboarding@resend.dev>",
            "to": [to_email],
            "subject": f"🚨 {stock_name} Alert: {direction} ${alert_price:.2f}",
            "html": html_body
        })
        return {'success': True, 'response': response}
    except Exception as e:
        print(f"Email send error: {e}")
        return {'success': False, 'error': str(e)}