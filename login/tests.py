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

	def test_home_can_be_viewed_in_english(self):
		response = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})

		self.assertRedirects(response, '/')
		response = self.client.get('/')
		self.assertContains(response, 'Your next great quiz starts here.')
		self.assertContains(response, 'Log in')

	def test_user_can_change_username(self):
		user = User.objects.create_user(username='anna', password='StrongPassword123!')
		self.client.force_login(user)

		response = self.client.post('/profile/username/', {'username': 'olena'})

		self.assertRedirects(response, '/profile/')
		user.refresh_from_db()
		self.assertEqual(user.username, 'olena')

	def test_user_can_change_password_with_old_password(self):
		user = User.objects.create_user(username='anna', password='StrongPassword123!')
		self.client.force_login(user)

		response = self.client.post(
			'/profile/password/',
			{
				'old_password': 'StrongPassword123!',
				'new_password1': 'NewStrongPassword456!',
				'new_password2': 'NewStrongPassword456!',
			},
		)

		self.assertRedirects(response, '/profile/')
		user.refresh_from_db()
		self.assertTrue(user.check_password('NewStrongPassword456!'))

	def test_password_change_rejects_wrong_old_password(self):
		user = User.objects.create_user(username='anna', password='StrongPassword123!')
		self.client.force_login(user)

		response = self.client.post(
			'/profile/password/',
			{
				'old_password': 'wrong-password',
				'new_password1': 'NewStrongPassword456!',
				'new_password2': 'NewStrongPassword456!',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'old_password')
		self.assertTrue(user.check_password('StrongPassword123!'))
