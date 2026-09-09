from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import (
	RegistrationForm,
	UkrainianAuthenticationForm,
	UserPasswordChangeForm,
	UsernameChangeForm,
)


class UserLoginView(LoginView):
	template_name = 'login/login.html'
	authentication_form = UkrainianAuthenticationForm
	redirect_authenticated_user = True


def register_view(request):
	if request.user.is_authenticated:
		return redirect('profile')

	form = RegistrationForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user)
		return redirect('profile')

	return render(request, 'login/register.html', {'form': form})


@login_required
def profile_view(request):
	username_form = UsernameChangeForm(instance=request.user)
	password_form = UserPasswordChangeForm(request.user)
	return render(
		request,
		'login/profile.html',
		{'username_form': username_form, 'password_form': password_form},
	)


@login_required
def change_username_view(request):
	if request.method != 'POST':
		return redirect('profile')

	username_form = UsernameChangeForm(request.POST, instance=request.user)
	if username_form.is_valid():
		username_form.save()
		return redirect('profile')

	return render(
		request,
		'login/profile.html',
		{
			'username_form': username_form,
			'password_form': UserPasswordChangeForm(request.user),
		},
	)


@login_required
def change_password_view(request):
	if request.method != 'POST':
		return redirect('profile')

	password_form = UserPasswordChangeForm(request.user, request.POST)
	if password_form.is_valid():
		user = password_form.save()
		update_session_auth_hash(request, user)
		return redirect('profile')

	return render(
		request,
		'login/profile.html',
		{
			'username_form': UsernameChangeForm(instance=request.user),
			'password_form': password_form,
		},
	)


def logout_view(request):
	logout(request)
	return redirect('login')
