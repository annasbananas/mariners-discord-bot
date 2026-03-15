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
                f"Successfully downloaded {object_key} from bucket {bucket_name}"
            )
            return s3_object
        else:
            logger.info("Could not find status...")
            return {}
    except NoCredentialsError:
        print(
            "Error: AWS credentials not found. Please configure your AWS CLI or environment variables."
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print(
                f"Error: The object {object_key} was not found in bucket {bucket_name}."
            )
        else:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


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
            f"Successfully uploaded data to bucket {bucket_name} as {object_key}"
        )
    except NoCredentialsError:
        print(
            "Error: AWS credentials not found. Please configure your AWS CLI or environment variables."
        )
    except ClientError as e:
        print(f"An unexpected error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: The local file {local_filename} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
