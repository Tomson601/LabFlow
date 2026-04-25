from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Laboratorium, Uzytkownik, Sprzet, Rezerwacja, Serwis

admin.site.register(Laboratorium)
admin.site.register(Sprzet)
admin.site.register(Rezerwacja)
admin.site.register(Serwis)

class CustomUserAdmin(UserAdmin):
    model = Uzytkownik
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('imie', 'nazwisko', 'rola')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('imie', 'nazwisko', 'rola')}),
    )
    list_display = ['email', 'imie', 'nazwisko', 'rola', 'is_staff']
    search_fields = ['email', 'imie', 'nazwisko', 'rola']

admin.site.register(Uzytkownik, CustomUserAdmin)
