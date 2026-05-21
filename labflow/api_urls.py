from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import LaboratoriumViewSet, RezerwacjaViewSet, SerwisViewSet, SprzetViewSet, UzytkownikViewSet

router = DefaultRouter()
router.register(r'laboratoria', LaboratoriumViewSet, basename='laboratoria')
router.register(r'uzytkownicy', UzytkownikViewSet, basename='uzytkownicy')
router.register(r'sprzet', SprzetViewSet, basename='sprzet')
router.register(r'rezerwacje', RezerwacjaViewSet, basename='rezerwacje')
router.register(r'serwis', SerwisViewSet, basename='serwis')

urlpatterns = [
	path('', include(router.urls)),
]
