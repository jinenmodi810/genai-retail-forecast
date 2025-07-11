import boto3

s3 = boto3.client("s3")
with open("model.tar.gz", "rb") as f:
    s3.upload_fileobj(f, "supplychain-genai-optim-jinen", "time_llm_sagemaker/model.tar.gz")

print("✅ model.tar.gz uploaded to S3")