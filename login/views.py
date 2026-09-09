from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import RegistrationForm


class UserLoginView(LoginView):
	template_name = 'login/login.html'
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
	return render(request, 'login/profile.html')


def logout_view(request):
	logout(request)
	return redirect('login')
