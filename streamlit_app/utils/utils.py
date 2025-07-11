# streamlit_app/utils.py

import streamlit as st
import csv
import os
from datetime import datetime
import boto3

LOG_FILE = "user_actions_log.csv"
AWS_REGION = "us-east-1"
S3_BUCKET = "genai-hackathon-logs"  # Your bucket here

s3 = boto3.client("s3", region_name=AWS_REGION)

def login(username, password):
    users = {
    "admin123": "admin123",
    "user1": "pass"
}
    if username in users and users[username] == password:
        st.session_state.user = username
        return True
    else:
        return False

def is_logged_in():
    return "user" in st.session_state

def logout():
    if "user" in st.session_state:
        del st.session_state.user

def log_user_action(action_desc):
    user = st.session_state.get("user", "unknown")
    timestamp = datetime.now().isoformat()

    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "user", "action"])
        writer.writerow([timestamp, user, action_desc])

    try:
        s3.upload_file(LOG_FILE, S3_BUCKET, LOG_FILE)
    except Exception as e:
        st.warning(f"Failed to upload logs to S3: {e}")