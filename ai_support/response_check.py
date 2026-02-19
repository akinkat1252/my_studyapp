import json

from ai_support.modules.task_management.generate_learning_topic import (
    generate_learning_topic,
)


def test():
    title = "Learn Python Programming"
    current_level = "Beginner"
    target_level = "Intermediate"
    description = "I want to learn Python for data analysis and web development."
    outline = generate_learning_topic(title, current_level, target_level, description)
    print(f"outline: {outline}")
    print(json.dumps(outline, indent=2, ensure_ascii=False))
