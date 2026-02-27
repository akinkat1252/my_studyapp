from django.db import models

from config import settings_common


# Create your models here.
class Category(models.Model):
    # Set when users create their own categories.
    owner = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='own_categories'
    )
    name = models.CharField(max_length=100)
    is_global = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["is_global"]),
        ]

    def __str__(self):
        return self.name
    

# Intermediate model for ManyToMany relationship between CustomUser and Category.
class UserInterestCategory(models.Model):
    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_interest_categories'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_users'
    )

    class Meta:
        verbose_name = 'User Interest Category'
        verbose_name_plural = 'User Interest Categories'
        constraints = [
            models.UniqueConstraint(fields=['user', 'category'], name='unique_user_category')
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"


# A rough draft model for creating learning goals.
class DraftLearningGoal(models.Model):
    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='draft_learning_goals'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='draft_learning_goals'
    )
    title = models.CharField(max_length=200)
    current_level = models.TextField(blank=True)
    target_level = models.TextField(blank=True)
    description = models.TextField(blank=True)

    raw_generated_data = models.JSONField(blank=True, null=True)
    is_finalized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Draft Learning Goal'
        verbose_name_plural = 'Draft Learning Goals'
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_finalized"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f'DraftLearningGoal: {self.title} by {self.user.username}'
    

# The finalized learning goal model.
class LearningGoal(models.Model):
    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_goals'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='learning_goals'
    )
    draft = models.OneToOneField(
        DraftLearningGoal,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='final_learning_goal'
    )
    title = models.CharField(max_length=200)
    current_level = models.TextField(blank=True)
    target_level = models.TextField(blank=True)
    rubric_schema = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Learning Goal'
        verbose_name_plural = 'Learning Goals'
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["category"]),
            models.Index(fields=["created_at"]),
        ]

    # Obtain the total study time for each learning goal
    @property
    def actual_study_time(self):
        return (
            self.study_sessions
            .aggregate(total=models.Sum('time_spent'))['total'] or 0
        )

    def __str__(self):
        return f'LearningGoal: {self.title} by {self.user.username}'


# Main topics under a learning goal.
class LearningMainTopic(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings_common.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_main_topics'
    )
    learning_goal = models.ForeignKey(
        LearningGoal,
        on_delete=models.CASCADE,
        related_name='main_topics'
    )
    title = models.CharField(max_length=200)
    rubric_schema = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Learning Main Topic'
        verbose_name_plural = 'Learning Main Topics'
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["learning_goal"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f'MainTopic: {self.title} for {self.learning_goal.title}'
    

# Subtopics under a main topic.
class LearningSubTopic(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    main_topic = models.ForeignKey(
        LearningMainTopic,
        on_delete=models.CASCADE,
        related_name='sub_topics'
    )
    title = models.CharField(max_length=200)
    rubric_schema = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Learning Sub Topic'
        verbose_name_plural = 'Learning Sub Topics'
        indexes = [
            models.Index(fields=["main_topic"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f'SubTopic: {self.title} for {self.main_topic.title}'
