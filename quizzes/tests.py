from django.contrib.auth.models import User
from django.test import TestCase

from .models import Answer, Question, Quiz


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

    def test_owner_can_add_question_and_answers(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=user, title='Моя вікторина', is_published=True)
        self.client.force_login(user)

        response = self.client.post(
            f'/quizzes/{quiz.pk}/questions/add/',
            {
                'text': 'Скільки буде 2 + 2?',
                'question_type': 'text',
                'media_url': '',
                'time_limit': 30,
                'order': 1,
                'answers-TOTAL_FORMS': 4,
                'answers-INITIAL_FORMS': 0,
                'answers-MIN_NUM_FORMS': 2,
                'answers-MAX_NUM_FORMS': 1000,
                'answers-0-text': '3',
                'answers-0-is_correct': '',
                'answers-1-text': '4',
                'answers-1-is_correct': 'on',
                'answers-2-text': '5',
                'answers-2-is_correct': '',
                'answers-3-text': '',
                'answers-3-is_correct': '',
            },
        )

        self.assertRedirects(response, f'/quizzes/{quiz.pk}/')
        question = Question.objects.get(quiz=quiz)
        self.assertEqual(question.answers.count(), 3)
        self.assertTrue(question.answers.get(text='4').is_correct)

    def test_user_can_take_quiz_and_get_score(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=user, title='Математика', is_published=True)
        question = Question.objects.create(quiz=quiz, text='2 + 2?')
        correct = Answer.objects.create(question=question, text='4', is_correct=True)
        Answer.objects.create(question=question, text='5')

        response = self.client.post(
            f'/quizzes/{quiz.pk}/take/',
            {f'question_{question.pk}': correct.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/quizzes/{quiz.pk}/result/')
        result_response = self.client.get(f'/quizzes/{quiz.pk}/result/')
        self.assertContains(result_response, '1 / 1')

    def test_only_owner_can_add_question(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        other_user = User.objects.create_user(username='other', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Закрита вікторина', is_published=True)
        self.client.force_login(other_user)

        response = self.client.get(f'/quizzes/{quiz.pk}/questions/add/')

        self.assertEqual(response.status_code, 404)

    def test_quiz_pages_follow_selected_english_language(self):
        response = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/quizzes/'})

        self.assertRedirects(response, '/quizzes/')
        response = self.client.get('/quizzes/')

        self.assertContains(response, 'Choose your game')
        self.assertContains(response, 'Quizzes')

    def test_quiz_detail_uses_english_labels(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=user, title='Science', is_published=True)
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})

        response = self.client.get(f'/quizzes/{quiz.pk}/')

        self.assertContains(response, 'Author')
        self.assertContains(response, 'This quiz has no questions yet.')
