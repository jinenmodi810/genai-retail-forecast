import os
import pandas as pd
import boto3
import joblib
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO



def derive_temporal_features(df, date_col='Date'):
    """
    From df[Date] generate:
      - Year, Month, Week, Day, Quarter
      - IsMonthStart, IsMonthEnd
    """
    df[date_col] = pd.to_datetime(df[date_col])
    df['Year']         = df[date_col].dt.year
    df['Month']        = df[date_col].dt.month
    df['Week']         = df[date_col].dt.isocalendar().week
    df['Day']          = df[date_col].dt.weekday
    df['Quarter']      = df[date_col].dt.quarter
    df['IsMonthStart'] = (df[date_col].dt.day == 1).astype(int)
    df['IsMonthEnd']   = (df[date_col].dt.day >= 28).astype(int)
    return df

# 1. Load test features from S3
def load_test_features(s3_bucket, s3_prefix):
    print("Loading test features...")
    s3 = boto3.client('s3')
    objs = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)

    parquet_files = [obj['Key'] for obj in objs.get('Contents', []) if obj['Key'].endswith('.parquet')]
    if not parquet_files:
        raise FileNotFoundError(f"No Parquet files found in s3://{s3_bucket}/{s3_prefix}")

    dfs = []
    for key in parquet_files:
        obj = s3.get_object(Bucket=s3_bucket, Key=key)
        df = pd.read_parquet(BytesIO(obj['Body'].read()))
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

# Map the categorical store_type values (A/B/C) to the numeric codes 1,2,3
STORE_TYPE_MAP = {
    'A': 0,
    'B': 1,
    'C': 2
}
# 2. Load local model for a given store type (1, 2, 3)
def load_model(store_type, model_base_path="/Users/jinenmodi/ImpData/supplychain-genai-optim/models/groupwise_by_type"):
    store_type_map = {'A': 0, 'B': 1, 'C': 2}
    numeric_type = store_type_map.get(store_type, store_type)  # fallback to numeric if already mapped
    model_path = os.path.join(model_base_path, f"xgb_type_{numeric_type}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


# 3. Run predictions for each store type
def predict_groupwise(df):
    print("Running predictions...")
    all_preds = []

    if 'store_type' not in df.columns:
        raise KeyError("Missing 'store_type' in input")

    for st in df['store_type'].unique():
        print(f"• store_type = {st}")
        model = load_model(st)
        sub = df[df['store_type']==st].copy()

        # 1) rename the S3-joined feature columns
        rename = {
          'features_store':'Store',
          'store':'Store',
          'features_date':'Date',
          'date':'Date',
          'isholiday':'IsHoliday',
          'features_temperature':'Temperature',
          'features_fuel_price':'Fuel_Price',
          'features_cpi':'CPI',
          'features_unemployment':'Unemployment',
          'features_markdown1':'MarkDown1',
          'features_markdown2':'MarkDown2',
          'features_markdown3':'MarkDown3',
          'features_markdown4':'MarkDown4',
          'features_markdown5':'MarkDown5',
          'store_size':'Store_Size',
          'dept':'Dept'
        }
        sub.rename(columns=rename, inplace=True)

        # 2) drop exact duplicate columns (Glue join artifacts)
        sub = sub.loc[:, ~sub.columns.duplicated()]

        # 3) derive temporal from Date
        sub = derive_temporal_features(sub, 'Date')

        # 4) map store_type to numeric 'Type' like training
        sub['Type'] = sub['store_type'].map(STORE_TYPE_MAP)

        # 5) assemble exactly the 20 features in correct order:
        feature_cols = [
            'Store','Dept','Type','IsHoliday','Temperature','Fuel_Price','CPI','Unemployment',
            'MarkDown1','MarkDown2','MarkDown3','MarkDown4','MarkDown5',
            'Year','Month','Week','Day','Quarter','IsMonthStart','IsMonthEnd'
        ]

        # 6) ensure numeric dtype, fillna
        for c in feature_cols:
            if c not in sub.columns:
                raise KeyError(f"Required feature missing: {c}")
            sub[c] = pd.to_numeric(sub[c], errors='coerce').fillna(0)

        # 7) predict
        sub['predicted_sales'] = model.predict(sub[feature_cols])

        # 8) collect outputs
        all_preds.append(sub[['Store','Dept','Date','store_type','predicted_sales']])

    return pd.concat(all_preds, ignore_index=True)

# 4. Save output to S3
def save_to_s3(df, s3_bucket, s3_key):
    print("Saving predictions to S3...")
    table = pa.Table.from_pandas(df)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression='snappy')
    buffer.seek(0)

    s3 = boto3.client('s3')
    s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=buffer.getvalue())
    print(f"Saved to s3://{s3_bucket}/{s3_key}")

# 5. Main function
def main():
    s3_bucket = "supplychain-genai-optim-jinen"
    input_prefix = "model-ready/test_with_store_features/"
    output_key = "model-ready/test_predictions.parquet"

    test_df = load_test_features(s3_bucket, input_prefix)
    prediction_df = predict_groupwise(test_df)
    save_to_s3(prediction_df, s3_bucket, output_key)

    return prediction_df

# 6. Entry point
if __name__ == "__main__":
    df = main()
    print("Sample predictions:")
    print(df.head())