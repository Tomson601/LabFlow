from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import connection

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
        # SQL QUERY - SELECT użytkownika po ID
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE id=%s",
                [user_id]
            )
            row = cursor.fetchone()
            if row:
                user = Uzytkownik(id=row[0], imie=row[1], nazwisko=row[2], email=row[3], rola=row[4], haslo=row[5])
                return user
        return None
    except Exception:
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
    serializer_class = LaboratoriumSerializer
    permission_classes = [StaffPermission]

    def get_queryset(self):
        # SQL QUERY - SELECT wszystkie laboratorium ORDER BY id
        return Laboratorium.objects.raw(
            "SELECT id, nazwa, lokalizacja, opis FROM labflow_laboratorium ORDER BY id"
        )

    def get_object(self):
        # SQL QUERY - SELECT laboratorium po ID
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, nazwa, lokalizacja, opis FROM labflow_laboratorium WHERE id=%s",
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Laboratorium(id=row[0], nazwa=row[1], lokalizacja=row[2], opis=row[3])
                return obj
            raise NotFound("Laboratorium nie znalezione.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT laboratorium
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_laboratorium (nazwa, lokalizacja, opis) VALUES (%s, %s, %s)",
                [serializer.validated_data['nazwa'], serializer.validated_data['lokalizacja'], 
                 serializer.validated_data.get('opis', '')]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE laboratorium
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_laboratorium SET nazwa=%s, lokalizacja=%s, opis=%s WHERE id=%s",
                [serializer.validated_data['nazwa'], serializer.validated_data['lokalizacja'], 
                 serializer.validated_data.get('opis', ''), pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE laboratorium
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_laboratorium WHERE id=%s", [pk])


class UzytkownikViewSet(viewsets.ModelViewSet):
    serializer_class = UzytkownikSerializer
    permission_classes = [SessionPermission]

    def get_queryset(self):
        # SQL QUERY - SELECT wszyscy użytkownicy ORDER BY id
        return Uzytkownik.objects.raw(
            "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik ORDER BY id"
        )

    def get_object(self):
        # SQL QUERY - SELECT użytkownika po ID
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, imie, nazwisko, email, rola, haslo FROM labflow_uzytkownik WHERE id=%s",
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Uzytkownik(id=row[0], imie=row[1], nazwisko=row[2], email=row[3], rola=row[4], haslo=row[5])
                return obj
            raise NotFound("Użytkownik nie znaleziony.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT użytkownika
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo) VALUES (%s, %s, %s, %s, %s)",
                [serializer.validated_data['imie'], serializer.validated_data['nazwisko'],
                 serializer.validated_data['email'], serializer.validated_data['rola'],
                 serializer.validated_data['haslo']]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE użytkownika
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_uzytkownik SET imie=%s, nazwisko=%s, email=%s, rola=%s, haslo=%s WHERE id=%s",
                [serializer.validated_data['imie'], serializer.validated_data['nazwisko'],
                 serializer.validated_data['email'], serializer.validated_data['rola'],
                 serializer.validated_data['haslo'], pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE użytkownika
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_uzytkownik WHERE id=%s", [pk])


class SprzetViewSet(viewsets.ModelViewSet):
    serializer_class = SprzetSerializer
    permission_classes = [StaffPermission]

    def get_queryset(self):
        laboratorium_id = self.request.query_params.get('laboratorium')
        
        if laboratorium_id:
            # SQL QUERY - SELECT sprzęt JOIN laboratorium WHERE laboratorium_id ORDER BY id
            return Sprzet.objects.raw(
                """
                SELECT s.id, s.nazwa, s.kategoria, s.status, s.laboratorium_id
                FROM labflow_sprzet s
                JOIN labflow_laboratorium l ON s.laboratorium_id = l.id
                WHERE s.laboratorium_id = %s
                ORDER BY s.id
                """,
                [laboratorium_id]
            )
        else:
            # SQL QUERY - SELECT wszystkie sprzęt JOIN laboratorium ORDER BY id
            return Sprzet.objects.raw(
                """
                SELECT s.id, s.nazwa, s.kategoria, s.status, s.laboratorium_id
                FROM labflow_sprzet s
                JOIN labflow_laboratorium l ON s.laboratorium_id = l.id
                ORDER BY s.id
                """
            )

    def get_object(self):
        # SQL QUERY - SELECT sprzęt po ID z JOIN laboratorium
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.id, s.nazwa, s.kategoria, s.status, s.laboratorium_id
                FROM labflow_sprzet s
                JOIN labflow_laboratorium l ON s.laboratorium_id = l.id
                WHERE s.id=%s
                """,
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Sprzet(id=row[0], nazwa=row[1], kategoria=row[2], status=row[3], laboratorium_id=row[4])
                return obj
            raise NotFound("Sprzęt nie znaleziony.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT sprzęt
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id) VALUES (%s, %s, %s, %s)",
                [serializer.validated_data['nazwa'], serializer.validated_data['kategoria'],
                 serializer.validated_data['status'], serializer.validated_data['laboratorium'].id]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE sprzęt
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_sprzet SET nazwa=%s, kategoria=%s, status=%s, laboratorium_id=%s WHERE id=%s",
                [serializer.validated_data['nazwa'], serializer.validated_data['kategoria'],
                 serializer.validated_data['status'], serializer.validated_data['laboratorium'].id, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE sprzęt
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_sprzet WHERE id=%s", [pk])


class RezerwacjaViewSet(viewsets.ModelViewSet):
    serializer_class = RezerwacjaSerializer
    permission_classes = [SessionPermission]

    def get_queryset(self):
        user = get_session_user(self.request)
        
        if user and user.rola == 'admin':
            # SQL QUERY - SELECT wszystkie rezerwacje JOIN sprzęt i użytkownik dla admina ORDER BY id
            return Rezerwacja.objects.raw(
                """
                SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id
                FROM labflow_rezerwacja r
                JOIN labflow_sprzet s ON r.sprzet_id = s.id
                JOIN labflow_uzytkownik u ON r.uzytkownik_id = u.id
                ORDER BY r.id
                """
            )
        elif user:
            # SQL QUERY - SELECT rezerwacje użytkownika JOIN sprzęt i użytkownik ORDER BY id
            return Rezerwacja.objects.raw(
                """
                SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id
                FROM labflow_rezerwacja r
                JOIN labflow_sprzet s ON r.sprzet_id = s.id
                JOIN labflow_uzytkownik u ON r.uzytkownik_id = u.id
                WHERE r.uzytkownik_id = %s
                ORDER BY r.id
                """,
                [user.id]
            )
        else:
            # Zwróć pusty queryset
            return Rezerwacja.objects.raw(
                "SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id FROM labflow_rezerwacja r WHERE 1=0"
            )

    def get_object(self):
        # SQL QUERY - SELECT rezerwację po ID z JOIN sprzęt i użytkownik
        pk = self.kwargs.get('pk')
        user = get_session_user(self.request)
        
        with connection.cursor() as cursor:
            if user and user.rola == 'admin':
                cursor.execute(
                    """
                    SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id
                    FROM labflow_rezerwacja r
                    JOIN labflow_sprzet s ON r.sprzet_id = s.id
                    JOIN labflow_uzytkownik u ON r.uzytkownik_id = u.id
                    WHERE r.id=%s
                    """,
                    [pk]
                )
            else:
                cursor.execute(
                    """
                    SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id
                    FROM labflow_rezerwacja r
                    JOIN labflow_sprzet s ON r.sprzet_id = s.id
                    JOIN labflow_uzytkownik u ON r.uzytkownik_id = u.id
                    WHERE r.id=%s AND r.uzytkownik_id=%s
                    """,
                    [pk, user.id if user else None]
                )
            
            row = cursor.fetchone()
            if row:
                obj = Rezerwacja(id=row[0], data_rozpoczecia=row[1], data_zakonczenia=row[2], 
                                status=row[3], uzytkownik_id=row[4], sprzet_id=row[5])
                return obj
        
        raise NotFound("Rezerwacja nie znaleziona.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT rezerwacja
        user = get_session_user(self.request)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_rezerwacja (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id) VALUES (%s, %s, %s, %s, %s)",
                [serializer.validated_data['data_rozpoczecia'], serializer.validated_data['data_zakonczenia'],
                 serializer.validated_data['status'], user.id, serializer.validated_data['sprzet'].id]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE rezerwacja
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_rezerwacja SET data_rozpoczecia=%s, data_zakonczenia=%s, status=%s, uzytkownik_id=%s, sprzet_id=%s WHERE id=%s",
                [serializer.validated_data['data_rozpoczecia'], serializer.validated_data['data_zakonczenia'],
                 serializer.validated_data['status'], serializer.validated_data['uzytkownik'].id,
                 serializer.validated_data['sprzet'].id, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE rezerwacja
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_rezerwacja WHERE id=%s", [pk])

    def create(self, request, *args, **kwargs):
        data_rozpoczecia = request.data.get('data_rozpoczecia')
        data_zakonczenia = request.data.get('data_zakonczenia')
        sprzet_id = request.data.get('sprzet')

        if not (data_rozpoczecia and data_zakonczenia and sprzet_id):
            return Response({'error': 'Brak wymaganych danych.'}, status=400)

        # SQL QUERY - CHECK konflikt rezerwacji
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM labflow_rezerwacja 
                WHERE sprzet_id = %s 
                AND data_rozpoczecia < %s 
                AND data_zakonczenia > %s
                """,
                [sprzet_id, data_zakonczenia, data_rozpoczecia]
            )
            if cursor.fetchone():
                return Response({'error': 'Istnieje już rezerwacja na ten sprzęt w podanym czasie.'}, status=400)

        return super().create(request, *args, **kwargs)


class SerwisViewSet(viewsets.ModelViewSet):
    serializer_class = SerwisSerializer
    permission_classes = [StaffPermission]

    def get_queryset(self):
        # SQL QUERY - SELECT wszystkie serwisy JOIN sprzęt ORDER BY id
        return Serwis.objects.raw(
            """
            SELECT s.id, s.data_zgloszenia, s.opis, s.status, s.sprzet_id
            FROM labflow_serwis s
            JOIN labflow_sprzet sp ON s.sprzet_id = sp.id
            ORDER BY s.id
            """
        )

    def get_object(self):
        # SQL QUERY - SELECT serwis po ID z JOIN sprzęt
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.id, s.data_zgloszenia, s.opis, s.status, s.sprzet_id
                FROM labflow_serwis s
                JOIN labflow_sprzet sp ON s.sprzet_id = sp.id
                WHERE s.id=%s
                """,
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Serwis(id=row[0], data_zgloszenia=row[1], opis=row[2], status=row[3], sprzet_id=row[4])
                return obj
            raise NotFound("Serwis nie znaleziony.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT serwis
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id) VALUES (%s, %s, %s, %s)",
                [serializer.validated_data['data_zgloszenia'], serializer.validated_data['opis'],
                 serializer.validated_data['status'], serializer.validated_data['sprzet'].id]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE serwis
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_serwis SET data_zgloszenia=%s, opis=%s, status=%s, sprzet_id=%s WHERE id=%s",
                [serializer.validated_data['data_zgloszenia'], serializer.validated_data['opis'],
                 serializer.validated_data['status'], serializer.validated_data['sprzet'].id, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE serwis
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_serwis WHERE id=%s", [pk])
