from django.db import connection

from .models import Uzytkownik


def fetch_user_by_id(user_id):
    if not user_id:
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE id=%s",
                [user_id],
            )
            row = cursor.fetchone()
    except Exception:
        return None

    if not row:
        return None

    return Uzytkownik(
        id=row[0],
        imie=row[1],
        nazwisko=row[2],
        email=row[3],
        rola=row[4],
        haslo=row[5],
    )
