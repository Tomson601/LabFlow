from django.core.management.base import BaseCommand
from labflow.models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Dodaje przykładowe dane do bazy"

    def handle(self, *args, **kwargs):
        if Laboratorium.objects.exists() or Uzytkownik.objects.exists():
            self.stdout.write(self.style.WARNING("Przykładowe dane już istnieją."))
            return

        lab1 = Laboratorium.objects.create(
            nazwa="Laboratorium Robotyki",
            lokalizacja="Budynek A, sala 101",
            opis="Stanowiska do testów robotów mobilnych"
        )
        lab2 = Laboratorium.objects.create(
            nazwa="Laboratorium Elektroniki",
            lokalizacja="Budynek B, sala 12",
            opis="Pracownia układów wbudowanych i pomiarów"
        )
        lab3 = Laboratorium.objects.create(
            nazwa="Laboratorium Informatyki",
            lokalizacja="Budynek C, sala 22",
            opis="Nowoczesna sala komputerowa"
        )

        user1 = Uzytkownik.objects.create(
            imie="Jan",
            nazwisko="Kowalski",
            email="jan.kowalski@example.com",
            rola="admin",
            haslo="admin123"
        )
        user2 = Uzytkownik.objects.create(
            imie="Anna",
            nazwisko="Nowak",
            email="anna.nowak@example.com",
            rola="student",
            haslo="technik123"
        )
        user3 = Uzytkownik.objects.create(
            imie="Piotr",
            nazwisko="Zieliński",
            email="pracownik@example.com",
            rola="pracownik",
            haslo="pracownik123"
        )

        sprzet1 = Sprzet.objects.create(
            nazwa="Oscyloskop Rigol",
            kategoria="pomiarowy",
            status="dostępny",
            laboratorium=lab2
        )
        sprzet2 = Sprzet.objects.create(
            nazwa="Drukarka 3D Prusa",
            kategoria="prototypowanie",
            status="zarezerwowany",
            laboratorium=lab1
        )
        sprzet3 = Sprzet.objects.create(
            nazwa="Zasilacz laboratoryjny",
            kategoria="zasilanie",
            status="serwis",
            laboratorium=lab2
        )
        sprzet4 = Sprzet.objects.create(
            nazwa="Komputer Dell",
            kategoria="komputer",
            status="dostępny",
            laboratorium=lab3
        )
        sprzet5 = Sprzet.objects.create(
            nazwa="Robot edukacyjny",
            kategoria="robotyka",
            status="zarezerwowany",
            laboratorium=lab1
        )

        teraz = timezone.now()

        Rezerwacja.objects.create(
            data_rozpoczecia=teraz + timedelta(days=1),
            data_zakonczenia=teraz + timedelta(days=1, hours=2),
            status="aktywna",
            uzytkownik=user2,
            sprzet=sprzet2
        )
        Rezerwacja.objects.create(
            data_rozpoczecia=teraz + timedelta(days=2),
            data_zakonczenia=teraz + timedelta(days=2, hours=3),
            status="oczekująca",
            uzytkownik=user3,
            sprzet=sprzet5
        )
        Rezerwacja.objects.create(
            data_rozpoczecia=teraz - timedelta(days=1),
            data_zakonczenia=teraz - timedelta(days=1, hours=-2),
            status="zakończona",
            uzytkownik=user1,
            sprzet=sprzet1
        )

        Serwis.objects.create(
            data_zgloszenia=teraz - timedelta(days=2),
            opis="Niestabilne napięcie wyjściowe",
            status="w trakcie",
            sprzet=sprzet3
        )
        Serwis.objects.create(
            data_zgloszenia=teraz - timedelta(days=1),
            opis="Awaria głowicy drukującej",
            status="nowe",
            sprzet=sprzet2
        )
        Serwis.objects.create(
            data_zgloszenia=teraz - timedelta(days=3),
            opis="Brak połączenia z siecią",
            status="zakończone",
            sprzet=sprzet4
        )

        self.stdout.write(self.style.SUCCESS("Dodano przykładowe dane do bazy."))
