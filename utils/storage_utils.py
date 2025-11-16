import boto3
import mimetypes
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from utils.s3_helper import cloudfront_url

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

def s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )

def upload_file_with_metadata(file_path, key=None, extra_args=None, callback=None):
    """
    Uploads file to S3 and ALWAYS returns CloudFront URL.
    Ensures correct ContentType + inline preview for PDF.
    """
    client = s3_client()
    
    if key is None:
        key = os.path.basename(file_path)

    # Guess MIME type
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    extra = extra_args or {}
    extra.setdefault("ContentType", content_type)
    extra.setdefault("ContentDisposition", "inline")

    try:
        with open(file_path, "rb") as f:
            client.upload_fileobj(f, S3_BUCKET, key, ExtraArgs=extra, Callback=callback)

        # DEBUG PRINTS TO VERIFY
        print("DEBUG CLOUDFRONT =>", os.getenv("CLOUDFRONT_DOMAIN"))
        print("DEBUG RETURNING URL =>", cloudfront_url(key))

        # Always return CloudFront URL
        return cloudfront_url(key)

    except ClientError as e:
        raise Exception(f"S3 Upload Failed: {e}")
def delete_file(key: str):
    """Delete a file from S3 by key (filename)."""
    client = s3_client()
    client.delete_object(Bucket=S3_BUCKET, Key=key)


def rename_file(old_key: str, new_key: str):
    """
    Rename a file in S3 by copying to new key and deleting old one.
    """
    client = s3_client()
    client.copy_object(
        Bucket=S3_BUCKET,
        CopySource={"Bucket": S3_BUCKET, "Key": old_key},
        Key=new_key
    )
    client.delete_object(Bucket=S3_BUCKET, Key=old_key)
