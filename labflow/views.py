from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from labflow.db_helpers import fetch_user_by_id
from django.db import connection


def get_logged_user(request):
    return fetch_user_by_id(request.session.get('user_id'))


@csrf_protect
def admin_login_view(request):
    return redirect('/')

def admin_panel_view(request):
    user = get_logged_user(request)
    if not user:
        return redirect('/')
    return redirect('/panel/')



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
        rola = 'student'
        haslo = request.POST.get('password')
        haslo_confirm = request.POST.get('password_confirm')
        
        if haslo != haslo_confirm:
            error = 'Hasła nie są takie same.'
        else:
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
                    cursor.execute("SELECT id FROM labflow_uzytkownik WHERE email=%s", [email])
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
