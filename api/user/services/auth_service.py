from abc import ABC, abstractmethod

from firebase_admin import auth
from loguru import logger
from rest_framework_simplejwt.tokens import RefreshToken

from api.user.exceptions import OAuthCustomExceptions
from api.user.models import User
from common.exceptions.custom_exceptions import CustomException


class AuthService(ABC):
    @abstractmethod
    def get_or_create_user(self, identifier: str, fcmToken: str, name: str = None):
        pass

    def get_token(self, user: User):
        print(user)
        return RefreshToken.for_user(user)


class FirebaseAuthService(AuthService):
    def get_or_create_user(self, id_token: str, name: str = None):
        return self._create_user(id_token, name)

    def _verify_firebase_token(self, id_token: str):
        """Firebase ID Token 검증"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.InvalidIdTokenError:
            logger.error("Invalid Firebase ID token")
            return None
        except auth.ExpiredIdTokenError:
            logger.error("Expired Firebase ID token")
            return None
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return None

    def _create_user(self, id_token: str, name: str):
        if not id_token:
            raise CustomException(OAuthCustomExceptions.INVALID_TOKEN)

        # Firebase ID Token 검증
        decoded_token = self._verify_firebase_token(id_token)
        if not decoded_token:
            raise CustomException(OAuthCustomExceptions.INVALID_TOKEN)

        # Firebase에서 사용자 정보 추출
        user_id = decoded_token.get("uid")
        email = decoded_token.get("email", "")
        username = decoded_token.get("name", name or "")
        provider = decoded_token.get("firebase", {}).get("sign_in_provider", "firebase")

        # 사용자 생성 또는 조회
        user, is_created = User.objects.get_or_create(
            identifier=user_id,
            defaults={
                "username": username,
                "email": email,
                "provider": provider,
            },
        )

        return user


class NativeAuthService(AuthService):
    def get_or_create_user(self, identifier: str, password: str):
        if not identifier or not password:
            raise CustomException(OAuthCustomExceptions.INVALID_TOKEN)

        user, is_created = User.objects.get_or_create(
            identifier=identifier,
            defaults={
                "password": password,
                "username": identifier,
                "provider": "native",
            },
        )

        return user
