from django.contrib.auth.models import User
from django.test import TestCase

from .models import Answer, Question, Quiz, QuizLike


class QuizTests(TestCase):
    def test_published_quiz_is_shown_in_list(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        Quiz.objects.create(owner=user, title='Загальна вікторина', is_published=True)

        response = self.client.get('/quizzes/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Загальна вікторина')

    def test_quiz_list_can_search_by_title(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        Quiz.objects.create(owner=user, title='Математика', is_published=True)
        Quiz.objects.create(owner=user, title='Історія', is_published=True)

        response = self.client.get('/quizzes/?q=матем')

        self.assertContains(response, 'Математика')
        self.assertNotContains(response, 'Історія')

    def test_my_quizzes_filter_shows_only_current_user_quizzes(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        other_user = User.objects.create_user(username='other', password='StrongPassword123!')
        Quiz.objects.create(owner=owner, title='Моя чернетка')
        Quiz.objects.create(owner=other_user, title='Чужа вікторина', is_published=True)
        self.client.force_login(owner)

        response = self.client.get('/quizzes/?mine=1')

        self.assertContains(response, 'Моя чернетка')
        self.assertNotContains(response, 'Чужа вікторина')

    def test_owner_can_delete_quiz(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Видалити мене')
        self.client.force_login(owner)

        response = self.client.post(f'/quizzes/{quiz.pk}/delete/')

        self.assertRedirects(response, '/quizzes/')
        self.assertFalse(Quiz.objects.filter(pk=quiz.pk).exists())

    def test_other_user_cannot_delete_quiz(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        visitor = User.objects.create_user(username='visitor', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Не видаляти')
        self.client.force_login(visitor)

        response = self.client.post(f'/quizzes/{quiz.pk}/delete/')

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Quiz.objects.filter(pk=quiz.pk).exists())

    def test_user_can_create_quiz(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        self.client.force_login(user)

        response = self.client.post(
            '/quizzes/create/',
            {'title': 'Моя вікторина', 'description': 'Опис', 'is_published': True},
        )

        self.assertRedirects(response, '/quizzes/1/')
        self.assertTrue(Quiz.objects.filter(owner=user, title='Моя вікторина').exists())

    def test_user_can_create_quiz_with_questions(self):
        user = User.objects.create_user(username='author', password='StrongPassword123!')
        self.client.force_login(user)

        response = self.client.post(
            '/quizzes/create/',
            {
                'title': 'Моя вікторина',
                'description': 'Опис',
                'is_published': True,
                'questions-TOTAL_FORMS': 1,
                'questions-INITIAL_FORMS': 0,
                'questions-MIN_NUM_FORMS': 0,
                'questions-MAX_NUM_FORMS': 1000,
                'questions-0-text': 'Скільки буде 2 + 2?',
                'questions-0-question_type': 'text',
                'questions-0-media_url': '',
                'questions-0-time_limit': 30,
                'questions-0-answer_1': '3',
                'questions-0-answer_2': '4',
                'questions-0-answer_3': '5',
                'questions-0-answer_4': '',
                'questions-0-correct_answer': '2',
            },
        )

        self.assertRedirects(response, '/quizzes/1/')
        quiz = Quiz.objects.get(title='Моя вікторина')
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

    def test_user_can_like_quiz_only_once(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        user = User.objects.create_user(username='player', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Популярна', is_published=True)
        self.client.force_login(user)

        self.client.post(f'/quizzes/{quiz.pk}/like/')
        self.client.post(f'/quizzes/{quiz.pk}/like/')

        self.assertEqual(QuizLike.objects.filter(quiz=quiz, user=user).count(), 1)

    def test_private_quiz_requires_invite_code(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Приватна', is_published=True, is_private=True)

        response = self.client.get(f'/quizzes/{quiz.pk}/')
        self.assertRedirects(response, '/quizzes/join/')

        response = self.client.post('/quizzes/join/', {'invite_code': quiz.invite_code.lower()})
        self.assertRedirects(response, f'/quizzes/{quiz.pk}/')
        self.assertEqual(self.client.get(f'/quizzes/{quiz.pk}/').status_code, 200)
        self.assertEqual(len(quiz.invite_code), 7)

    def test_owner_can_open_unpublished_quiz(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Чернетка', is_published=False)
        self.client.force_login(owner)

        response = self.client.get(f'/quizzes/{quiz.pk}/')

        self.assertEqual(response.status_code, 200)

    def test_other_users_cannot_open_unpublished_quiz(self):
        owner = User.objects.create_user(username='owner', password='StrongPassword123!')
        visitor = User.objects.create_user(username='visitor', password='StrongPassword123!')
        quiz = Quiz.objects.create(owner=owner, title='Чернетка', is_published=False)
        self.client.force_login(visitor)

        response = self.client.get(f'/quizzes/{quiz.pk}/')

        self.assertEqual(response.status_code, 404)
