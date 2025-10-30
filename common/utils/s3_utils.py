import uuid
from enum import Enum

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from config.settings.third_party.aws_settings import AWSConfig


class S3KeyPrefix(Enum):
    EXAMPLE = "example"
    PROFILE = "profile"
    DROP_FAVICON = "drop/favicon"
    DROP_SCREENSHOT = "drop/screenshot"
    DROP_META_IMAGE = "drop/meta_image"


class S3UploadUtil:
    @classmethod
    def upload(
        cls,
        file_id: uuid.UUID,
        file: UploadedFile,
        prefix: S3KeyPrefix,
        file_name: str,
    ) -> tuple[str, str]:
        file_name = file_name.replace(" ", "_")
        s3_bucket_name = AWSConfig.get_bucket_name()
        s3_key = f"{prefix.value}/{file_id}/{file_name}"
        # Upload to S3
        cls.upload_to_s3(file, s3_bucket_name, s3_key)

        return s3_key, f"{AWSConfig.get_custom_domain()}/{s3_key}"

    @staticmethod
    def check_file_exists(s3_key):
        """
        S3에 파일이 존재하는지 확인합니다.

        Args:
            s3_key: 확인할 파일의 S3 key
            is_private: 프라이빗 버킷 여부 (기본값: True)

        Returns:
            bool: 파일 존재 여부
        """
        s3_bucket_name = AWSConfig.get_bucket_name()

        if settings.ENV == "local":
            session = boto3.Session(profile_name="essentory")
        else:
            session = boto3.Session()

        s3_client = session.client("s3")

        try:
            # head_object는 객체가 존재하면 객체의 메타데이터를 반환하고
            # 존재하지 않으면 예외를 발생시킵니다
            s3_client.head_object(Bucket=s3_bucket_name, Key=s3_key)
            return f"{AWSConfig.get_custom_domain()}/{s3_key}"
        except ClientError as e:
            # 404 에러는 객체가 존재하지 않음을 의미합니다
            if e.response["Error"]["Code"] == "404":
                return None
            # 기타 다른 에러는 다시 발생시킵니다
            raise

    @staticmethod
    def extract_s3_key(s3_url):
        """
        S3 URL에서 S3 키를 추출합니다.
        """
        if "https://" in s3_url:
            domain_end = s3_url.find("/", 8)  # https:// 다음의 첫 번째 '/' 위치 찾기
            if domain_end != -1:
                s3_url = s3_url[domain_end + 1 :]
            else:
                s3_url = s3_url.split("https://")[1]

        return s3_url

    @staticmethod
    def upload_to_s3(file_obj, bucket_name, s3_key):
        """
        파일을 S3에 업로드합니다.

        Args:
            file_obj: 업로드할 파일 객체
            bucket_name: S3 버킷 이름
            s3_key: S3에 저장될 파일 경로/이름 (또는 딕셔너리인 경우 기본 경로)
        Returns:
            str 또는 dict: 업로드된 파일의 URL 또는 URLs 딕셔너리
        """

        session = boto3.Session()

        s3_client = session.client("s3")

        try:
            # Reset file pointer and read file content
            file_obj.seek(0)
            file_content = file_obj.read()

            # Use put_object instead of upload_fileobj
            content_type = getattr(file_obj, "content_type", "application/octet-stream")
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
            )
            return s3_key
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    @classmethod
    def upload_bytes(
        cls,
        file_id: uuid.UUID,
        file_data: bytes,
        prefix: S3KeyPrefix,
        file_name: str,
        content_type: str = "application/octet-stream",
    ) -> tuple[str, str]:
        """
        바이트 데이터를 S3에 업로드합니다.

        Args:
            file_data: 업로드할 파일 데이터 (bytes)
            prefix: S3 키 프리픽스
            file_name: 파일명
            content_type: Content-Type (기본값: application/octet-stream)

        Returns:
            tuple[str, str]: (s3_key, s3_url)
        """

        file_name = file_name.replace(" ", "_")
        s3_bucket_name = AWSConfig.get_bucket_name()
        s3_key = f"{prefix.value}/{file_id}/{file_name}"

        # S3에 직접 업로드
        session = boto3.Session()
        s3_client = session.client("s3")

        try:
            s3_client.put_object(
                Bucket=s3_bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
            )
            return s3_key, f"{AWSConfig.get_custom_domain()}/{s3_key}"
        except Exception as e:
            print(f"Error uploading bytes to S3: {str(e)}")
            import traceback

            traceback.print_exc()
            return None, None
