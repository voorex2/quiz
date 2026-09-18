from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Username')
        self.fields['email'].label = _('Email address')
        self.fields['password1'].label = _('Password')
        self.fields['password2'].label = _('Password confirmation')
        self.fields['username'].help_text = _(
            'Up to 150 characters. Letters, digits and @/./+/-/_ only.'
        )
        self.fields['password1'].help_text = _(
            'Your password must contain at least 8 characters and not be too simple.'
        )
        self.fields['password2'].help_text = _(
            'Enter the same password again for verification.'
        )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UsernameChangeForm(forms.ModelForm):
    username = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Username')

    class Meta:
        model = User
        fields = ('username',)


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = _('Current password')
        self.fields['new_password1'].label = _('New password')
        self.fields['new_password2'].label = _('New password confirmation')
        self.fields['new_password1'].help_text = _(
            'Your password must contain at least 8 characters and not be too simple.'
        )
        self.fields['new_password2'].help_text = _(
            'Enter the new password again for verification.'
        )


class UkrainianAuthenticationForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Username')
        self.fields['password'].label = _('Password')
