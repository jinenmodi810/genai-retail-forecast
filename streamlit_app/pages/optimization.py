import streamlit as st
import pandas as pd
import boto3
import json
import os
import csv
from datetime import datetime

st.set_page_config(page_title="Inventory Optimization & Alerts", layout="wide")

st.title("📦 Inventory Optimization & Reorder Alerts Demo")

# Sample default data for demo
default_inventory_data = {
    "Store": [1, 1, 2, 2],
    "Dept": [1, 2, 1, 2],
    "Inventory_Qty": [50, 20, 60, 15],
    "Reorder_Point": [30, 25, 40, 10]
}

default_forecast_data = {
    "Store": [1, 1, 2, 2],
    "Dept": [1, 2, 1, 2],
    "Forecast_Qty": [25, 10, 30, 20]
}

@st.cache_data
def load_sample_data():
    df_inventory = pd.DataFrame(default_inventory_data)
    df_forecast = pd.DataFrame(default_forecast_data)
    return df_inventory, df_forecast

st.sidebar.header("Upload your CSV files (Optional)")

uploaded_inventory = st.sidebar.file_uploader("Upload Inventory CSV", type=["csv"])
uploaded_forecast = st.sidebar.file_uploader("Upload Forecast CSV", type=["csv"])

if uploaded_inventory is not None:
    df_inventory = pd.read_csv(uploaded_inventory)
else:
    df_inventory, _ = load_sample_data()

if uploaded_forecast is not None:
    df_forecast = pd.read_csv(uploaded_forecast)
else:
    _, df_forecast = load_sample_data()

st.subheader("Current Inventory")
st.dataframe(df_inventory)

st.subheader("Forecasted Demand")
st.dataframe(df_forecast)

# Merge inventory and forecast on Store & Dept
df = pd.merge(df_inventory, df_forecast, on=["Store", "Dept"], how="inner")

# Calculate reorder alert
df["Reorder_Alert"] = df["Inventory_Qty"] < (df["Forecast_Qty"] + df["Reorder_Point"])

st.subheader("Inventory Status with Reorder Alerts")
def alert_style(row):
    color = 'background-color: #ffcccc' if row.Reorder_Alert else ''
    return [color]*len(row)

st.dataframe(df.style.apply(alert_style, axis=1))

st.markdown("""
### Reorder Alert Summary
- Red highlighted rows indicate inventory below forecast + reorder point → reorder needed.
""")

# SNS setup
AWS_REGION = "us-east-1"
# Fixed ARN - remove the trailing UUID suffix
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:590183971264:GenAI-Reorder-Alerts"

sns_client = boto3.client("sns", region_name=AWS_REGION)

def send_sns_alert(store, dept, inventory, forecast, reorder_point):
    message = (
        f"🚨 Reorder Alert:\n"
        f"Store: {store}, Dept: {dept}\n"
        f"Current Inventory: {inventory}\n"
        f"Forecast Demand: {forecast}\n"
        f"Reorder Point: {reorder_point}\n"
        f"Action: Please reorder stock immediately."
    )
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="GenAI Inventory Reorder Alert"
    )
    return response

st.subheader("Send Reorder Alerts via AWS SNS")

if st.button("Send Alerts for all flagged rows"):
    alerts = df[df["Reorder_Alert"]]
    if alerts.empty:
        st.success("No reorder alerts to send. Inventory levels are sufficient.")
    else:
        success_count = 0
        failed_count = 0
        for _, row in alerts.iterrows():
            try:
                resp = send_sns_alert(row.Store, row.Dept, row.Inventory_Qty, row.Forecast_Qty, row.Reorder_Point)
                if resp.get("MessageId"):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                st.error(f"Failed to send alert for Store {row.Store} Dept {row.Dept}: {str(e)}")
                failed_count += 1
        st.success(f"Alerts sent: {success_count}")
        if failed_count:
            st.warning(f"Failed to send: {failed_count}")

st.markdown("---")

# ======= FEEDBACK LOGIC START =======
# ======= FEEDBACK LOGIC START =======
FEEDBACK_FILE = "feedback.csv"

def save_feedback(store, dept, feedback):
    file_exists = os.path.isfile(FEEDBACK_FILE)
    with open(FEEDBACK_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "store", "dept", "feedback"])
        writer.writerow([datetime.now().isoformat(), store, dept, feedback])

def send_feedback_sns(store, dept, feedback):
    message = (
        f"📝 New Feedback Received:\n"
        f"Store: {store}\n"
        f"Department: {dept}\n"
        f"Question: Was this alert helpful?\n"
        f"Answer: {feedback}\n"
        f"Timestamp: {datetime.now().isoformat()}"
    )
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="GenAI Inventory Alert Feedback"
        )
        return True
    except Exception as e:
        st.warning(f"Failed to send SNS feedback notification: {e}")
        return False

alerts = df[df["Reorder_Alert"]]
if alerts.empty:
    st.info("No reorder alerts currently to provide feedback.")
else:
    feedback_responses = {}
    for _, row in alerts.iterrows():
        st.write(f"Store {row.Store}, Dept {row.Dept} - Reorder Alert")
        feedback_key = f"feedback_{row.Store}_{row.Dept}"
        feedback_responses[feedback_key] = st.radio(
            "Was this alert helpful?",
            ("Yes", "No"),
            key=feedback_key
        )
    if st.button("Submit Feedback for All Alerts"):
        for _, row in alerts.iterrows():
            key = f"feedback_{row.Store}_{row.Dept}"
            feedback = feedback_responses.get(key)
            if feedback:
                save_feedback(row.Store, row.Dept, feedback)
                sent = send_feedback_sns(row.Store, row.Dept, feedback)
                if sent:
                    st.success(f"Feedback for Store {row.Store} Dept {row.Dept} submitted and notification sent.")
                else:
                    st.error(f"Failed to send SNS notification for Store {row.Store} Dept {row.Dept}.")

# ======= EXPLAINABILITY TEXT START =======
st.markdown("""
---
### How Forecasts Are Made

Our TimeLLM model leverages historical sales data and advanced time-series modeling to predict future demand, accounting for seasonality and trends.

### Reorder Alerts Logic

Alerts trigger when inventory falls below the forecasted demand plus reorder buffer to prevent stockouts and ensure timely replenishment.

### Feedback Helps Us Improve

Your feedback on alerts helps refine our models and optimize inventory management.
""")
# ======= EXPLAINABILITY TEXT END =======