# components/crosscheck.py

import pandas as pd
import os
import joblib
from agents.forecast_agent import prepare_features, make_prediction

# Path to cleaned data
CLEANED_DATA_PATH = '/Users/jinenmodi/ImpData/supplychain-genai-optim/data/processed/cleaned_walmart_data.csv'
df = pd.read_csv(CLEANED_DATA_PATH, parse_dates=['Date'])

# --- Actual Sales ---
def get_actual_sales(store_id, dept_id, date_obj):
    match = df[
        (df['Store'] == store_id) &
        (df['Dept'] == dept_id) &
        (df['Date'] == pd.to_datetime(date_obj))
    ]
    if not match.empty:
        return float(match['Weekly_Sales'].values[0])
    else:
        return None

# --- Forecast Sales ---
def get_forecast_sales(store_id, dept_id, date_obj):
    prediction = make_prediction(store_id, dept_id, date_obj)
    if prediction is None:
        return None
    return round(float(prediction), 2)