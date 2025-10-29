from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from api.user.exceptions import UserExceptionEnum
from api.user.serializers.user_serializers import (
    MessageResponseSerializer,
    RefreshTokenSerializer,
    SocialLoginQuerySerializer,
    SocialLoginRequestSerializer,
    TokenSerializer,
)
from api.user.services.auth_service import (
    AuthService,
    FirebaseAuthService,
)
from common.exceptions.custom_exceptions import CustomException


class SocialAuthView(
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    """
    소셜 로그인 및 사용자 인증 관련 API 엔드포인트

    Google, Apple 소셜 로그인과 사용자 계정 관리 기능을 제공합니다.
    """

    @swagger_auto_schema(
        operation_summary="소셜 로그인",
        operation_description="""
        소셜 로그인을 통해 사용자 인증을 처리합니다.
        
        지원되는 제공업체:
        - google: Google OAuth 로그인
        - native: 자체 계정 로그인 (개발용)
        
        성공 시 JWT 토큰을 반환합니다.
        """,
        manual_parameters=[
            openapi.Parameter(
                "provider",
                openapi.IN_PATH,
                description="로그인 제공업체 (google, apple, native)",
                type=openapi.TYPE_STRING,
                required=True,
                enum=["google", "apple", "native"],
            ),
        ],
        query_serializer=SocialLoginQuerySerializer,
        request_body=SocialLoginRequestSerializer,
        responses={
            200: TokenSerializer,
            400: "잘못된 요청 데이터 또는 인증 실패",
            500: "내부 서버 오류",
        },
        tags=["인증"],
    )
    def create(self, request, *args, **kwargs):
        provider = kwargs.get("provider")
        service: AuthService = self.get_service(provider)

        # 쿼리 파라미터 검증
        query_serializer = SocialLoginQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query_data = query_serializer.validated_data

        # 요청 바디 검증
        request_serializer = SocialLoginRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_data = request_serializer.validated_data

        if provider == "native":
            identifier = request_data.get("identifier")
            password = request_data.get("password")
            user = service.get_or_create_user(identifier, password)
        else:
            # Firebase 로그인: request body에서 id_token과 fcmToken 가져오기
            id_token = request_data.get("id_token")

            user = service.get_or_create_user(id_token)

        refresh = service.get_token(user)
        return Response(
            TokenSerializer(
                {
                    "user_id": user.id,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "bearer",
                }
            ).data
        )

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_service(self, provider: str):
        """인증 서비스 팩토리 메소드"""
        if provider == "google":
            return FirebaseAuthService()
        else:
            raise ValueError("Invalid provider")

    @swagger_auto_schema(
        operation_summary="사용자 계정 탈퇴",
        operation_description="""
        현재 로그인한 사용자의 계정을 완전히 삭제합니다.
        
        Apple 로그인 사용자의 경우 Apple 서버에서도 토큰을 폐기합니다.
        이 작업은 되돌릴 수 없습니다.
        """,
        responses={
            200: MessageResponseSerializer,
            401: "인증되지 않은 사용자",
            500: "내부 서버 오류",
        },
        tags=["사용자 관리"],
    )
    @action(detail=False, methods=["DELETE"], permission_classes=[IsAuthenticated])
    def withdraw(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK,
        )


class RefreshView(GenericViewSet):
    """
    Refresh 토큰을 사용하여 새로운 Access 토큰을 발급받는 API
    """

    @swagger_auto_schema(
        operation_summary="토큰 갱신",
        operation_description="""
        유효한 Refresh 토큰을 사용하여 새로운 Access 토큰을 발급받습니다.
        
        Refresh 토큰이 만료되지 않은 경우 새로운 Access 토큰과 Refresh 토큰을 반환합니다.
        """,
        request_body=RefreshTokenSerializer,
        responses={
            200: TokenSerializer,
            401: "유효하지 않은 Refresh 토큰",
            400: "잘못된 요청 데이터",
        },
        tags=["인증"],
    )
    def refresh(self, request, *args, **kwargs):
        # 요청 데이터 검증
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data.get("refresh_token")

        if not refresh_token_str:
            raise CustomException(UserExceptionEnum.REFRESH_TOKEN_MISSING)

        try:
            # Refresh 토큰 검증 및 새로운 토큰 생성
            refresh_token = RefreshToken(refresh_token_str)

            # 새로운 Access 토큰 생성
            new_access_token = refresh_token.access_token

            # 사용자 정보 가져오기
            user_id = refresh_token.payload.get("user_id")

            return Response(
                TokenSerializer(
                    {
                        "user_id": user_id,
                        "access_token": str(new_access_token),
                        "refresh_token": str(refresh_token),
                        "token_type": "bearer",
                    }
                ).data,
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            error_detail = str(e)
            logger.error(f"Refresh token error: {error_detail}")

            if "expired" in error_detail.lower():
                raise CustomException(UserExceptionEnum.REFRESH_TOKEN_EXPIRED)
            elif (
                "blacklisted" in error_detail.lower()
                or "not valid" in error_detail.lower()
            ):
                raise CustomException(UserExceptionEnum.REFRESH_TOKEN_BLACKLISTED)
            else:
                raise CustomException(UserExceptionEnum.REFRESH_TOKEN_INVALID)

        except InvalidToken as e:
            error_detail = str(e)
            logger.error(f"Invalid refresh token: {error_detail}")

            if "expired" in error_detail.lower():
                raise CustomException(UserExceptionEnum.REFRESH_TOKEN_EXPIRED)
            else:
                raise CustomException(UserExceptionEnum.REFRESH_TOKEN_INVALID)

        except Exception as e:
            logger.error(f"Unexpected refresh token error: {e}")
            raise CustomException(UserExceptionEnum.REFRESH_TOKEN_INVALID)
