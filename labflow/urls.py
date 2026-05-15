from django.urls import path, include
from labflow.views import login_view, panel_view, logout_view, register_view, admin_login_view, admin_panel_view
from labflow import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('panel/', panel_view, name='panel'),
    path('logout/', logout_view, name='logout'),
    path('admin-login/', admin_login_view, name='admin-login'),
    path('admin-panel/', admin_panel_view, name='admin-panel'),
    path('api/', include('labflow.api_urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
