from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.utils.translation import get_language


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['username'].label = 'Username'
            self.fields['email'].label = 'Email address'
            self.fields['password1'].label = 'Password'
            self.fields['password2'].label = 'Password confirmation'
            self.fields['username'].help_text = 'Up to 150 characters. Letters, digits and @/./+/-/_ only.'
            self.fields['password1'].help_text = 'Your password must contain at least 8 characters and not be too simple.'
            self.fields['password2'].help_text = 'Enter the same password again for verification.'
        else:
            self.fields['username'].label = 'Нікнейм'
            self.fields['email'].label = 'Електронна пошта'
            self.fields['password1'].label = 'Пароль'
            self.fields['password2'].label = 'Підтвердження пароля'
            self.fields['username'].help_text = 'До 150 символів. Лише літери, цифри та символи @/./+/-/_.'
            self.fields['password1'].help_text = 'Пароль має містити щонайменше 8 символів і не бути надто простим.'
            self.fields['password2'].help_text = 'Введіть пароль ще раз для підтвердження.'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UsernameChangeForm(forms.ModelForm):
    username = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username' if get_language() == 'en' else 'Нікнейм'

    class Meta:
        model = User
        fields = ('username',)


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['old_password'].label = 'Current password'
            self.fields['new_password1'].label = 'New password'
            self.fields['new_password2'].label = 'New password confirmation'
            self.fields['new_password1'].help_text = 'Your password must contain at least 8 characters and not be too simple.'
            self.fields['new_password2'].help_text = 'Enter the new password again for verification.'
        else:
            self.fields['old_password'].label = 'Поточний пароль'
            self.fields['new_password1'].label = 'Новий пароль'
            self.fields['new_password2'].label = 'Підтвердження нового пароля'
            self.fields['new_password1'].help_text = 'Пароль має містити щонайменше 8 символів і не бути надто простим.'
            self.fields['new_password2'].help_text = 'Введіть новий пароль ще раз для підтвердження.'


class UkrainianAuthenticationForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['username'].label = 'Username'
            self.fields['password'].label = 'Password'
        else:
            self.fields['username'].label = 'Нікнейм'
            self.fields['password'].label = 'Пароль'
