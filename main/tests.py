from django.test import TestCase


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Онлайн-вікторина')

    def test_home_links_to_quizzes(self):
        response = self.client.get('/')

        self.assertContains(response, 'href="/quizzes/"')
        self.assertContains(response, 'href="/register/"')

    def test_authenticated_home_links_to_quiz_creation(self):
        from django.contrib.auth.models import User

        user = User.objects.create_user(username='author', password='StrongPassword123!')
        self.client.force_login(user)

        response = self.client.get('/')

        self.assertContains(response, 'href="/quizzes/create/"')
