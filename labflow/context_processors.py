from .models import Uzytkownik
from django.db import connection

def current_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            # SQL QUERY - SELECT użytkownika po ID
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE id=%s",
                    [user_id]
                )
                row = cursor.fetchone()
                if row:
                    user = Uzytkownik(id=row[0], imie=row[1], nazwisko=row[2], email=row[3], rola=row[4], haslo=row[5])
                    return {'user': user}
            return {'user': None}
        except Exception:
            return {'user': None}
    return {'user': None}
