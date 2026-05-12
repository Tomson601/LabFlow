from rest_framework import serializers
from .models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis


class LaboratoriumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorium
        fields = '__all__'

class UzytkownikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uzytkownik
        exclude = ['password', 'user_permissions', 'groups', 'is_superuser', 'is_staff', 'is_active', 'last_login', 'date_joined']

class SprzetSerializer(serializers.ModelSerializer):
    laboratorium_nazwa = serializers.CharField(source='laboratorium.nazwa', read_only=True)
    
    def validate_status(self, value):
        allowed = ['dostępny', 'zarezerwowany', 'serwis', 'w użyciu']
        if value.lower() not in allowed:
            raise serializers.ValidationError(f"Status sprzętu musi być jednym z: {allowed}")
        return value.lower()
    class Meta:
        model = Sprzet
        fields = '__all__'
        extra_fields = ['laboratorium_nazwa']
        # Dodajemy laboratorium_nazwa do pól zwracanych przez serializer
        fields = list(fields) + ['laboratorium_nazwa']

class RezerwacjaSerializer(serializers.ModelSerializer):
    sprzet_nazwa = serializers.CharField(source='sprzet.nazwa', read_only=True)
    uzytkownik = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate_status(self, value):
        allowed = ['oczekująca', 'aktywna', 'zakończona', 'odrzucona', 'zaakceptowana']
        if value.lower() not in allowed:
            raise serializers.ValidationError(f"Status rezerwacji musi być jednym z: {allowed}")
        return value.lower()

    class Meta:
        model = Rezerwacja
        fields = ['id', 'sprzet', 'sprzet_nazwa', 'data_rozpoczecia', 'data_zakonczenia', 'status', 'uzytkownik']

class SerwisSerializer(serializers.ModelSerializer):
    def validate_status(self, value):
        allowed = ['nowe', 'w trakcie', 'zakończone']
        if value.lower() not in allowed:
            raise serializers.ValidationError(f"Status serwisowy musi być jednym z: {allowed}")
        return value.lower()
    class Meta:
        model = Serwis
        fields = '__all__'
