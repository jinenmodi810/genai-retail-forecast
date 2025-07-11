import streamlit as st
import pandas as pd
from datetime import datetime
from components.sidebar import sidebar_inputs
from agents.forecast_agent import make_prediction
from components.crosscheck import get_actual_sales, get_forecast_sales
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor
import pandas as pd
import streamlit as st
from utils.utils import login, is_logged_in, logout, log_user_action
import os

st.set_page_config(
    page_title="GenAI Forecast",
    page_icon="📈",  # optional emoji icon
    layout="wide"
)

def local_css(file_name):
    full_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(full_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

st.markdown("# AI-Powered Retail Sales Forecast")
st.markdown("## Secure Login Portal")
st.write("Please enter your username and password to continue.")

if not is_logged_in():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.success(f"Welcome {username}!")
            log_user_action("User logged in")
                # optional clear memo
        else:
            st.error("Invalid credentials")
    st.stop()

else:
    st.sidebar.write(f"Logged in as: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        log_user_action("User logged out")
        logout()
           # optional clear memo

# Page setup
st.set_page_config(page_title="Retail Demand Forecasting", layout="centered")
st.title("AI-Powered Retail Sales Forecast")

# --- Forecasting Section ---
store, dept, date_str = sidebar_inputs()

if st.button("Predict Weekly Sales"):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        prediction = make_prediction(store, dept, date_obj)

        if prediction is not None:
            st.success(f"Predicted Weekly Sales for Dept {dept} on {date_str}: **${prediction:,.2f}**")
        else:
            st.warning("No prediction available for the selected inputs. Please check if model or data exists.")
    except Exception as e:
        st.error(f"Prediction failed: {e}")

# --- Cross-Check Historical Section ---
st.subheader("Cross-Check Actual vs Forecast (Backtest)")

with st.form("crosscheck_form"):
    st.write("Compare historical actual sales with forecast for a specific date.")

    store_id_check = st.number_input("Store ID", min_value=1, max_value=45, value=1)
    dept_id_check = st.number_input("Dept ID", min_value=1, max_value=99, value=1)
    date_check = st.date_input("Date to Check", value=pd.to_datetime("2012-01-01"))

    run_check = st.form_submit_button("Compare")

    if run_check:
        actual = get_actual_sales(store_id_check, dept_id_check, date_check)
        predicted = get_forecast_sales(store_id_check, dept_id_check, date_check)

        if actual is not None:
            st.info(f"Actual Weekly Sales: **${actual:,.2f}**")
        else:
            st.warning("No historical sales found for the selected date.")

        if predicted is not None:
            st.success(f"Forecasted Sales (from cleaned data): **${predicted:,.2f}**")
            if actual is not None:
                abs_error = abs(actual - predicted)
                pct_error = abs_error / actual * 100
                st.write(f"Absolute Error: **${abs_error:,.2f}**")
                st.write(f"Percent Error: **{pct_error:.2f}%**")
        else:
            st.warning("No forecast available (entry not found in cleaned dataset).")

# --- Style ---
try:
    with open("streamlit_app/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Custom styling skipped: style.css not found.")