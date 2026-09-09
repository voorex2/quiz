from django.contrib.auth.models import User
from django.test import TestCase


class AuthenticationTests(TestCase):
	def test_registration_logs_user_in(self):
		response = self.client.post(
			'/register/',
			{
				'username': 'anna',
				'email': 'anna@example.com',
				'password1': 'StrongPassword123!',
				'password2': 'StrongPassword123!',
			},
		)

		self.assertRedirects(response, '/profile/')
		self.assertTrue(response.wsgi_request.user.is_authenticated)
		self.assertTrue(User.objects.filter(username='anna').exists())

	def test_login_and_logout(self):
		User.objects.create_user(username='anna', password='StrongPassword123!')

		login_response = self.client.post(
			'/login/',
			{'username': 'anna', 'password': 'StrongPassword123!'},
		)
		self.assertRedirects(login_response, '/profile/')

		profile_response = self.client.get('/profile/')
		self.assertEqual(profile_response.status_code, 200)
		self.assertContains(profile_response, 'anna')

		logout_response = self.client.get('/logout/')
		self.assertRedirects(logout_response, '/login/')
		self.assertEqual(self.client.get('/profile/').status_code, 302)

	def test_profile_requires_authentication(self):
		response = self.client.get('/profile/')

		self.assertRedirects(response, '/login/?next=/profile/')
