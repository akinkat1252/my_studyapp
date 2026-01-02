from django.db import models
from config import settings_common


class LectureSession(models.Model):
    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lecture_sessions'
    )
    sub_topic = models.ForeignKey(
        'task_management.LearningSubTopic',
        on_delete=models.CASCADE,
        related_name='lecture_sessions',
    )
    topics = models.ManyToManyField(
        'LectureTopic',
        through='LectureProgress',
        related_name='lecture_sessions',
    )
    lecture_number = models.PositiveIntegerField()
    summary = models.TextField(blank=True)
    total_tokens = models.PositiveBigIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Lecture Session"
        verbose_name_plural = "Lecture Sessions"
        ordering = ["user", "sub_topic", "lecture_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sub_topic", "lecture_number"],
                name="unique_lecture_number_per_topic",
            ),
        ]

    def __str__(self):
        return f'Lecture Session: {self.user.username} - {self.sub_topic.title}'
    

class LectureLog(models.Model):
    ROLE_CHOICES = [
        ('ai', 'AI'),
        ('user', 'USER'),
        ('system', 'SYSTEM'),
    ]

    session = models.ForeignKey(
        LectureSession,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField(blank=True)
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Lecture Log: {self.role} - {self.message[:20]}'


class LectureTopic(models.Model):
    sub_topic = models.ForeignKey(
        "task_management.LearningSubTopic",
        on_delete=models.CASCADE,
        related_name="lecture_topics",
    )
    default_order = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Lecture Topic"
        verbose_name_plural = "Lecture Topics"
        ordering = ["default_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["sub_topic", "default_order"],
                name="unique_topic_default_order_per_sub_topic",
            ),
        ]

    def __str__(self):
        return f"LectureTopic {self.default_order}: {self.title}"


class LectureProgress(models.Model):
    session = models.ForeignKey(
        LectureSession,
        on_delete=models.CASCADE,
        related_name='progress_records',
    )
    topic = models.ForeignKey(
        LectureTopic,
        on_delete=models.CASCADE,
        related_name='progress_records',
    )
    order = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lecture Progress"
        verbose_name_plural = "Lecture Progress Records"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "topic"],
                name="unique_progress_per_session_and_topic",
            ),
        ]

    def __str__(self):
        return f'Lecture Progress: Session {self.session.id} - Topic {self.order}'