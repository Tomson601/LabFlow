from django.contrib import admin
from django.urls import path, include
from labflow.views import login_view, panel_view, logout_view
from rest_framework import routers
from labflow import views
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'laboratoria', views.LaboratoriumViewSet)
router.register(r'uzytkownicy', views.UzytkownikViewSet)
router.register(r'sprzet', views.SprzetViewSet)
router.register(r'rezerwacje', views.RezerwacjaViewSet)
router.register(r'serwis', views.SerwisViewSet)

urlpatterns = [
    path('', login_view, name='login'),
    path('panel/', panel_view, name='panel'),
    path('logout/', logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('labflow.api_urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
