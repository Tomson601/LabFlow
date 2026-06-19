from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Dodaje przykladowe dane do bazy"

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # SQL QUERY - CHECK czy dane juz istnieja
            cursor.execute("SELECT COUNT(*) FROM labflow_laboratorium")
            if cursor.fetchone()[0] > 0:
                self.stdout.write(self.style.WARNING("Przykladowe dane juz istnieja."))
                return

            def insert_laboratorium(nazwa, lokalizacja, opis):
                # SQL QUERY - INSERT laboratorium
                cursor.execute(
                    """
                    INSERT INTO labflow_laboratorium (nazwa, lokalizacja, opis)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s)
                    """,
                    [nazwa, lokalizacja, opis],
                )
                return cursor.fetchone()[0]

            def insert_uzytkownik(imie, nazwisko, email, rola, haslo):
                # SQL QUERY - INSERT uzytkownika
                cursor.execute(
                    """
                    INSERT INTO labflow_uzytkownik (imie, nazwisko, email, rola, haslo)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [imie, nazwisko, email, rola, haslo],
                )
                return cursor.fetchone()[0]

            def insert_sprzet(nazwa, kategoria, status, laboratorium_id):
                # SQL QUERY - INSERT sprzet
                cursor.execute(
                    """
                    INSERT INTO labflow_sprzet (nazwa, kategoria, status, laboratorium_id)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s)
                    """,
                    [nazwa, kategoria, status, laboratorium_id],
                )
                return cursor.fetchone()[0]

            def insert_rezerwacja(start, koniec, status, uzytkownik_id, sprzet_id):
                # SQL QUERY - INSERT rezerwacja
                cursor.execute(
                    """
                    INSERT INTO labflow_rezerwacja
                        (data_rozpoczecia, data_zakonczenia, status, uzytkownik_id, sprzet_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [start, koniec, status, uzytkownik_id, sprzet_id],
                )

            def insert_serwis(data_zgloszenia, opis, status, sprzet_id):
                # SQL QUERY - INSERT serwis
                cursor.execute(
                    """
                    INSERT INTO labflow_serwis (data_zgloszenia, opis, status, sprzet_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [data_zgloszenia, opis, status, sprzet_id],
                )

            lab_robotyka_id = insert_laboratorium(
                "Laboratorium Robotyki",
                "Budynek A, sala 101",
                "Roboty mobilne, stanowiska testowe i druk 3D",
            )
            lab_elektronika_id = insert_laboratorium(
                "Laboratorium Elektroniki",
                "Budynek B, sala 12",
                "Pomiary, zasilanie i uklady wbudowane",
            )
            lab_informatyka_id = insert_laboratorium(
                "Laboratorium Informatyki",
                "Budynek C, sala 22",
                "Komputery, siec i oprogramowanie laboratoryjne",
            )
            lab_chemia_id = insert_laboratorium(
                "Laboratorium Chemiczne",
                "Budynek D, sala 7",
                "Analiza probek i praca z mikroskopami",
            )

            admin_id = insert_uzytkownik(
                "Jan",
                "Kowalski",
                "admin@labflow.local",
                "admin",
                "admin123",
            )
            pracownik_id = insert_uzytkownik(
                "Piotr",
                "Zielinski",
                "pracownik@labflow.local",
                "pracownik",
                "pracownik123",
            )
            student_id = insert_uzytkownik(
                "Anna",
                "Nowak",
                "student@labflow.local",
                "student",
                "student123",
            )
            student_2_id = insert_uzytkownik(
                "Marta",
                "Wisniewska",
                "marta@student.local",
                "student",
                "student123",
            )

            oscyloskop_id = insert_sprzet("Oscyloskop Rigol DS1054Z", "pomiarowy", "dostępny", lab_elektronika_id)
            zasilacz_id = insert_sprzet("Zasilacz laboratoryjny Korad", "zasilanie", "dostępny", lab_elektronika_id)
            drukarka_id = insert_sprzet("Drukarka 3D Prusa MK4", "prototypowanie", "dostępny", lab_robotyka_id)
            robot_id = insert_sprzet("Robot edukacyjny TurtleBot", "robotyka", "dostępny", lab_robotyka_id)
            komputer_id = insert_sprzet("Komputer Dell Precision", "komputer", "dostępny", lab_informatyka_id)
            projektor_id = insert_sprzet("Projektor Epson", "multimedia", "dostępny", lab_informatyka_id)
            mikroskop_id = insert_sprzet("Mikroskop cyfrowy", "optyka", "dostępny", lab_chemia_id)
            spektrometr_id = insert_sprzet("Spektrometr UV-VIS", "analiza", "dostępny", lab_chemia_id)

            teraz = timezone.now()

            insert_rezerwacja(
                teraz - timedelta(hours=1),
                teraz + timedelta(hours=2),
                "aktywna",
                student_id,
                oscyloskop_id,
            )
            insert_rezerwacja(
                teraz + timedelta(days=1, hours=1),
                teraz + timedelta(days=1, hours=4),
                "oczekująca",
                student_2_id,
                drukarka_id,
            )
            insert_rezerwacja(
                teraz + timedelta(days=2),
                teraz + timedelta(days=2, hours=3),
                "oczekująca",
                pracownik_id,
                mikroskop_id,
            )
            insert_rezerwacja(
                teraz - timedelta(days=2, hours=3),
                teraz - timedelta(days=2, hours=1),
                "zakończona",
                admin_id,
                komputer_id,
            )
            

            insert_serwis(
                teraz - timedelta(days=1, hours=3),
                "Niestabilne napiecie wyjsciowe podczas obciazenia.",
                "w trakcie",
                zasilacz_id,
            )
            insert_serwis(
                teraz - timedelta(hours=8),
                "Zgloszono problem z kalibracja osi robota.",
                "nowe",
                robot_id,
            )
            insert_serwis(
                teraz - timedelta(days=5),
                "Wymieniono lampe i sprawdzono obraz.",
                "zakończone",
                projektor_id,
            )

        self.stdout.write(self.style.SUCCESS("Dodano przykladowe dane do bazy."))
