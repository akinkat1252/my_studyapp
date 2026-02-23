from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Max, Q, Sum

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

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def max_total_score(self):
        return self.default_questions * self.max_score_per_question
    
    def __str__(self):
        return f'Exam Type: {self.name} ({self.code})'


class ExamSession(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("evaluating", "Evaluating"),
        ("finished", "Finished"),
        ("aborted", "Aborted"),
    ]

    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    learning_goal = models.ForeignKey(
        'task_management.LearningGoal',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    main_topic = models.ForeignKey(
        'task_management.LearningMainTopic',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    sub_topic = models.ForeignKey(
        'task_management.LearningSubTopic',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.PROTECT,
        related_name='exam_sessions',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    attempt_number = models.PositiveIntegerField()
    current_question_number = models.PositiveIntegerField(default=0)
    max_questions = models.PositiveIntegerField(default=0)
    summary = models.TextField(default='', blank=True)
    rubric_snapshot = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Session'
        verbose_name_plural = 'Exam Sessions'
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(learning_goal__isnull=False, main_topic__isnull=True, sub_topic__isnull=True) |
                    Q(learning_goal__isnull=True, main_topic__isnull=False, sub_topic__isnull=True) |
                    Q(learning_goal__isnull=True, main_topic__isnull=True, sub_topic__isnull=False)
                ),
                name='only_one_exam_target_set',
            ),
            models.UniqueConstraint(
                fields=['user', 'learning_goal', 'exam_type', 'attempt_number'],
                condition=Q(learning_goal__isnull=False),
                name='unique_user-goal_attempt',
            ),
            models.UniqueConstraint(
                fields=['user', 'main_topic', 'exam_type', 'attempt_number'],
                condition=Q(main_topic__isnull=False),
                name='unique_user-main_topic_attempt',
            ),
            models.UniqueConstraint(
                fields=['user', 'sub_topic', 'exam_type', 'attempt_number'],
                condition=Q(sub_topic__isnull=False),
                name='unique_user-sub_topic_attempt',
            ),
        ]
        indexes = [
            models.Index(fields=["user", "learning_goal", "exam_type"]),
            models.Index(fields=["user", "main_topic", "exam_type"]),
            models.Index(fields=["user", "sub_topic", "exam_type"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["exam_type", "created_at"]),
        ]

    def clean(self):
        super().clean()

        if self.exam_type.target_level == "goal" and not self.learning_goal:
            raise ValidationError({
                "learning_goal": "Learning Goal must be set for this exam type."
            })
        if self.exam_type.target_level == "main_topic" and not self.main_topic:
            raise ValidationError({
                "main_topic": "Main Topic must be set for this exam type."
            })
        if self.exam_type.target_level == "sub_topic" and not self.sub_topic:
            raise ValidationError({
                "sub_topic": "Sub Topic must be set for this exam type."
            })


    def save(self, *args, **kwargs):
        is_new = self.pk is None
    
        with transaction.atomic():

            if is_new:

                if self.learning_goal:
                    qs = ExamSession.objects.select_for_update().filter(
                        user=self.user,
                        learning_goal=self.learning_goal,
                        exam_type=self.exam_type,
                    )
                elif self.main_topic:
                    qs = ExamSession.objects.select_for_update().filter(
                        user=self.user,
                        main_topic=self.main_topic,
                        exam_type=self.exam_type,
                    )
                elif self.sub_topic:
                    qs = ExamSession.objects.select_for_update().filter(
                        user=self.user,
                        sub_topic=self.sub_topic,
                        exam_type=self.exam_type,
                    )
                else:
                    raise ValidationError("At least one target (learning_goal, main_topic, sub_topic) must be set.")
            
                # Determine attempt_number
                last_attempt = (
                    qs.aggregate(max_attempt=Max('attempt_number'))['max_attempt'] or 0
                )

                self.attempt_number = last_attempt + 1
                self.max_questions = self.exam_type.default_questions

            self.full_clean()
            super().save(*args, **kwargs)

    @property
    def calculated_total_score(self):
        total = (
            self.questions
            .filter(evaluation__isnull=False)
            .aggregate(total_score=Sum('evaluation__score'))['total_score']
        )
        return total if total is not None else Decimal("0")
    
    @property
    def calculated_max_score(self):
        return (
            Decimal(self.max_questions) * 
            Decimal(self.exam_type.max_score_per_question)
        )

    @property
    def calculated_accuracy_rate(self):
        max_score = self.calculated_max_score
        if max_score == 0:
            return None
        return self.calculated_total_score / max_score


    def __str__(self):
        if self.learning_goal:
            target = f"goal:{self.learning_goal.id}"
        elif self.main_topic:
            target = f"main:{self.main_topic.id}"
        else:
            target = f"sub:{self.sub_topic.id}"

        return f"ExamSession [{self.exam_type.code}] {target} (Attempt {self.attempt_number})"


class ExamQuestion(models.Model):
    STATUS_CHOICES = [
        ("initialized", "Initialized"),
        ("generated", "Generated"),
        ("answered", "Answered"),
        ("evaluated", "Evaluated"),
        ("skipped", "Skipped"),
    ]

    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='questions',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="initialized")
    question_number = models.PositiveIntegerField(default=0)
    question = models.TextField()
    max_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # For MCQ type questions
    choices = models.JSONField(null=True, blank=True)
    correct_answer = models.CharField(max_length=5, null=True, blank=True)
    explanation = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Exam Question'
        verbose_name_plural = 'Exam Questions'
        get_latest_by = "created_at"
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'question_number'],
                name='unique_session-question_number',
            ),
        ]
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["session", "question_number"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        super().clean()

        scoring_method = self.session.exam_type.scoring_method

        if scoring_method == "binary":
            if not self.correct_answer:
                raise ValidationError({
                    "correct_answer": "Correct answer must be set for binary scoring."
                })
            if not self.choices:
                raise ValidationError({
                    "choices": "Choices must be set for binary scoring."
                })
            if not isinstance(self.choices, dict):
                raise ValidationError({"choices": "Choices must be a dictionary."})
            if self.correct_answer not in self.choices:
                raise ValidationError({
                    "correct_answer": "Correct answer must be one of the choices."
                })
            if not self.explanation:
                raise ValidationError({
                    "explanation": "Explanation must be provided for binary scoring."
                })
        else:
            if self.correct_answer or self.choices:
                raise ValidationError({
                    "choices and correct_answer must be empty for non-binary scoring."
                })

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            with transaction.atomic():
                last_number = (
                    ExamQuestion.objects
                    .filter(session=self.session)
                    .select_for_update()
                    .aggregate(max_num=models.Max('question_number'))['max_num'] or 0
                )
                self.question_number = last_number + 1
        self.full_clean()
        super().save(*args, **kwargs)

        # Update current_question_number in ExamSession
        ExamSession.objects.filter(pk=self.session_id).update(
            current_question_number=self.question_number
        )

    def __str__(self):
        return f'Exam Question: {self.session} / No.{self.question_number}'


class ExamAnswer(models.Model):
    question = models.OneToOneField(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name='answer',
    )

    answer = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Answer'
        verbose_name_plural = 'Exam Answers'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Exam Answer: {self.question} (Answer ID:{self.id})'
    

class ExamEvaluation(models.Model):
    question = models.OneToOneField(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name='evaluation',
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )
    rubric_snapshot = models.JSONField(null=True, blank=True)
    detail_scores = models.JSONField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Evaluation'
        verbose_name_plural = 'Exam Evaluations'

    def clean(self):
        super().clean()

        if self.question and self.score is not None:
            if self.score > Decimal(self.question.max_score):
                raise ValidationError({
                    "score": "Score cannot exceed the question's max score."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Exam Evaluation: {self.question} (Score:{self.score})'


class ExamResult(models.Model):
    session = models.OneToOneField(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='result',
    )
    max_score = models.DecimalField(max_digits=6, decimal_places=3)
    # snapshot for result screen
    total_score = models.DecimalField(max_digits=6, decimal_places=3)
    accuracy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("1")),
        ],
    )
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    used_tokens = models.PositiveBigIntegerField(default=0)
    report = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam Result'
        verbose_name_plural = 'Exam Results'
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f'Exam Result: {self.session} (Total Score:{self.total_score})'


class ExamSessionSlice(models.Model):
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='time_slices',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Exam Session Slice'
        verbose_name_plural = 'Exam Session Slices'
        constraints = [
            models.UniqueConstraint(
                fields=['session', ],
                condition=Q(ended_at__isnull=True),
                name="exam_session_one_open_slice_open_only",
            )
        ]
        indexes = [
            models.Index(fields=["session"]),
            models.Index(fields=["started_at"]),
        ]


    def __str__(self):
        to_time = self.ended_at.strftime("%Y-%m-%d %H:%M") if self.ended_at else "OPEN"
        return f'Exam Session Slice: Session {self.session.id} from {self.started_at:%Y-%m-%d %H:%M} to {to_time}'
    