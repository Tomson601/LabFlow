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
    class Meta:
        model = Sprzet
        fields = '__all__'

class RezerwacjaSerializer(serializers.ModelSerializer):
    sprzet_nazwa = serializers.CharField(source='sprzet.nazwa', read_only=True)
    uzytkownik = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Rezerwacja
        fields = ['id', 'sprzet', 'sprzet_nazwa', 'data_rozpoczecia', 'data_zakonczenia', 'status', 'uzytkownik']

class SerwisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serwis
        fields = '__all__'
