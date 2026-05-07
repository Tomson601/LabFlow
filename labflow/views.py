from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from labflow.models import Uzytkownik

# ...existing imports and viewsets...


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
from rest_framework import viewsets, permissions
from .models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis
from .serializers import (
    LaboratoriumSerializer, UzytkownikSerializer, SprzetSerializer,
    RezerwacjaSerializer, SerwisSerializer
)

class LaboratoriumViewSet(viewsets.ModelViewSet):
    queryset = Laboratorium.objects.all()
    serializer_class = LaboratoriumSerializer
    permission_classes = [permissions.IsAuthenticated]

class UzytkownikViewSet(viewsets.ModelViewSet):
    queryset = Uzytkownik.objects.all()
    serializer_class = UzytkownikSerializer
    permission_classes = [permissions.IsAuthenticated]

class SprzetViewSet(viewsets.ModelViewSet):
    queryset = Sprzet.objects.all()
    serializer_class = SprzetSerializer
    permission_classes = [permissions.IsAuthenticated]


class RezerwacjaViewSet(viewsets.ModelViewSet):
    queryset = Rezerwacja.objects.all()
    serializer_class = RezerwacjaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uzytkownik=self.request.user)

class SerwisViewSet(viewsets.ModelViewSet):
    queryset = Serwis.objects.all()
    serializer_class = SerwisSerializer
    permission_classes = [permissions.IsAuthenticated]
