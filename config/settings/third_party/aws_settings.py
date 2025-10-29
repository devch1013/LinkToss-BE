import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION_NAME = os.getenv("AWS_REGION")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
FILE_SERVER_URL = os.getenv("FILE_SERVER_URL")
AWS_S3_CUSTOM_DOMAIN = os.getenv("S3_CUSTOM_DOMAIN")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# S3 Settings
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_QUERYSTRING_AUTH = False  # URL에 인증 파라미터 제거


class AWSConfig:
    @staticmethod
    def get_bucket_name():
        return os.getenv("AWS_STORAGE_BUCKET_NAME")

    @staticmethod
    def get_custom_domain():
        return os.getenv("S3_CUSTOM_DOMAIN")

    @staticmethod
    def get_file_server_url():
        return os.getenv("FILE_SERVER_URL")
