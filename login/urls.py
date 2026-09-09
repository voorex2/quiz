from django.urls import path

from .views import (
	UserLoginView,
	change_password_view,
	change_username_view,
	logout_view,
	profile_view,
	register_view,
)


urlpatterns = [
	path('login/', UserLoginView.as_view(), name='login'),
	path('register/', register_view, name='register'),
	path('logout/', logout_view, name='logout'),
	path('profile/', profile_view, name='profile'),
	path('profile/username/', change_username_view, name='change_username'),
	path('profile/password/', change_password_view, name='change_password'),
]
