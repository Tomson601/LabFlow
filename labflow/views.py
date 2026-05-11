from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from labflow.models import Uzytkownik
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis
from .serializers import (
    LaboratoriumSerializer, UzytkownikSerializer, SprzetSerializer,
    RezerwacjaSerializer, SerwisSerializer
)

@csrf_protect
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/admin-panel/')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('/admin-panel/')
        else:
            error = 'Nieprawidłowy login, hasło lub brak uprawnień administratora.'
    return render(request, 'admin_login.html', {'error': error})

@user_passes_test(lambda u: u.is_superuser, login_url='/admin-login/')
def admin_panel_view(request):
    # Obsługa zmiany roli użytkownika
    if request.method == 'POST' and 'user_id' in request.POST and 'rola' in request.POST:
        user_id = request.POST.get('user_id')
        rola = request.POST.get('rola')
        user = Uzytkownik.objects.filter(id=user_id).first()
        if user and rola in ['student', 'pracownik', 'admin']:
            user.rola = rola
            user.is_staff = (rola == 'admin')
            user.save()

    # Obsługa potwierdzania rezerwacji
    if request.method == 'POST' and 'confirm_reservation_id' in request.POST:
        res_id = request.POST.get('confirm_reservation_id')
        rezerwacja = Rezerwacja.objects.filter(id=res_id).first()
        if rezerwacja and rezerwacja.status == 'oczekująca':
            rezerwacja.status = 'aktywna'
            rezerwacja.save()

    users = Uzytkownik.objects.all()
    labs = Laboratorium.objects.all()
    devices = Sprzet.objects.select_related('laboratorium').all()
    reservations = Rezerwacja.objects.select_related('sprzet', 'uzytkownik').all()
    services = Serwis.objects.select_related('sprzet').all()
    return render(request, 'admin_panel.html', {
        'users': users,
        'labs': labs,
        'devices': devices,
        'reservations': reservations,
        'services': services,
    })


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/panel/')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/panel/')
        else:
            return render(request, 'login.html', {'form': {'errors': True}})
    return render(request, 'login.html', {'form': {}})

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('/panel/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        imie = request.POST.get('imie')
        nazwisko = request.POST.get('nazwisko')
        
        errors = []
        
        if password != password_confirm:
            errors.append('Hasła się nie zgadzają.')
        
        if Uzytkownik.objects.filter(email=email).exists():
            errors.append('Email już jest zarejestrowany.')
        
        if Uzytkownik.objects.filter(username=username).exists():
            errors.append('Nazwa użytkownika już istnieje.')
        
        if len(password) < 6:
            errors.append('Hasło musi mieć co najmniej 6 znaków.')
        
        if errors:
            return render(request, 'register.html', {'errors': errors})
        
        user = Uzytkownik.objects.create_user(
            username=username,
            email=email,
            password=password,
            imie=imie,
            nazwisko=nazwisko,
            rola='uzytkownik'
        )
        
        login(request, user)
        return redirect('/panel/')
    
    return render(request, 'register.html', {})

@login_required(login_url='/')
def panel_view(request):
    return render(request, 'panel.html')

def logout_view(request):
    logout(request)
    return redirect('/')



class IsAdminOrPracownik(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.rola in ['admin', 'pracownik'] or request.user.is_superuser)

class LaboratoriumViewSet(viewsets.ModelViewSet):
    queryset = Laboratorium.objects.all()
    serializer_class = LaboratoriumSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrPracownik()]
        return [permissions.IsAuthenticated()]

class UzytkownikViewSet(viewsets.ModelViewSet):
    queryset = Uzytkownik.objects.all()
    serializer_class = UzytkownikSerializer
    permission_classes = [permissions.IsAuthenticated]



class SprzetViewSet(viewsets.ModelViewSet):
    queryset = Sprzet.objects.all()
    serializer_class = SprzetSerializer
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrPracownik()]
        return [permissions.IsAuthenticated()]


class RezerwacjaViewSet(viewsets.ModelViewSet):
    # Pozwól użytkownikowi anulować (usunąć) tylko swoją rezerwację
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.uzytkownik != request.user and not request.user.is_superuser:
            return Response({'error': 'Możesz anulować tylko swoją rezerwację.'}, status=403)
        return super().destroy(request, *args, **kwargs)

    queryset = Rezerwacja.objects.all()
    serializer_class = RezerwacjaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Rezerwacja.objects.all()
        return Rezerwacja.objects.filter(uzytkownik=user)

    def create(self, request, *args, **kwargs):
        data_rozpoczecia = request.data.get('data_rozpoczecia')
        data_zakonczenia = request.data.get('data_zakonczenia')
        sprzet_id = request.data.get('sprzet')

        # Sprawdź czy są wymagane dane
        if not (data_rozpoczecia and data_zakonczenia and sprzet_id):
            return Response({'error': 'Brak wymaganych danych.'}, status=400)

        konflikt = Rezerwacja.objects.filter(
            sprzet_id=sprzet_id,
            data_rozpoczecia__lt=data_zakonczenia,
            data_zakonczenia__gt=data_rozpoczecia
        ).exists()
        if konflikt:
            return Response({'error': 'Istnieje już rezerwacja na ten sprzęt w podanym czasie.'}, status=400)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        rezerwacja = serializer.save(uzytkownik=self.request.user)
        # Po utworzeniu rezerwacji ustaw status sprzętu na 'zarezerwowany'
        sprzet = rezerwacja.sprzet
        sprzet.status = 'zarezerwowany'
        sprzet.save()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Po zakończeniu rezerwacji ustaw sprzęt na 'dostępny' jeśli nie ma innych aktywnych rezerwacji
        instance = self.get_object()
        if instance.status == 'zakończona':
            sprzet = instance.sprzet
            # Sprawdź czy są inne aktywne rezerwacje na ten sprzęt
            aktywne = Rezerwacja.objects.filter(sprzet=sprzet, status='aktywna').exclude(id=instance.id).exists()
            if not aktywne:
                sprzet.status = 'dostępny'
                sprzet.save()
        return response

class SerwisViewSet(viewsets.ModelViewSet):
    queryset = Serwis.objects.all()
    serializer_class = SerwisSerializer
    permission_classes = [permissions.IsAuthenticated]
