from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.deck.views.deck_viewset import DeckViewSet

router = DefaultRouter()
router.register("", DeckViewSet, basename="deck")

urlpatterns = [
    path("", include(router.urls)),
]
