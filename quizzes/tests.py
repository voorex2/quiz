from django.contrib.auth.models import User
from django.test import TestCase

from .models import Quiz


class QuizTests(TestCase):
    def test_published_quiz_is_shown_in_list(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        Quiz.objects.create(owner=user, title='Загальна вікторина', is_published=True)

        response = self.client.get('/quizzes/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Загальна вікторина')

    def test_user_can_create_quiz(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        self.client.force_login(user)

        response = self.client.post(
            '/quizzes/create/',
            {'title': 'Моя вікторина', 'description': 'Опис', 'is_published': True},
        )

        self.assertRedirects(response, '/quizzes/1/')
        self.assertTrue(Quiz.objects.filter(owner=user, title='Моя вікторина').exists())
