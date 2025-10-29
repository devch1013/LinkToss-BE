import uuid
from typing import Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from api.user.models.user import User
from common.utils.s3_utils import S3KeyPrefix, S3UploadUtil


class UserProfileService:
    @classmethod
    def get_user_profile(cls, user: User) -> User:
        """사용자 프로필 조회"""
        return user

    @classmethod
    @transaction.atomic
    def update_user_profile(
        cls,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        profile_image: Optional[UploadedFile] = None,
    ) -> User:
        """사용자 프로필 수정"""
        if username is not None:
            user.username = username

        if email is not None:
            user.email = email

        if phone_number is not None:
            user.phone_number = phone_number

        # 프로필 이미지 업로드
        if profile_image is not None:
            profile_image_url = cls._upload_profile_image(user, profile_image)
            user.profile_image = profile_image_url

        user.save()
        return user

    # Internal helper methods

    @classmethod
    def _upload_profile_image(cls, user: User, image_file: UploadedFile) -> str:
        """프로필 이미지를 S3에 업로드하고 URL 반환"""
        file_id = uuid.uuid4()
        file_name = f"profile_{user.id}_{file_id}.{cls._get_file_extension(image_file.name)}"

        try:
            _, image_url = S3UploadUtil.upload(
                file_id=file_id,
                file=image_file,
                prefix=S3KeyPrefix.PROFILE,
                file_name=file_name,
            )
            return image_url
        except Exception as e:
            raise ValueError(f"Failed to upload profile image: {str(e)}")

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """파일 확장자 추출"""
        if "." in filename:
            return filename.rsplit(".", 1)[1].lower()
        return "jpg"  # 기본값
