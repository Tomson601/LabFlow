from django.db import models
from django.contrib.auth.models import AbstractUser

class Laboratorium(models.Model):
    nazwa = models.CharField(max_length=100)
    lokalizacja = models.CharField(max_length=100)
    opis = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nazwa

class Uzytkownik(AbstractUser):
    imie = models.CharField(max_length=50)
    nazwisko = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    rola = models.CharField(max_length=50)
    # haslo handled by AbstractUser

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.imie} {self.nazwisko}"

class Sprzet(models.Model):
    nazwa = models.CharField(max_length=100)
    kategoria = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    laboratorium = models.ForeignKey(Laboratorium, on_delete=models.CASCADE)

    def __str__(self):
        return self.nazwa

class Rezerwacja(models.Model):
    data_rozpoczecia = models.DateTimeField()
    data_zakonczenia = models.DateTimeField()
    status = models.CharField(max_length=50)
    uzytkownik = models.ForeignKey('Uzytkownik', on_delete=models.CASCADE)
    sprzet = models.ForeignKey(Sprzet, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.uzytkownik} - {self.sprzet} ({self.data_rozpoczecia})"

class Serwis(models.Model):
    data_zgloszenia = models.DateTimeField()
    opis = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    sprzet = models.ForeignKey(Sprzet, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.sprzet} - {self.status}"
