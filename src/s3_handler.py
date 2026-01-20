"""S3 integration module (optional)."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def s3_push(
    local_dir: Path,
    s3_prefix: str,
    bucket: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
) -> None:
    """
    Push local directory to S3.
    
    Args:
        local_dir: Local directory path
        s3_prefix: S3 prefix (e.g., "genomics/curated/")
        bucket: S3 bucket (reads from S3_BUCKET env if not provided)
        aws_access_key_id: AWS access key (reads from env if not provided)
        aws_secret_access_key: AWS secret key (reads from env if not provided)
    """
    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        raise
    
    # Get credentials and bucket from environment if not provided
    bucket = bucket or os.getenv("S3_BUCKET")
    if not bucket:
        raise ValueError("S3_BUCKET not set. Set environment variable or pass bucket parameter.")
    
    # Create S3 client
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )
    s3_client = session.client("s3")
    
    # Upload files
    local_dir = Path(local_dir)
    if not local_dir.exists():
        raise FileNotFoundError(f"Local directory not found: {local_dir}")
    
    for file_path in local_dir.glob("**/*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_dir)
            s3_key = f"{s3_prefix.rstrip('/')}/{relative_path}".replace("\\", "/")
            
            logger.info(f"Uploading {file_path} → s3://{bucket}/{s3_key}")
            s3_client.upload_file(str(file_path), bucket, s3_key)
    
    logger.info(f"✓ Uploaded all files to s3://{bucket}/{s3_prefix}")


def s3_pull(
    s3_prefix: str,
    local_dir: Path,
    bucket: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
) -> None:
    """
    Pull from S3 to local directory.
    
    Args:
        s3_prefix: S3 prefix (e.g., "genomics/curated/")
        local_dir: Local directory path
        bucket: S3 bucket (reads from S3_BUCKET env if not provided)
        aws_access_key_id: AWS access key (reads from env if not provided)
        aws_secret_access_key: AWS secret key (reads from env if not provided)
    """
    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        raise
    
    # Get credentials and bucket from environment if not provided
    bucket = bucket or os.getenv("S3_BUCKET")
    if not bucket:
        raise ValueError("S3_BUCKET not set. Set environment variable or pass bucket parameter.")
    
    # Create S3 client
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )
    s3_client = session.client("s3")
    
    # Create local directory
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    
    # List and download objects
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=s3_prefix.rstrip("/"))
    
    for page in pages:
        if "Contents" not in page:
            continue
        
        for obj in page["Contents"]:
            s3_key = obj["Key"]
            
            # Skip prefix itself
            if s3_key == s3_prefix.rstrip("/"):
                continue
            
            # Download file
            relative_path = s3_key[len(s3_prefix):].lstrip("/")
            local_file_path = local_dir / relative_path
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading s3://{bucket}/{s3_key} → {local_file_path}")
            s3_client.download_file(bucket, s3_key, str(local_file_path))
    
    logger.info(f"✓ Downloaded all files to {local_dir}")
