# forecast_agent.py

import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Paths
MODEL_DIR = '/Users/jinenmodi/ImpData/supplychain-genai-optim/models/groupwise_by_type'
CLEANED_DATA_PATH = '/Users/jinenmodi/ImpData/supplychain-genai-optim/data/processed/cleaned_walmart_data.csv'

# Load cleaned dataset for feature lookup
df_full = pd.read_csv(CLEANED_DATA_PATH, parse_dates=['Date'])

# --- Feature Preparation ---
def prepare_features(store_id, dept_id, date_obj):
    row = df_full[
        (df_full['Store'] == store_id) &
        (df_full['Dept'] == dept_id) &
        (df_full['Date'] == pd.to_datetime(date_obj))
    ]

    if row.empty:
        return None

    # Encode 'Type' same as training
    row['Type'] = row['Type'].astype('category').cat.codes

    feature_cols = [
        'Store', 'Dept', 'Type', 'IsHoliday',
        'Temperature', 'Fuel_Price', 'CPI', 'Unemployment',
        'MarkDown1', 'MarkDown2', 'MarkDown3', 'MarkDown4', 'MarkDown5',
        'Year', 'Month', 'Week', 'Day', 'Quarter', 'IsMonthStart', 'IsMonthEnd'
    ]

    return row[feature_cols].astype(float)

# --- Prediction Function ---
def make_prediction(store_id, dept_id, date_obj):
    features = prepare_features(store_id, dept_id, date_obj)
    if features is None:
        return None

    # Use the 'Type' value from original df for this row
    type_code = df_full[
        (df_full['Store'] == store_id) & (df_full['Dept'] == dept_id)
    ]['Type'].astype('category').cat.codes

    if type_code.empty:
        return None

    model_path = os.path.join(MODEL_DIR, f"xgb_type_{type_code.iloc[0]}.pkl")
    if not os.path.exists(model_path):
        return None

    model = joblib.load(model_path)
    y_pred = model.predict(features)[0]
    return y_pred