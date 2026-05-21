from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import Laboratorium, Rezerwacja, Serwis, Sprzet, Uzytkownik
from .serializers import (
    LaboratoriumSerializer,
    RezerwacjaSerializer,
    SerwisSerializer,
    SprzetSerializer,
    UzytkownikSerializer,
)


def get_session_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return Uzytkownik.objects.get(id=user_id)
    except Uzytkownik.DoesNotExist:
        return None


class SessionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return get_session_user(request) is not None


class StaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = get_session_user(request)
        return bool(user and user.rola in {'admin', 'pracownik'})


class LaboratoriumViewSet(viewsets.ModelViewSet):
    queryset = Laboratorium.objects.all().order_by('id')
    serializer_class = LaboratoriumSerializer
    permission_classes = [StaffPermission]


class UzytkownikViewSet(viewsets.ModelViewSet):
    queryset = Uzytkownik.objects.all().order_by('id')
    serializer_class = UzytkownikSerializer
    permission_classes = [SessionPermission]


class SprzetViewSet(viewsets.ModelViewSet):
    queryset = Sprzet.objects.select_related('laboratorium').all().order_by('id')
    serializer_class = SprzetSerializer
    permission_classes = [StaffPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        laboratorium_id = self.request.query_params.get('laboratorium')
        if laboratorium_id:
            queryset = queryset.filter(laboratorium_id=laboratorium_id)
        return queryset


class RezerwacjaViewSet(viewsets.ModelViewSet):
    queryset = Rezerwacja.objects.select_related('sprzet', 'uzytkownik').all().order_by('id')
    serializer_class = RezerwacjaSerializer
    permission_classes = [SessionPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = get_session_user(self.request)
        if user and user.rola == 'admin':
            return queryset
        if user:
            return queryset.filter(uzytkownik=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = get_session_user(self.request)
        serializer.save(uzytkownik=user)

    def create(self, request, *args, **kwargs):
        data_rozpoczecia = request.data.get('data_rozpoczecia')
        data_zakonczenia = request.data.get('data_zakonczenia')
        sprzet_id = request.data.get('sprzet')

        if not (data_rozpoczecia and data_zakonczenia and sprzet_id):
            return Response({'error': 'Brak wymaganych danych.'}, status=400)

        konflikt = Rezerwacja.objects.filter(
            sprzet_id=sprzet_id,
            data_rozpoczecia__lt=data_zakonczenia,
            data_zakonczenia__gt=data_rozpoczecia,
        ).exists()
        if konflikt:
            return Response({'error': 'Istnieje już rezerwacja na ten sprzęt w podanym czasie.'}, status=400)

        return super().create(request, *args, **kwargs)


class SerwisViewSet(viewsets.ModelViewSet):
    queryset = Serwis.objects.select_related('sprzet').all().order_by('id')
    serializer_class = SerwisSerializer
    permission_classes = [StaffPermission]
