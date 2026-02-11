from django.db import models
from django.db.models import Q

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
    # snapshot for result screen
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    report = models.TextField(blank=True)
    used_tokens = models.PositiveBigIntegerField(default=0)
    # lecture state
    last_report_log_id = models.PositiveBigIntegerField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    can_continue = models.BooleanField(default=False)


    class Meta:
        verbose_name = "Lecture Session"
        verbose_name_plural = "Lecture Sessions"
        ordering = ["lecture_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sub_topic", "lecture_number"],
                name="unique_lecture_number_per_topic",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "sub_topic"]),
            models.Index(fields=["user"]),
            models.Index(fields=["is_finished"]),
            models.Index(fields=["can_continue"]),
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

    class Meta:
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

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
        indexes = [
            models.Index(fields=["sub_topic"]),
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
        indexes = [
            models.Index(fields=["session", "is_completed"]),
            models.Index(fields=["topic"]),
        ]

    def __str__(self):
        return f'Lecture Progress: Session {self.session.id} - Topic {self.topic.title}'
    

class LectureSessionSlice(models.Model):
    session = models.ForeignKey(
        LectureSession,
        on_delete=models.CASCADE,
        related_name='time_slices',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session"],
                condition=Q(ended_at__isnull=True),
                name="lecture_session_one_open_slice_open_only",
            )
        ]
        verbose_name = "Lecture Session Slice"
        verbose_name_plural = "Lecture Session Slices"
        indexes = [
            models.Index(fields=["session", "ended_at"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        to_time = self.ended_at.strftime("%Y-%m-%d %H:%M") if self.ended_at else "OPEN"
        return f'Lecture Session Slice: Session {self.session.id} from {self.started_at:%Y-%m-%d %H:%M} to {to_time}'