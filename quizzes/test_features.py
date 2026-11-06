from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from .forms import QuestionEditorForm
from .models import (Answer, AttemptAnswer, AuthorFollow, Category, Favorite,
                     Notification, NotificationPreference, Question, Quiz, QuizAttempt, WeeklyQuiz)


class FeatureTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('writer')
        self.reader = get_user_model().objects.create_user('reader')
        self.other = get_user_model().objects.create_user('other')
        self.quiz = Quiz.objects.create(owner=self.owner, title='Public quiz', is_published=True)
        self.question = Question.objects.create(quiz=self.quiz, text='First?')
        self.right = Answer.objects.create(question=self.question, text='Yes', is_correct=True)
        Answer.objects.create(question=self.question, text='No')
        self.client.force_login(self.reader)

    def test_favorites_are_idempotent_private_to_user_and_filterable(self):
        category = Category.objects.create(name='Test category')
        self.quiz.category = category
        self.quiz.save()
        for _ in range(2):
            self.client.post(f'/quizzes/{self.quiz.pk}/favorite/')
        self.assertEqual(Favorite.objects.count(), 1)
        response = self.client.get(f'/quizzes/?favorites=1&category={category.pk}&q=Public')
        self.assertEqual(list(response.context['quizzes']), [self.quiz])
        self.client.force_login(self.other)
        self.assertFalse(self.client.get('/quizzes/?favorites=1').context['quizzes'])
        self.client.force_login(self.reader)
        self.client.post(f'/quizzes/{self.quiz.pk}/favorite/', {'remove': '1'})
        self.assertFalse(Favorite.objects.exists())

    def test_favorites_reject_get_and_private_quizzes(self):
        self.assertEqual(self.client.get(f'/quizzes/{self.quiz.pk}/favorite/').status_code, 405)
        self.quiz.is_private = True
        self.quiz.save()
        self.assertEqual(self.client.post(f'/quizzes/{self.quiz.pk}/favorite/').status_code, 404)

    def test_category_filter_excludes_other_categories_and_private_quizzes(self):
        category = Category.objects.create(name='New category')
        self.quiz.category = category
        self.quiz.save()
        Quiz.objects.create(owner=self.owner, title='Other public', is_published=True)
        Quiz.objects.create(owner=self.owner, title='Secret', is_published=True, is_private=True, category=category)
        response = self.client.get(f'/quizzes/?category={category.pk}')
        self.assertEqual(list(response.context['quizzes']), [self.quiz])

    def test_shuffle_preserves_answer_ids_and_grading(self):
        second = Question.objects.create(quiz=self.quiz, text='Second?', order=2)
        second_right = Answer.objects.create(question=second, text='Correct', is_correct=True)
        Answer.objects.create(question=second, text='Incorrect')
        self.quiz.shuffle_questions = True
        self.quiz.save()
        with patch('quizzes.views.random.shuffle', side_effect=lambda values: values.reverse()) as shuffle:
            response = self.client.get(f'/quizzes/{self.quiz.pk}/take/')
        self.assertEqual(shuffle.call_count, 3)
        self.assertEqual(response.context['questions'][0], second)
        self.assertEqual(response.context['questions'][1].display_answers[-1], self.right)
        self.client.post(f'/quizzes/{self.quiz.pk}/take/', {
            f'question_{self.question.pk}': self.right.pk, f'question_{second.pk}': second_right.pk})
        self.assertEqual(QuizAttempt.objects.get().score, 2)
        self.assertEqual(AttemptAnswer.objects.filter(is_correct=True).count(), 2)

    def test_disabled_shuffle_does_not_reorder(self):
        self.quiz.shuffle_answers = False
        self.quiz.save()
        with patch('quizzes.views.random.shuffle') as shuffle:
            self.client.get(f'/quizzes/{self.quiz.pk}/take/')
        shuffle.assert_not_called()

    def test_statistics_include_skips_and_only_owner_data(self):
        self.client.post(f'/quizzes/{self.quiz.pk}/take/', {f'question_{self.question.pk}': self.right.pk})
        self.client.post(f'/quizzes/{self.quiz.pk}/take/', {f'question_{self.question.pk}': 'invalid'})
        other_quiz = Quiz.objects.create(owner=self.other, title='Other stats', is_published=True)
        QuizAttempt.objects.create(quiz=other_quiz, score=1, total=1, percentage=100)
        self.client.force_login(self.owner)
        response = self.client.get('/quizzes/statistics/')
        self.assertEqual(response.context['summary'], {'attempt_count': 2, 'average': 50})
        self.assertEqual(response.context['questions'][0].error_rate, 50)
        self.assertNotContains(response, 'Other stats')
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get('/quizzes/statistics/').context['summary']['attempt_count'], 0)

    def test_notifications_follow_publish_once_and_unfollow(self):
        self.client.post(f'/quizzes/authors/{self.owner.pk}/follow/')
        draft = Quiz.objects.create(owner=self.owner, title='Draft')
        self.assertFalse(Notification.objects.exists())
        draft.is_published = True
        draft.save()
        draft.title = 'Updated'
        draft.save()
        draft.is_published = False
        draft.save()
        draft.is_published = True
        draft.save()
        self.assertEqual(Notification.objects.filter(user=self.reader).count(), 1)
        self.client.post(f'/quizzes/authors/{self.owner.pk}/follow/', {'remove': '1'})
        Quiz.objects.create(owner=self.owner, title='Later', is_published=True)
        self.assertEqual(Notification.objects.count(), 1)

    def test_private_quizzes_do_not_notify_and_hidden_items_do_not_leak(self):
        AuthorFollow.objects.create(user=self.reader, author=self.owner)
        secret = Quiz.objects.create(owner=self.owner, title='Private title', is_published=True, is_private=True)
        self.assertFalse(Notification.objects.exists())
        secret.is_private = False
        secret.save()
        self.assertEqual(Notification.objects.count(), 1)
        secret.is_private = True
        secret.save()
        self.assertNotContains(self.client.get('/quizzes/notifications/'), 'Private title')
        self.assertEqual(self.client.get(f'/quizzes/{secret.pk}/rating/').status_code, 302)

    def test_weekly_notifications_opt_in_and_read_isolation(self):
        self.client.post('/quizzes/notifications/', {'action': 'preferences', 'weekly': 'on'})
        week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        weekly = WeeklyQuiz(quiz=self.quiz, week=week)
        weekly.full_clean()
        weekly.save()
        weekly.save()
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().user, self.reader)
        Notification.objects.create(user=self.other, quiz=self.quiz, kind='weekly', event='other')
        self.client.post('/quizzes/notifications/', {'action': 'read'})
        self.assertTrue(Notification.objects.get(user=self.reader).is_read)
        self.assertFalse(Notification.objects.get(user=self.other).is_read)
        self.client.post('/quizzes/notifications/', {'action': 'preferences'})
        self.assertFalse(NotificationPreference.objects.get(user=self.reader).weekly)

    def test_weekly_rejects_private_and_future_dates(self):
        next_monday = timezone.localdate() + timedelta(days=7 - timezone.localdate().weekday())
        with self.assertRaises(ValidationError):
            WeeklyQuiz(quiz=self.quiz, week=next_monday).full_clean()
        self.quiz.is_private = True
        self.quiz.save()
        with self.assertRaises(ValidationError):
            WeeklyQuiz(quiz=self.quiz, week=next_monday - timedelta(days=7)).full_clean()

    def editor_data(self):
        return {'title': self.quiz.title, 'is_published': 'on',
                'questions-TOTAL_FORMS': '1', 'questions-INITIAL_FORMS': '1',
                'questions-0-question_id': str(self.question.pk),
                'questions-0-text': 'Updated question', 'questions-0-question_type': 'image',
                'questions-0-time_limit': '30', 'questions-0-answer_1': 'Yes',
                'questions-0-answer_2': 'No', 'questions-0-correct_answer': '1'}

    def test_upload_preserve_render_and_remove_image(self):
        buffer = BytesIO()
        Image.new('RGB', (4, 4), 'red').save(buffer, format='PNG')
        self.client.force_login(self.owner)
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            data = self.editor_data()
            data['questions-0-image'] = SimpleUploadedFile('picture.png', buffer.getvalue(), content_type='image/png')
            response = self.client.post(f'/quizzes/{self.quiz.pk}/edit/', data)
            self.assertEqual(response.status_code, 302)
            self.question.refresh_from_db()
            image_name = self.question.image.name
            self.assertTrue(image_name)
            self.assertContains(self.client.get(f'/quizzes/{self.quiz.pk}/take/'), self.question.image.url)
            self.client.post(f'/quizzes/{self.quiz.pk}/edit/', self.editor_data())
            self.question.refresh_from_db()
            self.assertEqual(self.question.image.name, image_name)
            data = self.editor_data()
            data['questions-0-remove_image'] = 'on'
            self.client.post(f'/quizzes/{self.quiz.pk}/edit/', data)
            self.question.refresh_from_db()
            self.assertFalse(self.question.image)

    def test_bad_upload_and_foreign_question_id_are_rejected(self):
        form = QuestionEditorForm({}, {'image': SimpleUploadedFile('bad.png', b'not an image')})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
        foreign = Question.objects.create(quiz=Quiz.objects.create(owner=self.other, title='Other'), text='Foreign')
        self.client.force_login(self.owner)
        data = self.editor_data()
        data['questions-0-question_id'] = str(foreign.pk)
        self.assertEqual(self.client.post(f'/quizzes/{self.quiz.pk}/edit/', data).status_code, 404)
        self.question.refresh_from_db()
        self.assertEqual(self.question.text, 'First?')

    def test_feature_pages_render_and_require_login(self):
        for path in ('/quizzes/statistics/', '/quizzes/notifications/', '/quizzes/?favorites=1'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(f'/quizzes/{self.quiz.pk}/edit/'), 'multipart/form-data')
        self.client.logout()
        for path in ('/quizzes/statistics/', '/quizzes/notifications/', '/quizzes/?favorites=1'):
            self.assertEqual(self.client.get(path).status_code, 302)
