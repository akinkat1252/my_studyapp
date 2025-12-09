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
    lecture_count = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True)
    total_count = models.PositiveBigIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Lecture Session: {self.user.username} - {self.sub_topic.title}'
    

class LectureLog(models.Model):
    ROLE_CHOICES = [
        ('ai', 'AI'),
        ('user', 'USER'),
        ('master', 'MASTER'),
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
