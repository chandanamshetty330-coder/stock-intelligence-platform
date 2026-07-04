import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st
import re

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client():
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_authed_client():
    """Get authenticated Supabase client with user session"""
    supabase = get_supabase_client()
    try:
        if 'session' in st.session_state and st.session_state.session:
            access_token = st.session_state.session.access_token
            refresh_token = st.session_state.session.refresh_token
            supabase.auth.set_session(access_token, refresh_token)
    except Exception as e:
        print(f"Session error: {e}")
    return supabase

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sign_up(email, password, full_name):
    """Register new user"""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {'full_name': full_name}
            }
        })
        return {'success': True, 'user': response.user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def sign_in(email, password):
    """Login user"""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        return {'success': True, 'user': response.user,
                'session': response.session}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def sign_out():
    """Logout user"""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_current_user():
    """Get current logged in user"""
    if 'user' in st.session_state:
        return st.session_state.user
    return None

def is_authenticated():
    """Check if user is logged in"""
    return 'user' in st.session_state and st.session_state.user is not None

def save_portfolio(user_id, ticker, stock_name, quantity, buy_price):
    """Save portfolio item to database"""
    try:
        supabase = get_authed_client()
        response = supabase.table('portfolio').insert({
            'user_id': str(user_id),
            'ticker': ticker,
            'stock_name': stock_name,
            'quantity': quantity,
            'buy_price': float(buy_price)
        }).execute()
        print(f"Portfolio saved: {response}")
        return {'success': True}
    except Exception as e:
        print(f"Portfolio save error: {e}")
        return {'success': False, 'error': str(e)}

def get_portfolio(user_id):
    """Get user portfolio from database"""
    try:
        supabase = get_authed_client()
        response = supabase.table('portfolio').select('*').eq(
            'user_id', str(user_id)).execute()
        return response.data
    except Exception as e:
        print(f"Portfolio get error: {e}")
        return []

def delete_portfolio_item(item_id):
    """Delete portfolio item"""
    try:
        supabase = get_authed_client()
        supabase.table('portfolio').delete().eq(
            'id', str(item_id)).execute()
        return {'success': True}
    except Exception as e:
        print(f"Delete error: {e}")
        return {'success': False, 'error': str(e)}

def save_alert(user_id, ticker, alert_price, alert_type):
    """Save price alert to database"""
    try:
        supabase = get_authed_client()
        response = supabase.table('alerts').insert({
            'user_id': str(user_id),
            'ticker': ticker,
            'alert_price': float(alert_price),
            'alert_type': alert_type
        }).execute()
        return {'success': True}
    except Exception as e:
        print(f"Alert save error: {e}")
        return {'success': False, 'error': str(e)}

def get_alerts(user_id):
    """Get user alerts from database"""
    try:
        supabase = get_authed_client()
        response = supabase.table('alerts').select('*').eq(
            'user_id', str(user_id)).execute()
        return response.data
    except Exception as e:
        print(f"Alerts get error: {e}")
        return []

def save_watchlist(user_id, ticker, stock_name, added_price):
    """Save stock to watchlist"""
    try:
        supabase = get_authed_client()
        supabase.table('watchlist').insert({
            'user_id': str(user_id),
            'ticker': ticker,
            'stock_name': stock_name,
            'added_price': float(added_price)
        }).execute()
        return {'success': True}
    except Exception as e:
        print(f"Watchlist save error: {e}")
        return {'success': False, 'error': str(e)}

def get_watchlist(user_id):
    """Get user's watchlist"""
    try:
        supabase = get_authed_client()
        response = supabase.table('watchlist').select('*').eq(
            'user_id', str(user_id)).execute()
        return response.data
    except Exception as e:
        print(f"Watchlist get error: {e}")
        return []

def delete_watchlist_item(item_id):
    """Remove item from watchlist"""
    try:
        supabase = get_authed_client()
        supabase.table('watchlist').delete().eq(
            'id', str(item_id)).execute()
        return {'success': True}
    except Exception as e:
        print(f"Watchlist delete error: {e}")
        return {'success': False, 'error': str(e)}

def save_trade(user_id, ticker, stock_name, trade_type, quantity, price, notes=''):
    """Record a buy/sell trade"""
    try:
        supabase = get_authed_client()
        total = float(quantity) * float(price)
        supabase.table('trade_history').insert({
            'user_id': str(user_id),
            'ticker': ticker,
            'stock_name': stock_name,
            'trade_type': trade_type,
            'quantity': int(quantity),
            'price': float(price),
            'total_value': total,
            'notes': notes
        }).execute()
        return {'success': True}
    except Exception as e:
        print(f"Trade save error: {e}")
        return {'success': False, 'error': str(e)}

def get_trade_history(user_id):
    """Get user's trade history, most recent first"""
    try:
        supabase = get_authed_client()
        response = supabase.table('trade_history').select('*').eq(
            'user_id', str(user_id)).order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Trade history get error: {e}")
        return []
    
def delete_trade_item(item_id):
    """Delete a trade history record"""
    try:
        supabase = get_authed_client()
        supabase.table('trade_history').delete().eq(
            'id', str(item_id)).execute()
        return {'success': True}
    except Exception as e:
        print(f"Trade delete error: {e}")
        return {'success': False, 'error': str(e)}

import base64

def get_profile(user_id):
    """Get user's profile data (name, phone, avatar, bio)"""
    try:
        supabase = get_authed_client()
        response = supabase.table('profiles').select('*').eq(
            'id', str(user_id)).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Get profile error: {e}")
        return None

def upsert_profile(user_id, full_name=None, phone=None, avatar_url=None, bio=None,
                   default_stock=None, default_stock_name=None,
                   currency=None, landing_page=None):
    """Create or update user's profile row"""
    try:
        supabase = get_authed_client()
        data = {'id': str(user_id)}
        if full_name is not None:
            data['full_name'] = full_name
        if phone is not None:
            data['phone'] = phone
        if avatar_url is not None:
            data['avatar_url'] = avatar_url
        if bio is not None:
            data['bio'] = bio
        if default_stock is not None:
            data['default_stock'] = default_stock
        if default_stock_name is not None:
            data['default_stock_name'] = default_stock_name
        if currency is not None:
            data['currency'] = currency
        if landing_page is not None:
            data['landing_page'] = landing_page
        supabase.table('profiles').upsert(data).execute()
        return {'success': True}
    except Exception as e:
        print(f"Upsert profile error: {e}")
        return {'success': False, 'error': str(e)}

def upload_avatar(user_id, file_bytes, file_ext='png'):
    """Upload a profile picture to Supabase Storage and return its public URL"""
    try:
        supabase = get_authed_client()
        file_path = f"{user_id}/avatar.{file_ext}"
        supabase.storage.from_('avatars').upload(
            file_path, file_bytes,
            file_options={"upsert": "true", "content-type": f"image/{file_ext}"}
        )
        # Build the public URL manually with a cache-busting timestamp,
        # since get_public_url() can return a malformed path on some client versions
        import time
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{file_path}?t={int(time.time())}"
        return {'success': True, 'url': public_url}
    except Exception as e:
        print(f"Avatar upload error: {e}")
        return {'success': False, 'error': str(e)}

def update_display_name(full_name):
    """Update the name stored in Supabase Auth user_metadata (used across the app)"""
    try:
        supabase = get_authed_client()
        supabase.auth.update_user({'data': {'full_name': full_name}})
        return {'success': True}
    except Exception as e:
        print(f"Update name error: {e}")
        return {'success': False, 'error': str(e)}

def change_password(new_password):
    """Change the logged-in user's password"""
    try:
        supabase = get_authed_client()
        supabase.auth.update_user({'password': new_password})
        return {'success': True}
    except Exception as e:
        print(f"Change password error: {e}")
        return {'success': False, 'error': str(e)}

def get_settings(user_id):
    """Get user settings from profiles table (reusing bio-adjacent fields via a settings JSON approach)"""
    try:
        supabase = get_authed_client()
        response = supabase.table('profiles').select('*').eq(
            'id', str(user_id)).execute()
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        print(f"Get settings error: {e}")
        return {}

def delete_account(user_id):
    """Delete all user data across tables. Auth user itself must be deleted
    via Supabase dashboard or an admin-privileged server call (not possible
    from the client SDK for security reasons)."""
    try:
        supabase = get_authed_client()
        supabase.table('portfolio').delete().eq('user_id', str(user_id)).execute()
        supabase.table('alerts').delete().eq('user_id', str(user_id)).execute()
        supabase.table('watchlist').delete().eq('user_id', str(user_id)).execute()
        supabase.table('trade_history').delete().eq('user_id', str(user_id)).execute()
        supabase.table('profiles').delete().eq('id', str(user_id)).execute()
        return {'success': True}
    except Exception as e:
        print(f"Delete account error: {e}")
        return {'success': False, 'error': str(e)}              