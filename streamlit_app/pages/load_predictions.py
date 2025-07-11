# streamlit_app/pages/04_load_predictions.py

import streamlit as st
import pandas as pd
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor

@st.cache_data(show_spinner=False, ttl=600)
def load_predictions_from_athena(
    aws_region: str,
    database: str,
    table: str,
    output_s3_staging: str,
) -> pd.DataFrame:
    """
    Run a SELECT * on your Athena table and return a Pandas DataFrame.
    Caches results for 10 minutes.
    """
    conn = connect(
        s3_staging_dir=output_s3_staging,
        region_name=aws_region,
        cursor_class=PandasCursor,
    )
    query = f"SELECT store, dept, date, store_type, predicted_sales FROM {database}.{table} LIMIT 1000"
    df = pd.read_sql(query, conn)
    return df

def main():
    st.title("📊 Test Set Predictions")
    st.write("This pulls directly from Athena’s `test_predictions` table.")

    # — you could move these to secrets or env-vars —
    AWS_REGION = "us-east-1"
    DATABASE   = "supplychain_genai_catalog"
    TABLE      = "test_predictions"
    STAGING    = "s3://supplychain-genai-optim-jinen/athena-staging/"

    df = load_predictions_from_athena(AWS_REGION, DATABASE, TABLE, STAGING)
    st.dataframe(df, use_container_width=True)

    # simple histogram of predicted sales
    st.subheader("Predicted sales distribution")
    st.bar_chart(df["predicted_sales"].value_counts().sort_index())

if __name__ == "__main__":
    main()