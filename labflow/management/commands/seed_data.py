from django.core.management.base import BaseCommand
from labflow.models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis
from django.utils import timezone
from datetime import timedelta
from django.db import connection


class Command(BaseCommand):
    help = "Dodaje przykładowe dane do bazy"

    def handle(self, *args, **kwargs):
        # SQL QUERY - CHECK czy dane już istnieją
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM labflow_laboratorium")
            if cursor.fetchone()[0] > 0:
                self.stdout.write(self.style.WARNING("Przykładowe dane już istnieją."))
                return

            # SQL QUERY - INSERT laboratoria
            cursor.execute(
                """
                INSERT INTO labflow_laboratorium (nazwa, lokalizacja, opis)
                VALUES (%s, %s, %s)
                """,
                ["Laboratorium Robotyki", "Budynek A, sala 101", "Stanowiska do testów robotów mobilnych"]
            )
            lab1_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_laboratorium (nazwa, lokalizacja, opis)
                VALUES (%s, %s, %s)
                """,
                ["Laboratorium Elektroniki", "Budynek B, sala 12", "Pracownia układów wbudowanych i pomiarów"]
            )
            lab2_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_laboratorium (nazwa, lokalizacja, opis)
                VALUES (%s, %s, %s)
                """,
                ["Laboratorium Informatyki", "Budynek C, sala 22", "Nowoczesna sala komputerowa"]
            )
            lab3_id = cursor.lastrowid

            # SQL QUERY - INSERT użytkownicy
            cursor.execute(
                """
                INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                ["Jan", "Kowalski", "jan.kowalski@example.com", "admin", "admin123"]
            )
            user1_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                ["Anna", "Nowak", "anna.nowak@example.com", "student", "technik123"]
            )
            user2_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                ["Piotr", "Zieliński", "pracownik@example.com", "pracownik", "pracownik123"]
            )
            user3_id = cursor.lastrowid

            # SQL QUERY - INSERT sprzęt
            cursor.execute(
                """
                INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Oscyloskop Rigol", "pomiarowy", "dostępny", lab2_id]
            )
            sprzet1_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Drukarka 3D Prusa", "prototypowanie", "zarezerwowany", lab1_id]
            )
            sprzet2_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Zasilacz laboratoryjny", "zasilanie", "serwis", lab2_id]
            )
            sprzet3_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Komputer Dell", "komputer", "dostępny", lab3_id]
            )
            sprzet4_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Robot edukacyjny", "robotyka", "zarezerwowany", lab1_id]
            )
            sprzet5_id = cursor.lastrowid

            teraz = timezone.now()
            start1 = teraz + timedelta(days=1)
            end1 = teraz + timedelta(days=1, hours=2)
            start2 = teraz + timedelta(days=2)
            end2 = teraz + timedelta(days=2, hours=3)
            start3 = teraz - timedelta(days=1)
            end3 = teraz - timedelta(days=1, hours=-2)

            # SQL QUERY - INSERT rezerwacje
            cursor.execute(
                """
                INSERT INTO labflow_rezerwacja (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [start1, end1, "aktywna", user2_id, sprzet2_id]
            )

            cursor.execute(
                """
                INSERT INTO labflow_rezerwacja (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [start2, end2, "oczekująca", user3_id, sprzet5_id]
            )

            cursor.execute(
                """
                INSERT INTO labflow_rezerwacja (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [start3, end3, "zakończona", user1_id, sprzet1_id]
            )

            # SQL QUERY - INSERT serwisy
            cursor.execute(
                """
                INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id)
                VALUES (%s, %s, %s, %s)
                """,
                [teraz - timedelta(days=2), "Niestabilne napięcie wyjściowe", "w trakcie", sprzet3_id]
            )

            cursor.execute(
                """
                INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id)
                VALUES (%s, %s, %s, %s)
                """,
                [teraz - timedelta(days=1), "Awaria głowicy drukującej", "nowe", sprzet2_id]
            )

            cursor.execute(
                """
                INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id)
                VALUES (%s, %s, %s, %s)
                """,
                [teraz - timedelta(days=3), "Brak połączenia z siecią", "zakończone", sprzet4_id]
            )

        self.stdout.write(self.style.SUCCESS("Dodano przykładowe dane do bazy."))
