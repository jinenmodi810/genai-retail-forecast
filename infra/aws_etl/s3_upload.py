# infra/aws_etl/s3_upload.py

import boto3
import os
from config import S3_BUCKET_NAME, S3_RAW_PREFIX, LOCAL_RAW_PATH

s3 = boto3.client('s3')

def upload_raw_files():
    for filename in os.listdir(LOCAL_RAW_PATH):
        local_path = os.path.join(LOCAL_RAW_PATH, filename)
        if os.path.isfile(local_path):
            s3_key = f"{S3_RAW_PREFIX}{filename}"
            print(f"Uploading {filename} to s3://{S3_BUCKET_NAME}/{s3_key}")
            s3.upload_file(local_path, S3_BUCKET_NAME, s3_key)

    print("All files uploaded to S3.")

if __name__ == "__main__":
    upload_raw_files()