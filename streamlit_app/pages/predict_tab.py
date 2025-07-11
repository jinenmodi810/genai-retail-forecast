import sys
sys.path.append("model_upload/code")

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pyathena import connect
from inference.time_llm_forecastor import TimeLLMForecastor

st.set_page_config(layout="wide")
st.title("📊 TimeLLM Forecast from Walmart Data")
st.markdown("Forecast future sales using **real historical Walmart data** and our custom GPT2-powered TimeLLM model.")

# Load model once
@st.cache_resource
def load_model():
    return TimeLLMForecastor()

model = load_model()

# Inputs
store_id = st.number_input("🏬 Store ID", min_value=1, value=1)
dept_id = st.number_input("📦 Department ID", min_value=1, value=1)
forecast_date = st.date_input("📅 Forecast Cutoff Date")

# Query Athena & Forecast
if st.button("🔮 Forecast with TimeLLM"):
    try:
        conn = connect(
            s3_staging_dir="s3://supplychain-genai-optim-jinen/query-results/",
            region_name="us-east-1"
        )
        query = f"""
            SELECT weekly_sales
            FROM supplychain_genai_catalog.joined
            WHERE store = {store_id}
              AND dept = {dept_id}
              AND CAST(date AS DATE) < DATE('{forecast_date}')
            ORDER BY date DESC
            LIMIT 48
        """
        df = pd.read_sql(query, conn)

        if df.shape[0] < model.config.seq_len:
            st.warning(f"❗ Not enough data: only {df.shape[0]} weeks found.")
        else:
            # Order from oldest to latest
            series = df["weekly_sales"].iloc[::-1].tolist()
            forecast = model.predict(series)

            st.success("✅ Forecast generated using real Walmart data.")
            st.markdown("### 🔍 Forecast Output")
            st.json(forecast)

            # Line plot
            full_series = series + [None] * len(forecast)
            forecast_only = [None] * len(series) + forecast
            chart_df = pd.DataFrame({
                "Historical Sales": full_series,
                "TimeLLM Forecast": forecast_only
            })
            st.markdown("### 📈 Forecast Visualization")
            st.line_chart(chart_df)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")