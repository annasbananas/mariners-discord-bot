import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def get_s3_object(bucket_name, object_key, local_filename):
    """
    Downloads an S3 object to a local file.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key (path) of the object in the bucket.
        local_filename (str): The name of the local file to save the object to.
    """
    s3 = boto3.client('s3')
    try:
        s3.download_file(bucket_name, object_key, local_filename)
        print(f"Successfully downloaded {object_key} from bucket {bucket_name} to {local_filename}")
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS CLI or environment variables.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Error: The object {object_key} was not found in bucket {bucket_name}.")
        else:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def put_s3_object(bucket_name, local_filename, object_key):
    """
    Uploads a local file to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        local_filename (str): The path to the local file to upload.
        object_key (str): The key (path) to store the object as in the bucket.
    """
    s3 = boto3.client('s3')
    try:
        s3.upload_file(local_filename, bucket_name, object_key)
        print(f"Successfully uploaded {local_filename} to bucket {bucket_name} as {object_key}")
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS CLI or environment variables.")
    except ClientError as e:
        print(f"An unexpected error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: The local file {local_filename} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")