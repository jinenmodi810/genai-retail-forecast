import boto3
import pandas as pd
from io import BytesIO

# 1. S3 location of your predictions parquet
BUCKET = "supplychain-genai-optim-jinen"
KEY    = "model-ready/test_predictions.parquet"

# 2. Download and read the Parquet
s3 = boto3.client("s3")
obj = s3.get_object(Bucket=BUCKET, Key=KEY)
df = pd.read_parquet(BytesIO(obj["Body"].read()))

# 3. Inspect schema and sample data
print("Columns in Parquet file:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head().to_string(index=False))

# 4. Null‐check for predicted_sales
nulls = df["predicted_sales"].isna().sum()
print(f"\nNull count in 'predicted_sales': {nulls}")