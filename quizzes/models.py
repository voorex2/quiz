import secrets
import string

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    DEFAULT_LABELS = {name: label for name, label in (
        ('History', _('History')), ('Science', _('Science')),
        ('Programming', _('Programming')), ('Cinema', _('Cinema')),
        ('Geography', _('Geography')), ('General knowledge', _('General knowledge')),
    )}
    name = models.CharField(_('Name'), max_length=80, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return str(self.DEFAULT_LABELS.get(self.name, self.name))


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='quizzes', verbose_name=_('Category'))
    shuffle_answers = models.BooleanField(_('Shuffle answers'), default=True)
    shuffle_questions = models.BooleanField(_('Shuffle questions'), default=False)
    announced = models.BooleanField(default=False, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_quizzes',
    )
    invite_code = models.CharField(max_length=8, unique=True, editable=False)
    is_published = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.invite_code:
            alphabet = string.ascii_uppercase + string.digits
            self.invite_code = ''.join(secrets.choice(alphabet) for _ in range(7))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('quiz_detail', kwargs={'pk': self.pk})


class Question(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = 'text', _('Text')
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
    )
    media_url = models.URLField(blank=True)
    image = models.ImageField(_('Image upload'), upload_to='questions/%Y/%m/', blank=True)
    time_limit = models.PositiveIntegerField(default=30, help_text=_('Time in seconds'))
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order', 'id')

    def __str__(self):
        return self.text[:80]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizLike(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('quiz', 'user'), name='unique_quiz_like_per_user'),
        )

    def __str__(self):
        return f'{self.user} likes {self.quiz}'


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        null=True,
        blank=True,
    )
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    percentage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Quiz attempt')
        verbose_name_plural = _('Quiz attempts')

    def __str__(self):
        return f'{self.user} -> {self.quiz}: {self.score}/{self.total}'


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, null=True, on_delete=models.SET_NULL, related_name='responses')
    question_text = models.TextField()
    is_correct = models.BooleanField(default=False)


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'quiz'), name='unique_favorite')]


class AuthorFollow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'author'), name='unique_author_follow')]


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    weekly = models.BooleanField(_('Receive quiz of the week'), default=False)


class WeeklyQuiz(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, limit_choices_to={'is_published': True, 'is_private': False})
    week = models.DateField(_('Week starting Monday'), unique=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        if self.week and (self.week.weekday() != 0 or self.week > timezone.localdate()):
            raise ValidationError(_('Choose a Monday that is not in the future.'))
        if self.quiz_id and (not self.quiz.is_published or self.quiz.is_private):
            raise ValidationError(_('Choose a public published quiz.'))

    def __str__(self):
        return f'{self.week}: {self.quiz}'


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=[('author', _('New author quiz')), ('weekly', _('Quiz of the week'))])
    event = models.CharField(max_length=80)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')
        constraints = [models.UniqueConstraint(fields=('user', 'event'), name='unique_notification_event')]
