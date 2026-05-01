import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from datetime import date
import sqlite3
import hashlib

# Set page config MUST be the first Streamlit command
st.set_page_config(page_title="Personal Expense Analyzer", page_icon="💸", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE SETUP ---
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0] == make_hash(password)
    return False

def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, make_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

init_db()

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'
if 'manual_expenses' not in st.session_state:
    st.session_state.manual_expenses = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Payment_Mode'])

# --- LOGIN & SIGNUP PAGE ---
def login_page():
    st.markdown("<h1 style='text-align: center;' class='fade-in'>💸 Expense Analyzer</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <style>
            .auth-container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
                color: inherit;
                animation: slideUp 0.8s ease-out;
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
        <div class="auth-container">
        """, unsafe_allow_html=True)
        
        auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
        
        with auth_tab1:
            st.subheader("Login to your account")
            l_username = st.text_input("Username", key="l_user")
            l_password = st.text_input("Password", type="password", key="l_pass")
            if st.button("Login", use_container_width=True):
                if check_user(l_username, l_password):
                    st.session_state.logged_in = True
                    st.session_state.username = l_username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    
        with auth_tab2:
            st.subheader("Create a new account")
            s_username = st.text_input("New Username", key="s_user")
            s_password = st.text_input("New Password", type="password", key="s_pass")
            if st.button("Sign Up", use_container_width=True):
                if s_username and s_password:
                    if create_user(s_username, s_password):
                        st.success("Account created successfully! You can now log in.")
                    else:
                        st.error("Username already exists.")
                else:
                    st.warning("Please enter a username and password.")
                    
        st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN APP FUNCTION ---
def main_app():
    # --- DYNAMIC CSS FOR THEME & ANIMATIONS ---
    if st.session_state.theme == 'Dark':
        bg_rgba = "rgba(30, 30, 30, 0.7)"
        border_color = "rgba(255, 255, 255, 0.1)"
        text_color = "#FFFFFF"
        metric_val_color = "#00FF7F"
        label_color = "#A9A9A9"
        alert_bg = "rgba(255, 69, 0, 0.15)"
        alert_border = "#FF4500"
        plotly_theme = "plotly_dark"
    else:
        bg_rgba = "rgba(255, 255, 255, 0.8)"
        border_color = "rgba(0, 0, 0, 0.1)"
        text_color = "#000000"
        metric_val_color = "#008000"
        label_color = "#555555"
        alert_bg = "rgba(255, 69, 0, 0.05)"
        alert_border = "#FF4500"
        plotly_theme = "plotly_white"

    st.markdown(f"""
    <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: scale(0.95); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(-20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.6s ease-out;
        }}
        
        /* Glassmorphism Responsive Metric Cards */
        .metric-card {{
            background: {bg_rgba};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {border_color};
            color: {text_color};
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 1rem;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            animation: fadeIn 0.5s ease-out;
        }}
        .metric-card:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 14px 28px rgba(0,0,0,0.15), 0 10px 10px rgba(0,0,0,0.12);
        }}
        .metric-value {{
            font-size: clamp(1.5rem, 4vw, 2.2rem);
            font-weight: 800;
            color: {metric_val_color};
            margin-top: 10px;
        }}
        .metric-label {{
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            color: {label_color};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .alert-card {{
            background: {alert_bg};
            border-left: 5px solid {alert_border};
            backdrop-filter: blur(5px);
            padding: 20px;
            margin-top: 15px;
            border-radius: 10px;
            color: {text_color};
            animation: slideIn 0.5s ease-out forwards;
            transition: transform 0.2s;
        }}
        .alert-card:hover {{
            transform: translateX(5px);
        }}
        .insight-card {{
            background: {bg_rgba};
            border-left: 5px solid #00BFFF;
            backdrop-filter: blur(5px);
            padding: 20px;
            margin-top: 15px;
            border-radius: 10px;
            color: {text_color};
            animation: slideIn 0.6s ease-out forwards;
        }}
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    st.sidebar.title(f"💸 Welcome, {st.session_state.username}")
    
    st.sidebar.subheader("App Settings")
    theme_col, logout_col = st.sidebar.columns(2)
    with theme_col:
        if st.button("🌗 Theme"):
            st.session_state.theme = 'Light' if st.session_state.theme == 'Dark' else 'Dark'
            st.rerun()
    with logout_col:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.sidebar.markdown("---")

    st.sidebar.subheader("1. Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

    st.sidebar.subheader("2. Manual Entry")
    with st.sidebar.expander("Add New Expense"):
        with st.form("expense_form", clear_on_submit=True):
            date_input = st.date_input("Date", value=date.today())
            category_input = st.selectbox("Category", ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"])
            amount_input = st.number_input("Amount", min_value=0.0, format="%.2f")
            payment_input = st.selectbox("Payment Mode", ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer"])
            submit_button = st.form_submit_button("Add Expense")
            
            if submit_button:
                new_expense = pd.DataFrame({
                    'Date': [date_input],
                    'Category': [category_input],
                    'Amount': [amount_input],
                    'Payment_Mode': [payment_input]
                })
                st.session_state.manual_expenses = pd.concat([st.session_state.manual_expenses, new_expense], ignore_index=True)
                st.success("Expense added successfully!")

    # Combine data
    df = pd.DataFrame()
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")

    if not st.session_state.manual_expenses.empty:
        if not df.empty:
            df = pd.concat([df, st.session_state.manual_expenses], ignore_index=True)
        else:
            df = st.session_state.manual_expenses.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("3. Budget")
    budget = st.sidebar.number_input("Set Monthly Budget ($)", min_value=0.0, value=1000.0, step=100.0)

    # --- MAIN CONTENT ---
    st.markdown("<h1 class='fade-in'>Personal Expense Analyzer 📊</h1>", unsafe_allow_html=True)
    
    if df.empty:
        st.info("👋 Upload a CSV file or add expenses manually from the sidebar to get started.")
    else:
        expected_cols = ['Date', 'Category', 'Amount', 'Payment_Mode']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
        else:
            df['Date'] = pd.to_datetime(df['Date'])
            df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
            df['Month'] = df['Date'].dt.month
            df['Year'] = df['Date'].dt.year
            df = df.sort_values(by='Date')
            
            tab1, tab2, tab3 = st.tabs(["📋 Dashboard", "🧠 Insights & Predictions", "📁 Data & Export"])
            
            min_date = df['Date'].min().date()
            max_date = df['Date'].min().date() if df['Date'].min() == df['Date'].max() else df['Date'].max().date()
            
            col_filter1, col_filter2 = st.columns([1, 3])
            with col_filter1:
                if min_date == max_date:
                    start_date, end_date = min_date, max_date
                else:
                    try:
                        date_range = st.date_input("Filter Date Range", [min_date, max_date])
                        if len(date_range) == 2:
                            start_date, end_date = date_range
                        else:
                            start_date, end_date = date_range[0], date_range[0]
                    except ValueError:
                        start_date, end_date = min_date, max_date
            
            mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
            filtered_df = df.loc[mask]
            
            if filtered_df.empty:
                st.warning("No data found for the selected date range.")
                return

            total_expense = filtered_df['Amount'].sum()
            months_count = filtered_df['YearMonth'].nunique()
            monthly_avg = total_expense / months_count if months_count > 0 else total_expense
            top_category = filtered_df.groupby('Category')['Amount'].sum().idxmax()
            
            daily_spending = filtered_df.groupby(filtered_df['Date'].dt.date)['Amount'].sum()
            highest_spending_day = daily_spending.idxmax()

            # --- TAB 1: DASHBOARD ---
            with tab1:
                st.markdown("### 🔑 Key Metrics")
                c1, c2, c3, c4 = st.columns(4)
                
                with c1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Total</div><div class="metric-value">${total_expense:,.2f}</div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Avg/Month</div><div class="metric-value">${monthly_avg:,.2f}</div></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Top Category</div><div class="metric-value">{top_category}</div></div>', unsafe_allow_html=True)
                with c4:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Highest Day</div><div class="metric-value">{highest_spending_day.strftime("%b %d")}</div></div>', unsafe_allow_html=True)
                    
                budget_variance = budget - monthly_avg
                if budget_variance >= 0:
                    st.success(f"🎉 **Budget Status:** You are under budget by **${budget_variance:,.2f}** per month!")
                else:
                    st.error(f"⚠️ **Budget Status:** You are over budget by **${abs(budget_variance):,.2f}** per month!")
                    
                st.markdown("---")
                
                v_col1, v_col2 = st.columns(2)
                with v_col1:
                    category_sum = filtered_df.groupby('Category', as_index=False)['Amount'].sum()
                    fig_pie = px.pie(category_sum, values='Amount', names='Category', title="Category-wise Distribution", hole=0.4, template=plotly_theme)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                with v_col2:
                    daily_trend = filtered_df.groupby('Date', as_index=False)['Amount'].sum()
                    fig_line = px.line(daily_trend, x='Date', y='Amount', title="Daily Spending Trend", markers=True, line_shape='spline', template=plotly_theme)
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                monthly_sum = filtered_df.groupby('YearMonth', as_index=False)['Amount'].sum().sort_values(by='YearMonth')
                fig_bar = px.bar(monthly_sum, x='YearMonth', y='Amount', title="Monthly Expenses Comparison", text_auto='.2s', color='Amount', template=plotly_theme)
                st.plotly_chart(fig_bar, use_container_width=True)

            # --- TAB 2: INSIGHTS & PREDICTIONS ---
            with tab2:
                st.markdown("### 🤖 Smart AI Insights")
                
                # Rule-based AI Engine
                category_totals = filtered_df.groupby('Category')['Amount'].sum()
                if total_expense > 0:
                    for cat, amt in category_totals.items():
                        percentage = (amt / total_expense) * 100
                        if percentage > 40:
                            st.markdown(f"""
                            <div class="insight-card">
                                💡 <b>Insight:</b> You are spending <b>{percentage:.1f}%</b> of your total budget on <b>{cat}</b> (${amt:,.2f}). 
                                Consider finding ways to cut down costs in this category to improve your savings.
                            </div>
                            """, unsafe_allow_html=True)
                        elif percentage < 5 and cat != "Other":
                            st.markdown(f"""
                            <div class="insight-card" style="border-left-color: #00FF7F;">
                                ⭐ <b>Great Job:</b> Your <b>{cat}</b> expenses are impressively low at just <b>{percentage:.1f}%</b> of your total!
                            </div>
                            """, unsafe_allow_html=True)
                            
                # Anomalies
                st.markdown("<br>### 🚨 Anomalies Detected", unsafe_allow_html=True)
                if len(filtered_df) > 5:
                    q1 = filtered_df['Amount'].quantile(0.25)
                    q3 = filtered_df['Amount'].quantile(0.75)
                    iqr = q3 - q1
                    upper_bound = q3 + 1.5 * iqr
                    unusual_expenses = filtered_df[filtered_df['Amount'] > upper_bound]
                    
                    if not unusual_expenses.empty:
                        for _, row in unusual_expenses.iterrows():
                            st.markdown(f'<div class="alert-card"><b>{row["Date"].strftime("%Y-%m-%d")}</b>: Unusually high expense of <b>${row["Amount"]:,.2f}</b> on {row["Category"]}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No unusual spikes in spending detected!")
                else:
                    st.info("Not enough data to calculate unusual expenses.")
                
                # Predictions
                st.markdown("<br>### 🔮 Next Month Prediction", unsafe_allow_html=True)
                if len(monthly_sum) > 2:
                    monthly_sum['MonthIndex'] = np.arange(len(monthly_sum))
                    X = monthly_sum[['MonthIndex']].values
                    y = monthly_sum['Amount'].values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    next_month_idx = np.array([[len(monthly_sum)]])
                    prediction = model.predict(next_month_idx)[0]
                    
                    st.info(f"Based on trends, your predicted expense for next month is: **${max(0, prediction):,.2f}**")
                    
                    future_df = pd.DataFrame({'MonthIndex': [len(monthly_sum)], 'Amount': [max(0, prediction)], 'Type': ['Predicted']})
                    monthly_sum['Type'] = 'Actual'
                    combined_df = pd.concat([monthly_sum, future_df], ignore_index=True)
                    
                    fig_pred = px.line(combined_df, x='MonthIndex', y='Amount', color='Type', title="Spending Trend & Prediction", markers=True, template=plotly_theme)
                    st.plotly_chart(fig_pred, use_container_width=True)
                else:
                    st.info("Need at least 3 months of data to predict next month's expenses.")

            # --- TAB 3: DATA & EXPORT ---
            with tab3:
                st.subheader("📁 Data Export & View")
                
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name='expense_report.csv',
                    mime='text/csv',
                    use_container_width=True
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(filtered_df.style.format({"Amount": "${:.2f}"}), use_container_width=True)

# --- RUN APP ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
