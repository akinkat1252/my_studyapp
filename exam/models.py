from django.core.exceptions import ValidationError
from django.db import models, transaction

from config import settings_common


# Create your models here.
class ExamType(models.Model):
    TARGET_CHOICES = [
        ("goal", "Learning Goal"),
        ("main_topic", "Main Topic"),
        ("sub_topic", "Sub Topic"),
    ]
    FLOW_CHOICES = [
        ("per_question", "Per Question"),
        ("batch", "Batch Evaluation"),
    ]
    SCORING_METHOD_CHOICES = [
        ("binary", "Binary (Correct/Incorrect)"),
        ("rubric", "Rubric Based"),
        ("rubric_heavy", "Advanced Rubric"),
    ]

    code = models.CharField(max_length=30, unique=True)
    name= models.CharField(max_length=100)

    target_level = models.CharField(max_length=20, choices=TARGET_CHOICES)
    flow_type = models.CharField(max_length=20, choices=FLOW_CHOICES)
    scoring_method = models.CharField(max_length=20, choices=SCORING_METHOD_CHOICES)

    default_questions = models.PositiveIntegerField()
    max_score_per_question = models.PositiveIntegerField()

    allow_post_chat = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def max_total_score(self):
        return self.default_questions * self.max_score_per_question
    
    def __str__(self):
        return f'Exam Type: {self.name} ({self.code})'


class ExamSession(models.Model):
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
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.PROTECT,
        related_name='exam_sessions',
    )

    attempt_number = models.PositiveIntegerField(default=0)
    current_question_number = models.PositiveIntegerField(default=0)
    max_questions = models.PositiveIntegerField(default=0)
    summary = models.TextField(default='', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Session'
        verbose_name_plural = 'Exam Sessions'

    def clean(self):
        target_level = self.exam_type.target_level

        if target_level == "goal" and not self.learning_goal:
            raise ValidationError("Goal exam must link to learning_goal.")

        if target_level == "main_topic" and not self.main_topic:
            raise ValidationError("Main Topic exam must link to main_topic.")

        if target_level == "sub_topic" and not self.sub_topic:
            raise ValidationError("Sub Topic exam must link to sub_topic.")

    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.pk is None:
            # Decide the number of questions when creating the first one
            self.max_questions = self.exam_type.default_questions

            # Determine attempt_number
            with transaction.atomic():
                last_attempt = (
                    ExamSession.objects
                    .select_for_update()
                    .filter(
                        user=self.user,
                        learning_goal=self.learning_goal,
                        main_topic=self.main_topic,
                        sub_topic=self.sub_topic,
                        exam_type=self.exam_type,
                    )
                    .aggregate(max_attempt=models.Max('attempt_number'))['max_attempt'] or 0
                )
                self.attempt_number = last_attempt + 1
        super().save(*args, **kwargs)

    def __str__(self):
        target = self.learning_goal or self.main_topic or self.sub_topic
        return f'Exam Session: [{self.exam_type.code}] {target} (Attempt {self.attempt_number})'
    

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


class ExamResult(models.Model):
    session = models.OneToOneField(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='result',
    )

    total_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)
    accuracy_rate = models.FloatField(null=True, blank=True)
    # snapshot for result screen
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    used_tokens = models.PositiveBigIntegerField(default=0)
    report = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Result'
        verbose_name_plural = 'Exam Results'

    def __str__(self):
        return f'Exam Result: {self.session} (Total Score:{self.total_score}/)'
