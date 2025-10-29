from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.user.views.auth_view import RefreshView, SocialAuthView
from api.user.views.user_profile_viewset import UserProfileViewSet

router = DefaultRouter()
router.register(r"profile", UserProfileViewSet, basename="user-profile")

urlpatterns = [
    path(
        "<str:provider>/login/",
        SocialAuthView.as_view({"post": "create"}),
        name="social-login",
    ),
    path(
        "withdraw/",
        SocialAuthView.as_view({"delete": "withdraw"}),
        name="withdraw",
    ),
    path("refresh/", RefreshView.as_view({"post": "refresh"}), name="token-refresh"),
    path("", include(router.urls)),
]
