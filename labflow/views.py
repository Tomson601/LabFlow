
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View

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

class SerwisViewSet(viewsets.ModelViewSet):
    queryset = Serwis.objects.all()
    serializer_class = SerwisSerializer
    permission_classes = [permissions.IsAuthenticated]
