from .models import Uzytkownik

def current_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Uzytkownik.objects.get(id=user_id)
            return {'user': user}
        except Uzytkownik.DoesNotExist:
            return {'user': None}
    return {'user': None}
