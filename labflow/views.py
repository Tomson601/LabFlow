from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from labflow.models import Uzytkownik, Laboratorium, Sprzet, Rezerwacja, Serwis

# Pomocnicza funkcja do pobierania zalogowanego użytkownika
def get_logged_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return Uzytkownik.objects.get(id=user_id)
        except Uzytkownik.DoesNotExist:
            return None
    return None


@csrf_protect
def admin_login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = Uzytkownik.objects.get(email=email, rola='admin')
            if user.haslo == password:
                request.session['user_id'] = user.id
                return redirect('/admin-panel/')
            else:
                error = 'Nieprawidłowe hasło.'
        except Uzytkownik.DoesNotExist:
            error = 'Nie znaleziono użytkownika.'
    return render(request, 'admin_login.html', {'error': error})

def admin_panel_view(request):
    user = get_logged_user(request)
    if not user or user.rola != 'admin':
        return redirect('/admin-login/')
    # Dodaj logikę panelu admina
    return render(request, 'admin_panel.html', {'user': user})



@csrf_protect
def login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = Uzytkownik.objects.get(email=email)
            if user.haslo == password:
                request.session['user_id'] = user.id
                return redirect('/panel/')
            else:
                error = 'Nieprawidłowe hasło.'
        except Uzytkownik.DoesNotExist:
            error = 'Nie znaleziono użytkownika.'
    return render(request, 'login.html', {'error': error})


@csrf_protect
def register_view(request):
    error = None
    if request.method == 'POST':
        imie = request.POST.get('imie')
        nazwisko = request.POST.get('nazwisko')
        email = request.POST.get('email')
        rola = request.POST.get('rola', 'student')
        haslo = request.POST.get('password')
        if Uzytkownik.objects.filter(email=email).exists():
            error = 'Użytkownik o tym emailu już istnieje.'
        else:
            user = Uzytkownik.objects.create(imie=imie, nazwisko=nazwisko, email=email, rola=rola, haslo=haslo)
            request.session['user_id'] = user.id
            return redirect('/panel/')
    return render(request, 'register.html', {'error': error})


def panel_view(request):
    user = get_logged_user(request)
    if not user:
        return redirect('/')
    return render(request, 'panel.html', {'user': user})


def logout_view(request):
    request.session.flush()
    return redirect('/')
