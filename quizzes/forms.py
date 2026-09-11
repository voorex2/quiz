from django import forms

from .models import Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ('title', 'description', 'is_published')
        labels = {
            'title': 'Назва вікторини',
            'description': 'Опис',
            'is_published': 'Опублікувати вікторину',
        }
