from typing import Optional

from accounts.models import Language


def get_default_language() -> Language:
    try:
        return Language.objects.get(code="en")
    except Language.DoesNotExist:
        raise RuntimeError("Default language (code='en') is not seeded.")

def language_constraint(language: Optional[Language]) -> str:
    if language is None:
        language = get_default_language()

    return (
        f"The user's preferred language is {language.name}(code:{language.code}).\n"
        "All outputs must be in the user's preferred language.\n"
        "If the title language is ambiguous, do not guess.\n"
        "Always prioritize the user's preferred language."
    )
