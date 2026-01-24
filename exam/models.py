from django.core.exceptions import ValidationError
from django.db import models, transaction

from config import settings_common


# Create your models here.
class ExamSession(models.Model):
    FORMAT_CHOICES = [
        ('mcq', 'MCQ'),  # Multiple choice Quiz
        ('wt', 'WT'),  # Written Task
        ('ct', 'CT'),  # Conprehensive Test
    ]
    QUESTION_DEFAULTS = {
        'mcq': 10,
        'wt': 1,
        'ct': 3,
    }

    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # Must be linked to a learning goal, main topic, or sub topic.
    learning_goal = models.ForeignKey(
        'task_management.LearningGoal',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='exam_sessions',
    )
    main_topic = models.ForeignKey(
        'task_management.LearningMainTopic',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='exam_sessions',
    )
    sub_topic = models.ForeignKey(
        'task_management.LearningSubTopic',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='exam_sessions',
    )

    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    attempt_number = models.PositiveIntegerField(default=0)
    current_question_number = models.PositiveIntegerField(default=0)
    max_questions = models.PositiveIntegerField(default=0)
    summary = models.TextField(default='', blank=True)
    used_tokens = models.PositiveBigIntegerField(default=0)
    total_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Session'
        verbose_name_plural = 'Exam Sessions'
        constraints = [
            # # CT → must be linked to learning_goal
            models.UniqueConstraint(
                fields=['user', 'learning_goal', 'attempt_number'],
                condition=models.Q(format='ct', learning_goal__isnull=False),
                name='unique_ct_attempt_per_goal',
            ),

            # MCQ / WT for main_topic
            models.UniqueConstraint(
                fields=['user', 'main_topic', 'attempt_number'],
                condition=models.Q(format='mcq', main_topic__isnull=False),
                name='unique_mcq_attempt_per_main_topic',
            ),
            models.UniqueConstraint(
                fields=['user', 'main_topic', 'attempt_number'],
                condition=models.Q(format='wt', main_topic__isnull=False),
                name='unique_wt_attempt_per_main_topic',
            ),

            # MCQ / WT for sub_topic
            models.UniqueConstraint(
                fields=['user', 'sub_topic', 'attempt_number'],
                condition=models.Q(format='mcq', sub_topic__isnull=False),
                name='unique_mcq_attempt_per_sub_topic',
            ),
            models.UniqueConstraint(
                fields=['user', 'sub_topic', 'attempt_number'],
                condition=models.Q(format='wt', sub_topic__isnull=False),
                name='unique_wt_attempt_per_sub_topic',
            ),
        ]

    def clean(self):
        # MCQ / WT must have either main_topic or sub_topic (but not both)
        if self.format in ('mcq', 'wt'):
            if bool(self.main_topic) == bool(self.sub_topic):
                raise ValidationError('Please specify either main_topic or sub_topic, not both.')
            if self.learning_goal:
                raise ValidationError('MCQ/WT must not be linked to a learning goal.')
        # CT must link ONLY to learning_goal
        if self.format == 'ct':
            if not self.learning_goal or self.main_topic or self.sub_topic:
                raise ValidationError('CT format must be linked only to a learning goal.')

    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.pk is None:
            # Decide the number of questions when creating the first one
            self.max_questions = self.QUESTION_DEFAULTS.get(self.format, 0)
        super().save(*args, **kwargs)

    def recalculation_used_tokens(self):
        log_tokens = self.logs.aggregate(total=models.Sum('token_count'))['total'] or 0
        eval_tokens = ExamEvaluation.objects.filter(
            exam_log__session=self
        ).aggregate(total=models.Sum('token_count'))['total'] or 0

        self.used_tokens = log_tokens + eval_tokens
        self.save(update_fields=['used_tokens'])

    def __str__(self):
        topic_label = None
        if self.learning_goal:
            topic_label = f'{self.learning_goal.title}'
        elif self.main_topic:
            topic_label = f'{self.main_topic.title}'
        elif self.sub_topic:
            topic_label = f'{self.sub_topic.title}'
        else:
            topic_label = 'No Topic'
        return f'Exam Session: [{self.get_format_display()}] {topic_label} (Attempt {self.attempt_number})'
    

class ExamLog(models.Model):
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    question_number = models.PositiveIntegerField(default=0)
    question = models.TextField(default='')
    answer = models.TextField(blank=True)
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Log'
        verbose_name_plural = 'Exam Logs'
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'question_number'],
                name='unique_session-question_number',
            ),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            with transaction.atomic():
                last_number = (
                    ExamLog.objects
                    .select_for_update()
                    .filter(session=self.session)
                    .aggregate(max_num=models.Max('question_number'))['max_num'] or 0
                )
                self.question_number = last_number + 1
        super().save(*args, **kwargs)

        if is_new:
            self.session.current_question_number = self.question_number
            self.session.save(update_fields=['current_question_number'])

    def __str__(self):
        return f'Exam Log: {self.session} / No.{self.question_number}'
    

class ExamEvaluation(models.Model):
    exam_log = models.OneToOneField(
        ExamLog,
        on_delete=models.CASCADE,
        related_name='evaluation',
    )
    score = models.FloatField(default=0)
    feedback = models.TextField(default='')
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Evaluation'
        verbose_name_plural = 'Exam Evaluations'
        
    def __str__(self):
        return f'Exam Evaluation: {self.exam_log} (Score:{self.score})'
