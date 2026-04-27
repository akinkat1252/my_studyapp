from typing import Optional

from accounts.models import CustomUser
from accounts.services import get_default_language, get_user_language


def language_constraint_common(user: CustomUser) -> str:
    language = get_user_language(user=user)
    if language is None:
        language = get_default_language()

    return (
        f"The user's preferred language is {language.name} "
        f"(code: {language.code}).\n"
        "All natural language text in the output must be written in this language.\n"
        "Do not mix multiple languages in the same response.\n"
        "Do not translate technical keywords unless necessary.\n"
    )
