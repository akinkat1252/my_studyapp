from .exceptions import MissingUserLanguageError
from .models import CustomUser, Language


def get_user_language(user: CustomUser) -> Language:
    if not user.user_language:
        raise MissingUserLanguageError(f"user_language missing for user {user.id}")
    
    return user.user_language


def get_default_language() -> Language:
    try:
        return Language.objects.get(code="en")
    except Language.DoesNotExist:
        raise RuntimeError("Default language (code='en') is not seeded.")
