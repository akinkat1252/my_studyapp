from django.core.exceptions import ValidationError
from django.db import models

from config import settings_common


# Create your models here.
class StudySession(models.Model):
    SESSION_TYPE_CHOICES = [
        ('lec', 'Lecture'),
        ('test', 'Test'),
        ('review', 'Review'),
    ]

    user = models.ForeignKey(settings_common.AUTH_USER_MODEL, on_delete=models.CASCADE)
    learning_goal = models.ForeignKey(
        'task_management.LearningGoal',
        on_delete=models.CASCADE,
        related_name='study_sessions'
    )
    main_topic = models.ForeignKey(
        'task_management.LearningMainTopic',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='study_sessions',
    )
    sub_topic = models.ForeignKey(
        'task_management.LearningSubTopic',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='study_sessions',
    )
    lecture_session = models.OneToOneField(
        'lecture.LectureSession',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='study_sessions',
    )
    exam_session = models.OneToOneField(
        'exam.ExamSession',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='study_sessions'
    )
    session_type = models.CharField(max_length=10, choices=SESSION_TYPE_CHOICES)
    total_score = models.FloatField(default=0)
    note = models.TextField(blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    time_spent = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = 'Study Session'
        verbose_name_plural = 'Study Sessions'

    def clean(self):
        if self.session_type == 'lec':
            if not self.lecture_session:
                raise ValidationError("Lecture type requires lecture_session.")
            if self.exam_session:
                raise ValidationError("Lecture type must not have exam_session.")

        if self.session_type == 'test':
            if not self.exam_session:
                raise ValidationError("Test type requires exam_session.")
            if self.lecture_session:
                raise ValidationError("Test type must not have lecture_session.")

    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.pk:
            old = StudySession.objects.get(pk=self.pk)
            old_end_time = old.end_time if old else None
        else:
            old = None
            old_end_time = None

        if self.end_time and (not old_end_time or self.end_time != old_end_time):
            duration = self.end_time - self.start_time
            self.time_spent = round(duration.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Study Session: [{self.start_time:%Y-%m-%d %H:%M}] {self.user.username} - {self.session_type}'
