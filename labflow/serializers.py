from rest_framework import serializers

from .models import Laboratorium, Rezerwacja, Serwis, Sprzet, Uzytkownik


class LaboratoriumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorium
        fields = '__all__'


class UzytkownikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uzytkownik
        fields = ['id', 'imie', 'nazwisko', 'email', 'rola', 'haslo']
        extra_kwargs = {'haslo': {'write_only': True}}


class SprzetSerializer(serializers.ModelSerializer):
    laboratorium_nazwa = serializers.CharField(source='laboratorium.nazwa', read_only=True)

    class Meta:
        model = Sprzet
        fields = ['id', 'nazwa', 'kategoria', 'status', 'laboratorium', 'laboratorium_nazwa']

    def validate_status(self, value):
        allowed = ['dostępny', 'zarezerwowany', 'serwis', 'w użyciu']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status sprzętu musi być jednym z: {allowed}")
        return normalized


class RezerwacjaSerializer(serializers.ModelSerializer):
    sprzet_nazwa = serializers.CharField(source='sprzet.nazwa', read_only=True)
    uzytkownik = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Rezerwacja
        fields = ['id', 'sprzet', 'sprzet_nazwa', 'data_rozpoczecia', 'data_zakonczenia', 'status', 'uzytkownik']

    def validate_status(self, value):
        allowed = ['oczekująca', 'aktywna', 'zakończona', 'odrzucona', 'zaakceptowana']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status rezerwacji musi być jednym z: {allowed}")
        return normalized


class SerwisSerializer(serializers.ModelSerializer):
    sprzet_nazwa = serializers.CharField(source='sprzet.nazwa', read_only=True)

    class Meta:
        model = Serwis
        fields = ['id', 'data_zgloszenia', 'opis', 'status', 'sprzet', 'sprzet_nazwa']

    def validate_status(self, value):
        allowed = ['nowe', 'w trakcie', 'zakończone']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status serwisowy musi być jednym z: {allowed}")
        return normalized
