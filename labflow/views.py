from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from labflow.models import Uzytkownik, Laboratorium, Sprzet, Rezerwacja, Serwis
from django.db import connection

# Pomocnicza funkcja do pobierania zalogowanego użytkownika
def get_logged_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            # SQL QUERY - SELECT użytkownika po ID
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE id=%s", [user_id])
                row = cursor.fetchone()
                if row:
                    user = Uzytkownik(id=row[0], imie=row[1], nazwisko=row[2], email=row[3], rola=row[4], haslo=row[5])
                    return user
            return None
        except Exception:
            return None
    return None


@csrf_protect
def admin_login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        try:
            # SQL QUERY - SELECT admina po emailu i roli
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE email=%s AND rola=%s",
                    [email, 'admin']
                )
                row = cursor.fetchone()
                if row:
                    if row[5] == password:  # porównanie hasła
                        request.session['user_id'] = row[0]
                        return redirect('/admin-panel/')
                    else:
                        error = 'Nieprawidłowe hasło.'
                else:
                    error = 'Nie znaleziono użytkownika.'
        except Exception as e:
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
            # SQL QUERY - SELECT użytkownika po emailu
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE email=%s",
                    [email]
                )
                row = cursor.fetchone()
                if row:
                    if row[5] == password:  # porównanie hasła
                        request.session['user_id'] = row[0]
                        return redirect('/panel/')
                    else:
                        error = 'Nieprawidłowe hasło.'
                else:
                    error = 'Nie znaleziono użytkownika.'
        except Exception as e:
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
        
        # SQL QUERY - CHECK czy email już istnieje
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM labflow_uzytkownik WHERE email=%s", [email])
            if cursor.fetchone():
                error = 'Użytkownik o tym emailu już istnieje.'
            else:
                # SQL QUERY - INSERT nowy użytkownik
                cursor.execute(
                    "INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo) VALUES (%s, %s, %s, %s, %s)",
                    [imie, nazwisko, email, rola, haslo]
                )
                # Pobierz ID nowo utworzonego użytkownika
                cursor.execute("SELECT LAST_INSERT_ID()")
                user_id = cursor.fetchone()[0]
                request.session['user_id'] = user_id
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
