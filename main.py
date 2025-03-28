import boto3
import argparse
import logging
import os
import magic
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize S3 client
def init_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_REGION")
    )


def list_buckets():
    """List all S3 buckets"""
    s3 = init_client()
    response = s3.list_buckets()
    for bucket in response.get("Buckets", []):
        logging.info(f"{bucket['Name']}")

def create_bucket(bucket_name):
    """Create an S3 bucket"""
    s3 = init_client()
    region = os.getenv("AWS_REGION")

    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )

    logging.info(f"Bucket {bucket_name} created successfully in region {region}.")

def empty_bucket(bucket_name):
    """Empty the S3 bucket before deleting it"""
    s3 = init_client()
    try:
        # List all objects in the bucket
        objects = s3.list_objects_v2(Bucket=bucket_name)
        
        # If the bucket is not empty
        if 'Contents' in objects:
            # Delete all objects in the bucket
            delete_objects = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
            s3.delete_objects(Bucket=bucket_name, Delete=delete_objects)
            logging.info(f"All objects in bucket {bucket_name} have been deleted.")
        else:
            logging.info(f"Bucket {bucket_name} is already empty.")
    except Exception as e:
        logging.error(f"Error emptying bucket {bucket_name}: {e}")

def delete_bucket(bucket_name):
    """Delete an S3 bucket after emptying it"""
    s3 = init_client()
    try:
        # Empty the bucket first
        empty_bucket(bucket_name)
        
        # Now delete the bucket
        s3.delete_bucket(Bucket=bucket_name)
        logging.info(f"Bucket {bucket_name} deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting bucket: {e}")

def bucket_exists(bucket_name):
    """Check if an S3 bucket exists"""
    s3 = init_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
        logging.info("Bucket exists.")
    except Exception:
        logging.info("Bucket does not exist.")

def download_file_and_upload_to_s3(file_path, bucket_name, object_name):
    """Upload an allowed file type to S3 and set public read access"""
    allowed_mime_types = {"image/bmp", "image/jpeg", "image/png", "image/webp", "video/mp4"}
    
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_file(file_path)
    
    if file_mime_type not in allowed_mime_types:
        logging.error("Invalid file type. Allowed types: .bmp, .jpg, .jpeg, .png, .webp, .mp4")
        return
    
    s3 = init_client()
    s3.upload_file(file_path, bucket_name, object_name)
    logging.info(f"File {file_path} uploaded to {bucket_name}/{object_name}.")


def delete_public_access_block(bucket_name):
    """Fix permission issues by deleting the public access block"""
    s3 = init_client()
    try:
        s3.delete_public_access_block(Bucket=bucket_name)
        logging.info(f"Public access block removed from {bucket_name}.")
    except Exception as e:
        logging.error(f"Error removing public access block: {e}")

def main():
    parser = argparse.ArgumentParser(description="S3 CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list_buckets", help="List all S3 buckets")
    
    parser_create = subparsers.add_parser("create_bucket", help="Create an S3 bucket")
    parser_create.add_argument("bucket_name", type=str, help="Bucket name")
    
    parser_delete = subparsers.add_parser("delete_bucket", help="Delete an S3 bucket")
    parser_delete.add_argument("bucket_name", type=str, help="Bucket name")
    
    parser_exists = subparsers.add_parser("bucket_exists", help="Check if an S3 bucket exists")
    parser_exists.add_argument("bucket_name", type=str, help="Bucket name")
    
    parser_upload = subparsers.add_parser("upload_file", help="Upload a file to S3")
    parser_upload.add_argument("file_path", type=str, help="Local file path")
    parser_upload.add_argument("bucket_name", type=str, help="Bucket name")
    parser_upload.add_argument("object_name", type=str, help="Object name in S3")
    
    parser_delete_access = subparsers.add_parser("delete_public_access_block", help="Delete public access block")
    parser_delete_access.add_argument("bucket_name", type=str, help="Bucket name")
    
    args = parser.parse_args()
    
    if args.command == "list_buckets":
        list_buckets()
    elif args.command == "create_bucket":
        create_bucket(args.bucket_name)
    elif args.command == "delete_bucket":
        delete_bucket(args.bucket_name)
    elif args.command == "bucket_exists":
        bucket_exists(args.bucket_name)
    elif args.command == "upload_file":
        download_file_and_upload_to_s3(args.file_path, args.bucket_name, args.object_name)
    elif args.command == "delete_public_access_block":
        delete_public_access_block(args.bucket_name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
