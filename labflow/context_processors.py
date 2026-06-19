from .db_helpers import fetch_user_by_id


def current_user(request):
    return {'user': fetch_user_by_id(request.session.get('user_id'))}
