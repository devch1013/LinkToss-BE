from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.drop.views.comment_viewset import CommentViewSet
from api.drop.views.drop_viewset import DropViewSet

router = DefaultRouter()
router.register(r"comments", CommentViewSet, basename="comment")
router.register("", DropViewSet, basename="drop")

urlpatterns = [
    path("", include(router.urls)),
]
