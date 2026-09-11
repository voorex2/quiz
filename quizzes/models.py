import uuid

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
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Вікторина'
        verbose_name_plural = 'Вікторини'

    def __str__(self):
        return self.title

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
