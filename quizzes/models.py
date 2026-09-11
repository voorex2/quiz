import secrets
import string

from django.conf import settings
from django.db import models
from django.urls import reverse


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
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
        verbose_name = 'Вікторина'
        verbose_name_plural = 'Вікторини'

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
        TEXT = 'text', 'Текст'
        IMAGE = 'image', 'Зображення'
        VIDEO = 'video', 'Відео'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
    )
    media_url = models.URLField(blank=True)
    time_limit = models.PositiveIntegerField(default=30, help_text='Час у секундах')
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
