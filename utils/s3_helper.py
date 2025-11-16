import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

BUCKET = os.getenv("S3_BUCKET")
CLOUDFRONT = os.getenv("CLOUDFRONT_DOMAIN")

def cloudfront_url(key):
    return f"https://{CLOUDFRONT}/{key}"
