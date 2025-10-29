from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.drop.views.comment_viewset import CommentViewSet
from api.drop.views.drop_viewset import DropViewSet

router = DefaultRouter()
router.register(r"drops", DropViewSet, basename="drop")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
]
