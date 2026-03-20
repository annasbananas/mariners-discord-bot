import boto3
import logging

from botocore.exceptions import NoCredentialsError, ClientError

logger = logging.getLogger(__name__)


def get_s3_object(bucket_name, object_key):
    """
    Downloads an S3 object to a local file.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key (path) of the object in the bucket.
    """
    s3 = boto3.client("s3")
    try:
        s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
        if s3_object:
            logger.info(
                "Successfully downloaded %s from bucket %s",
                object_key,
                bucket_name,
            )
            return s3_object
        else:
            logger.info("Could not find status...")
            return {}
    except NoCredentialsError:
        logger.error(
            "Error: AWS credentials not found. Please configure your AWS CLI or environment variables."
        )
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logger.info(
                "The object %s was not found in bucket %s.", object_key, bucket_name
            )
        else:
            logger.exception("Unexpected S3 error while reading object: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error while reading S3 object: %s", e)
        return None


def put_s3_object(bucket_name, object_key, data):
    """
    Uploads a local file to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key (path) to store the object as in the bucket.
    """
    s3 = boto3.client("s3")
    try:
        s3.put_object(Bucket=bucket_name, Key=object_key, Body=data)
        logger.info(
            "Successfully uploaded data to bucket %s as %s",
            bucket_name,
            object_key,
        )
    except NoCredentialsError:
        logger.error(
            "Error: AWS credentials not found. Please configure your AWS CLI or environment variables."
        )
        return None
    except ClientError as e:
        logger.exception("Unexpected S3 error while writing object: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error while writing S3 object: %s", e)
        return None
