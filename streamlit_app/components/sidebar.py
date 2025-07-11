import streamlit as st
import pandas as pd

def sidebar_inputs():
    st.sidebar.title("Forecast Inputs")

    # Load cleaned dataset to extract date bounds (once per app load)
    df = pd.read_csv("/Users/jinenmodi/ImpData/supplychain-genai-optim/data/processed/cleaned_walmart_data.csv", parse_dates=['Date'])
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()

    store = st.sidebar.number_input("Store ID", min_value=1, max_value=45, value=1)
    dept = st.sidebar.number_input("Department ID", min_value=1, max_value=99, value=1)
    
    st.sidebar.markdown(f"**Available Dates:** {min_date} → {max_date}")
    date_input = st.sidebar.date_input("Forecast Date", min_value=min_date, max_value=max_date, value=min_date)

    return store, dept, date_input.strftime("%Y-%m-%d")