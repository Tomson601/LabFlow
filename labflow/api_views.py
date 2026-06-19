from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db import connection

from .models import Laboratorium, Rezerwacja, Serwis, Sprzet, Uzytkownik
from .db_helpers import fetch_user_by_id
from .serializers import (
    LaboratoriumSerializer,
    RezerwacjaSerializer,
    SerwisSerializer,
    SprzetSerializer,
    UzytkownikSerializer,
)


CLOSED_REZERWACJA_STATUSES = ['zakończona', 'odrzucona', 'anulowana']


def get_session_user(request):
    return fetch_user_by_id(request.session.get('user_id'))


def sync_rezerwacja_statuses():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE labflow_rezerwacja
            SET status = CASE
                WHEN CAST(data_zakonczenia AS datetime2) <= CAST(SYSDATETIME() AS datetime2) THEN %s
                WHEN CAST(data_rozpoczecia AS datetime2) <= CAST(SYSDATETIME() AS datetime2)
                    AND CAST(data_zakonczenia AS datetime2) > CAST(SYSDATETIME() AS datetime2) THEN %s
                ELSE %s
            END
            WHERE status NOT IN (%s, %s)
            """,
            ['zakończona', 'aktywna', 'oczekująca', 'odrzucona', 'anulowana']
        )


class SessionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return get_session_user(request) is not None


class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = get_session_user(request)
        return bool(user and user.rola == 'admin')


class StaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = get_session_user(request)
        if request.method == 'DELETE':
            return bool(user and user.rola == 'admin')
        return bool(user and user.rola in {'admin', 'pracownik'})


class StaffEquipmentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = get_session_user(request)
        return bool(user and user.rola in {'admin', 'pracownik'})


class LaboratoriumViewSet(viewsets.ModelViewSet):
    serializer_class = LaboratoriumSerializer
    permission_classes = [StaffEquipmentPermission]

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
        instance = self.get_object()
        nazwa = serializer.validated_data.get('nazwa', instance.nazwa)
        lokalizacja = serializer.validated_data.get('lokalizacja', instance.lokalizacja)
        opis = serializer.validated_data.get('opis', instance.opis)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_laboratorium SET nazwa=%s, lokalizacja=%s, opis=%s WHERE id=%s",
                [nazwa, lokalizacja, opis, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE laboratorium i zależne rekordy
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM labflow_rezerwacja
                WHERE sprzet_id IN (
                    SELECT id FROM labflow_sprzet WHERE laboratorium_id=%s
                )
                """,
                [pk]
            )
            cursor.execute(
                """
                DELETE FROM labflow_serwis
                WHERE sprzet_id IN (
                    SELECT id FROM labflow_sprzet WHERE laboratorium_id=%s
                )
                """,
                [pk]
            )
            cursor.execute("DELETE FROM labflow_sprzet WHERE laboratorium_id=%s", [pk])
            cursor.execute("DELETE FROM labflow_laboratorium WHERE id=%s", [pk])


class UzytkownikViewSet(viewsets.ModelViewSet):
    serializer_class = UzytkownikSerializer
    permission_classes = [AdminPermission]

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

    def create(self, request, *args, **kwargs):
        raise ValidationError({'error': 'Użytkownicy są dodawani tylko przez rejestrację.'})

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE użytkownika
        pk = self.kwargs.get('pk')
        user = get_session_user(self.request)
        instance = self.get_object()
        if 'email' in self.request.data and self.request.data.get('email') != instance.email:
            raise ValidationError({'error': 'Nie można zmieniać adresu email użytkownika.'})
        if user and str(user.id) == str(pk) and 'rola' in self.request.data:
            raise ValidationError({'error': 'Nie można zmieniać własnej roli.'})
        imie = serializer.validated_data.get('imie', instance.imie)
        nazwisko = serializer.validated_data.get('nazwisko', instance.nazwisko)
        email = instance.email
        rola = serializer.validated_data.get('rola', instance.rola)
        haslo = serializer.validated_data.get('haslo', instance.haslo)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_uzytkownik SET imie=%s, nazwisko=%s, email=%s, rola=%s, haslo=%s WHERE id=%s",
                [imie, nazwisko, email, rola, haslo, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE użytkownika
        pk = self.kwargs.get('pk')
        user = get_session_user(self.request)
        if user and str(user.id) == str(pk):
            raise ValidationError({'error': 'Nie można usunąć aktualnie zalogowanego użytkownika.'})
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_uzytkownik WHERE id=%s", [pk])


class SprzetViewSet(viewsets.ModelViewSet):
    serializer_class = SprzetSerializer
    permission_classes = [StaffEquipmentPermission]

    def get_status_sql(self):
        return """
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM labflow_serwis sv
                    WHERE sv.sprzet_id = s.id
                    AND sv.status IN ('nowe', 'w trakcie')
                ) THEN 'serwis'
                WHEN EXISTS (
                    SELECT 1
                    FROM labflow_rezerwacja r
                    WHERE r.sprzet_id = s.id
                    AND r.status = 'aktywna'
                    AND CAST(r.data_rozpoczecia AS datetime2) <= CAST(SYSDATETIME() AS datetime2)
                    AND CAST(r.data_zakonczenia AS datetime2) > CAST(SYSDATETIME() AS datetime2)
                ) THEN 'zarezerwowany'
                ELSE 'dostępny'
            END
        """

    def get_queryset(self):
        sync_rezerwacja_statuses()
        laboratorium_id = self.request.query_params.get('laboratorium')
        
        if laboratorium_id:
            # SQL QUERY - SELECT sprzęt JOIN laboratorium WHERE laboratorium_id ORDER BY id
            return Sprzet.objects.raw(
                f"""
                SELECT s.id, s.nazwa, s.kategoria, {self.get_status_sql()} AS status, s.status AS status_bazowy, s.laboratorium_id, l.nazwa AS laboratorium_nazwa
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
                f"""
                SELECT s.id, s.nazwa, s.kategoria, {self.get_status_sql()} AS status, s.status AS status_bazowy, s.laboratorium_id, l.nazwa AS laboratorium_nazwa
                FROM labflow_sprzet s
                JOIN labflow_laboratorium l ON s.laboratorium_id = l.id
                ORDER BY s.id
                """
            )

    def get_object(self):
        # SQL QUERY - SELECT sprzęt po ID z JOIN laboratorium
        sync_rezerwacja_statuses()
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT s.id, s.nazwa, s.kategoria, {self.get_status_sql()} AS status, s.status AS status_bazowy, s.laboratorium_id, l.nazwa AS laboratorium_nazwa
                FROM labflow_sprzet s
                JOIN labflow_laboratorium l ON s.laboratorium_id = l.id
                WHERE s.id=%s
                """,
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Sprzet(id=row[0], nazwa=row[1], kategoria=row[2], status=row[3], laboratorium_id=row[5])
                obj.status_bazowy = row[4]
                obj.laboratorium_nazwa = row[6]
                return obj
            raise NotFound("Sprzęt nie znaleziony.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT sprzęt
        status = serializer.validated_data.get('status', 'dostępny')
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id) VALUES (%s, %s, %s, %s)",
                [serializer.validated_data['nazwa'], serializer.validated_data['kategoria'],
                 status, serializer.validated_data['laboratorium_id']]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE sprzęt
        pk = self.kwargs.get('pk')
        instance = self.get_object()
        nazwa = serializer.validated_data.get('nazwa', instance.nazwa)
        kategoria = serializer.validated_data.get('kategoria', instance.kategoria)
        status = serializer.validated_data.get('status', getattr(instance, 'status_bazowy', instance.status))
        laboratorium = serializer.validated_data.get('laboratorium_id')
        laboratorium_id = laboratorium if laboratorium else instance.laboratorium_id
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_sprzet SET nazwa=%s, kategoria=%s, status=%s, laboratorium_id=%s WHERE id=%s",
                [nazwa, kategoria, status, laboratorium_id, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE sprzęt i zależne rekordy
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_rezerwacja WHERE sprzet_id=%s", [pk])
            cursor.execute("DELETE FROM labflow_serwis WHERE sprzet_id=%s", [pk])
            cursor.execute("DELETE FROM labflow_sprzet WHERE id=%s", [pk])


class RezerwacjaViewSet(viewsets.ModelViewSet):
    serializer_class = RezerwacjaSerializer
    permission_classes = [SessionPermission]

    def is_sprzet_in_service(self, sprzet_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 id
                FROM labflow_serwis
                WHERE sprzet_id = %s AND status = 'w trakcie'
                """,
                [sprzet_id]
            )
            return cursor.fetchone() is not None

    def has_conflict(self, sprzet_id, data_rozpoczecia, data_zakonczenia, exclude_id=None):
        params = [sprzet_id, data_zakonczenia, data_rozpoczecia, *CLOSED_REZERWACJA_STATUSES]
        exclude_sql = ''
        if exclude_id:
            exclude_sql = 'AND id <> %s'
            params.append(exclude_id)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id FROM labflow_rezerwacja
                WHERE sprzet_id = %s
                AND data_rozpoczecia < %s
                AND data_zakonczenia > %s
                AND status NOT IN (%s, %s, %s)
                {exclude_sql}
                """,
                params
            )
            return cursor.fetchone() is not None

    def get_queryset(self):
        sync_rezerwacja_statuses()
        user = get_session_user(self.request)
        
        if user and user.rola == 'admin':
            # SQL QUERY - SELECT wszystkie rezerwacje JOIN sprzęt i użytkownik dla admina ORDER BY id
            return Rezerwacja.objects.raw(
                """
                SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id,
                       s.nazwa AS sprzet_nazwa, CONCAT(u.imie, ' ', u.nazwisko) AS uzytkownik_nazwa, u.email AS uzytkownik_email
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
                SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id,
                       s.nazwa AS sprzet_nazwa, CONCAT(u.imie, ' ', u.nazwisko) AS uzytkownik_nazwa, u.email AS uzytkownik_email
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
                "SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id, CAST('' AS varchar(100)) AS sprzet_nazwa, CAST('' AS varchar(101)) AS uzytkownik_nazwa, CAST('' AS varchar(254)) AS uzytkownik_email FROM labflow_rezerwacja r WHERE 1=0"
            )

    @action(detail=False, methods=['get'], url_path='dostepnosc')
    def dostepnosc(self, request):
        sync_rezerwacja_statuses()
        sprzet_id = request.query_params.get('sprzet')
        exclude_id = request.query_params.get('exclude')

        if not sprzet_id:
            return Response({'error': 'Brak identyfikatora sprzetu.'}, status=400)

        params = [sprzet_id, *CLOSED_REZERWACJA_STATUSES]
        exclude_sql = ''
        if exclude_id:
            exclude_sql = 'AND id <> %s'
            params.append(exclude_id)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, data_rozpoczecia, data_zakonczenia, status
                FROM labflow_rezerwacja
                WHERE sprzet_id = %s
                AND status NOT IN (%s, %s, %s)
                {exclude_sql}
                ORDER BY data_rozpoczecia
                """,
                params
            )
            rows = cursor.fetchall()

        return Response([
            {
                'id': row[0],
                'data_rozpoczecia': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
                'data_zakonczenia': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else '',
                'status': row[3],
            }
            for row in rows
        ])

    def get_object(self):
        # SQL QUERY - SELECT rezerwację po ID z JOIN sprzęt i użytkownik
        sync_rezerwacja_statuses()
        pk = self.kwargs.get('pk')
        user = get_session_user(self.request)
        
        with connection.cursor() as cursor:
            if user and user.rola == 'admin':
                cursor.execute(
                    """
                    SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id,
                           s.nazwa AS sprzet_nazwa, CONCAT(u.imie, ' ', u.nazwisko) AS uzytkownik_nazwa, u.email AS uzytkownik_email
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
                    SELECT r.id, r.data_rozpoczecia, r.data_zakonczenia, r.status, r.uzytkownik_id, r.sprzet_id,
                           s.nazwa AS sprzet_nazwa, CONCAT(u.imie, ' ', u.nazwisko) AS uzytkownik_nazwa, u.email AS uzytkownik_email
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
                obj.sprzet_nazwa = row[6]
                obj.uzytkownik_nazwa = row[7]
                obj.uzytkownik_email = row[8]
                return obj
        
        raise NotFound("Rezerwacja nie znaleziona.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT rezerwacja
        user = get_session_user(self.request)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_rezerwacja (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id) VALUES (%s, %s, %s, %s, %s)",
                [serializer.validated_data['data_rozpoczecia'], serializer.validated_data['data_zakonczenia'],
                 serializer.validated_data['status'], user.id, serializer.validated_data['sprzet_id']]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE rezerwacja
        pk = self.kwargs.get('pk')
        instance = self.get_object()
        if instance.status in CLOSED_REZERWACJA_STATUSES:
            raise ValidationError({'error': 'Nie można edytować zakończonej, odrzuconej ani anulowanej rezerwacji.'})

        data_rozpoczecia = serializer.validated_data.get('data_rozpoczecia', instance.data_rozpoczecia)
        data_zakonczenia = serializer.validated_data.get('data_zakonczenia', instance.data_zakonczenia)
        status = serializer.validated_data.get('status', instance.status)
        uzytkownik_id = instance.uzytkownik_id
        sprzet = serializer.validated_data.get('sprzet_id')
        sprzet_id = sprzet if sprzet else instance.sprzet_id

        if data_rozpoczecia >= data_zakonczenia:
            raise ValidationError({'error': 'Data zakończenia musi być późniejsza niż data rozpoczęcia.'})

        if self.is_sprzet_in_service(sprzet_id):
            raise ValidationError({'error': 'Nie można zarezerwować sprzętu, który jest aktualnie w serwisie.'})

        if self.has_conflict(sprzet_id, data_rozpoczecia, data_zakonczenia, exclude_id=pk):
            raise ValidationError({'error': 'Istnieje już rezerwacja na ten sprzęt w podanym czasie.'})

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_rezerwacja SET data_rozpoczecia=%s, data_zakonczenia=%s, status=%s, uzytkownik_id=%s, sprzet_id=%s WHERE id=%s",
                [data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id, pk]
            )
        sync_rezerwacja_statuses()

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE rezerwacja
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_rezerwacja WHERE id=%s", [pk])

    def create(self, request, *args, **kwargs):
        sync_rezerwacja_statuses()
        data_rozpoczecia = request.data.get('data_rozpoczecia')
        data_zakonczenia = request.data.get('data_zakonczenia')
        sprzet_id = request.data.get('sprzet')

        if not (data_rozpoczecia and data_zakonczenia and sprzet_id):
            return Response({'error': 'Brak wymaganych danych.'}, status=400)

        if self.is_sprzet_in_service(sprzet_id):
            return Response({'error': 'Nie można zarezerwować sprzętu, który jest aktualnie w serwisie.'}, status=400)

        # SQL QUERY - CHECK konflikt rezerwacji
        if self.has_conflict(sprzet_id, data_rozpoczecia, data_zakonczenia):
            return Response({'error': 'Istnieje już rezerwacja na ten sprzęt w podanym czasie.'}, status=400)

        return super().create(request, *args, **kwargs)


class SerwisViewSet(viewsets.ModelViewSet):
    serializer_class = SerwisSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [SessionPermission()]
        return [StaffPermission()]

    def get_queryset(self):
        # SQL QUERY - SELECT wszystkie serwisy JOIN sprzęt ORDER BY id
        return Serwis.objects.raw(
            """
            SELECT s.id, s.data_zgloszenia, s.opis, s.status, s.sprzet_id, sp.nazwa AS sprzet_nazwa
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
                SELECT s.id, s.data_zgloszenia, s.opis, s.status, s.sprzet_id, sp.nazwa AS sprzet_nazwa
                FROM labflow_serwis s
                JOIN labflow_sprzet sp ON s.sprzet_id = sp.id
                WHERE s.id=%s
                """,
                [pk]
            )
            row = cursor.fetchone()
            if row:
                obj = Serwis(id=row[0], data_zgloszenia=row[1], opis=row[2], status=row[3], sprzet_id=row[4])
                obj.sprzet_nazwa = row[5]
                return obj
            raise NotFound("Serwis nie znaleziony.")

    def perform_create(self, serializer):
        # SQL QUERY - INSERT serwis
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id) VALUES (%s, %s, %s, %s)",
                [serializer.validated_data['data_zgloszenia'], serializer.validated_data['opis'],
                 serializer.validated_data['status'], serializer.validated_data['sprzet_id']]
            )

    def perform_update(self, serializer):
        # SQL QUERY - UPDATE serwis
        pk = self.kwargs.get('pk')
        instance = self.get_object()
        data_zgloszenia = serializer.validated_data.get('data_zgloszenia', instance.data_zgloszenia)
        opis = serializer.validated_data.get('opis', instance.opis)
        status = serializer.validated_data.get('status', instance.status)
        sprzet = serializer.validated_data.get('sprzet_id')
        sprzet_id = sprzet if sprzet else instance.sprzet_id
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE labflow_serwis SET data_zgloszenia=%s, opis=%s, status=%s, sprzet_id=%s WHERE id=%s",
                [data_zgloszenia, opis, status, sprzet_id, pk]
            )

    def perform_destroy(self, instance):
        # SQL QUERY - DELETE serwis
        pk = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM labflow_serwis WHERE id=%s", [pk])
