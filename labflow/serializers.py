from rest_framework import serializers
from django.db import connection

from .models import Laboratorium, Rezerwacja, Serwis, Sprzet, Uzytkownik


def sql_id_exists(table_name, pk):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id FROM {table_name} WHERE id=%s", [pk])
        return cursor.fetchone() is not None


class LaboratoriumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorium
        fields = '__all__'


class UzytkownikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uzytkownik
        fields = ['id', 'imie', 'nazwisko', 'email', 'rola', 'haslo']
        extra_kwargs = {
            'email': {'validators': []},
            'haslo': {'write_only': True},
        }


class SprzetSerializer(serializers.ModelSerializer):
    laboratorium = serializers.IntegerField(source='laboratorium_id')
    laboratorium_nazwa = serializers.SerializerMethodField()
    status_bazowy = serializers.CharField(read_only=True)

    class Meta:
        model = Sprzet
        fields = ['id', 'nazwa', 'kategoria', 'status', 'status_bazowy', 'laboratorium', 'laboratorium_nazwa']
        extra_kwargs = {'status': {'required': False}}

    def validate_status(self, value):
        allowed = ['dostępny', 'zarezerwowany', 'serwis', 'w użyciu']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status sprzętu musi być jednym z: {allowed}")
        return normalized

    def get_laboratorium_nazwa(self, instance):
        return getattr(instance, 'laboratorium_nazwa', '')

    def validate_laboratorium(self, value):
        if not sql_id_exists('labflow_laboratorium', value):
            raise serializers.ValidationError('Laboratorium nie istnieje.')
        return value


class RezerwacjaSerializer(serializers.ModelSerializer):
    sprzet = serializers.IntegerField(source='sprzet_id')
    sprzet_nazwa = serializers.SerializerMethodField()
    uzytkownik = serializers.IntegerField(source='uzytkownik_id', read_only=True)
    uzytkownik_nazwa = serializers.SerializerMethodField()
    uzytkownik_email = serializers.SerializerMethodField()

    class Meta:
        model = Rezerwacja
        fields = ['id', 'sprzet', 'sprzet_nazwa', 'data_rozpoczecia', 'data_zakonczenia', 'status', 'uzytkownik', 'uzytkownik_nazwa', 'uzytkownik_email']

    def get_uzytkownik_nazwa(self, instance):
        return getattr(instance, 'uzytkownik_nazwa', '')

    def get_uzytkownik_email(self, instance):
        return getattr(instance, 'uzytkownik_email', '')

    def get_sprzet_nazwa(self, instance):
        return getattr(instance, 'sprzet_nazwa', '')

    def validate_sprzet(self, value):
        if not sql_id_exists('labflow_sprzet', value):
            raise serializers.ValidationError('Sprzęt nie istnieje.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data_rozpoczecia = getattr(instance, 'data_rozpoczecia', None)
        data_zakonczenia = getattr(instance, 'data_zakonczenia', None)
        if isinstance(instance, dict):
            data_rozpoczecia = data_rozpoczecia or instance.get('data_rozpoczecia')
            data_zakonczenia = data_zakonczenia or instance.get('data_zakonczenia')
        if data_rozpoczecia:
            data['data_rozpoczecia'] = data_rozpoczecia.strftime('%Y-%m-%d %H:%M:%S')
        if data_zakonczenia:
            data['data_zakonczenia'] = data_zakonczenia.strftime('%Y-%m-%d %H:%M:%S')
        return data

    def validate_status(self, value):
        allowed = ['oczekująca', 'aktywna', 'zakończona', 'odrzucona', 'zaakceptowana', 'anulowana']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status rezerwacji musi być jednym z: {allowed}")
        return normalized


class SerwisSerializer(serializers.ModelSerializer):
    sprzet = serializers.IntegerField(source='sprzet_id')
    sprzet_nazwa = serializers.SerializerMethodField()

    class Meta:
        model = Serwis
        fields = ['id', 'data_zgloszenia', 'opis', 'status', 'sprzet', 'sprzet_nazwa']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data_zgloszenia = getattr(instance, 'data_zgloszenia', None)
        if data_zgloszenia is None and isinstance(instance, dict):
            data_zgloszenia = instance.get('data_zgloszenia')
        if data_zgloszenia:
            data['data_zgloszenia'] = data_zgloszenia.strftime('%Y-%m-%d %H:%M:%S')
        return data

    def get_sprzet_nazwa(self, instance):
        return getattr(instance, 'sprzet_nazwa', '')

    def validate_sprzet(self, value):
        if not sql_id_exists('labflow_sprzet', value):
            raise serializers.ValidationError('Sprzęt nie istnieje.')
        return value

    def validate_status(self, value):
        allowed = ['nowe', 'w trakcie', 'zakończone']
        normalized = value.lower()
        if normalized not in allowed:
            raise serializers.ValidationError(f"Status serwisowy musi być jednym z: {allowed}")
        return normalized
