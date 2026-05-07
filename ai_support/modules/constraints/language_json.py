from accounts.models import CustomUser
from ai_support.modules.constraints.language_common import language_constraint_common


def language_constraint_json(user: CustomUser) -> str:
    return (
        language_constraint_common(user=user)
        + "In JSON output:\n"
        + "- Key names must remain exactly as specified in English.\n"
        + "- Only string values should be written in the user's preferred language.\n"
        + "- Do not translate key names."
    )