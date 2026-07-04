import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import sign_in, sign_up, is_valid_email

def show_login_page():
    """Show login/signup page"""

    # Custom CSS
    st.markdown("""
    <style>
        .login-header {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00C853, #1565C0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            padding: 1rem 0;
        }
        .login-subheader {
            text-align: center;
            color: #888;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: #1e1e2e;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid #00C853;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<p class="login-header">📈 AI Stock Intelligence</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="login-subheader">Real-time Stock Analysis powered by AI & ML</p>',
                unsafe_allow_html=True)

    # Features showcase
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Live Analysis</h4>
            <p>Real-time stock data with interactive charts</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI Predictions</h4>
            <p>LSTM-powered price predictions</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>📰 Sentiment Analysis</h4>
            <p>Live news sentiment using NLP</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Login/Signup tabs
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    # LOGIN TAB
    with tab1:
        st.subheader("Welcome Back!")
        st.markdown("Login to access your personalized dashboard")

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your@email.com")
            password = st.text_input("🔒 Password",
                                     type="password",
                                     placeholder="Enter your password")
            remember = st.checkbox("Remember me")
            login_btn = st.form_submit_button(
                "🚀 Login", use_container_width=True, type="primary")

        if login_btn:
            if not email or not password:
                st.error("⚠️ Please fill in all fields!")
            elif not is_valid_email(email):
                st.error("⚠️ Please enter a valid email!")
            else:
                with st.spinner("Logging in..."):
                    result = sign_in(email, password)
                    if result['success']:
                        st.session_state.user = result['user']
                        st.session_state.session = result['session']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed! Check your email and password.")

    # SIGNUP TAB
    with tab2:
        st.subheader("Create Your Account")
        st.markdown("Join thousands of investors using AI-powered analysis")

        with st.form("signup_form"):
            full_name = st.text_input("👤 Full Name",
                                      placeholder="Chandana M Shetty")
            email = st.text_input("📧 Email",
                                  placeholder="your@email.com")
            password = st.text_input("🔒 Password",
                                     type="password",
                                     placeholder="Min 6 characters")
            confirm_password = st.text_input("🔒 Confirm Password",
                                             type="password",
                                             placeholder="Repeat password")
            agree = st.checkbox("I agree to Terms & Conditions")
            signup_btn = st.form_submit_button(
                "✨ Create Account", use_container_width=True, type="primary")

        if signup_btn:
            if not full_name or not email or not password:
                st.error("⚠️ Please fill in all fields!")
            elif not is_valid_email(email):
                st.error("⚠️ Please enter a valid email!")
            elif len(password) < 6:
                st.error("⚠️ Password must be at least 6 characters!")
            elif password != confirm_password:
                st.error("⚠️ Passwords don't match!")
            elif not agree:
                st.error("⚠️ Please agree to Terms & Conditions!")
            else:
                with st.spinner("Creating your account..."):
                    result = sign_up(email, password, full_name)
                    if result['success']:
                        st.success("""✅ Account created successfully!
                        Please check your email to verify your account,
                        then login.""")
                    else:
                        st.error(f"❌ Signup failed! {result['error']}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888;'>
        🔒 Secured by Supabase Authentication | 
        Built with ❤️ by Chandana M
    </div>
    """, unsafe_allow_html=True)