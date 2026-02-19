from django.shortcuts import get_object_or_404, redirect, render

from ai_support.modules.task_management.generate_learning_topic import (
    generate_learning_topic,
)
from task_management.models import DraftLearningGoal


# View to generate learning topic outline using AI and save to draft
def learning_topic_generate_view(request, draft_id):
    draft = get_object_or_404(
        DraftLearningGoal,
        id=draft_id,
        user=request.user
    )

    parsed_json = generate_learning_topic(
        title=draft.title,
        current_level=draft.current_level,
        target_level=draft.target_level,
        description=draft.description,
        language=request.user.user_language,
    )

    draft.raw_generated_data = parsed_json
    draft.save()

    return redirect("task_management:topic_preview", draft_id=draft.id)
