from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import get_language

from .models import Answer, Question, Quiz


class QuizForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['title'].label = 'Quiz title'
            self.fields['description'].label = 'Description'
            self.fields['is_published'].label = 'Publish quiz'
        else:
            self.fields['title'].label = 'Назва вікторини'
            self.fields['description'].label = 'Опис'
            self.fields['is_published'].label = 'Опублікувати вікторину'

    class Meta:
        model = Quiz
        fields = ('title', 'description', 'is_published')


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['text'].label = 'Question text'
            self.fields['question_type'].label = 'Question type'
            self.fields['media_url'].label = 'Image or video URL'
            self.fields['time_limit'].label = 'Time limit (seconds)'
            self.fields['order'].label = 'Question order'
            self.fields['question_type'].choices = (
                ('text', 'Text'),
                ('image', 'Image'),
                ('video', 'Video'),
            )
        else:
            self.fields['text'].label = 'Текст питання'
            self.fields['question_type'].label = 'Тип питання'
            self.fields['media_url'].label = 'Посилання на зображення або відео'
            self.fields['time_limit'].label = 'Час на відповідь (секунди)'
            self.fields['order'].label = 'Порядок питання'
            self.fields['question_type'].choices = (
                ('text', 'Текст'),
                ('image', 'Зображення'),
                ('video', 'Відео'),
            )

    class Meta:
        model = Question
        fields = ('text', 'question_type', 'media_url', 'time_limit', 'order')


class AnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['text'].label = 'Answer option'
            self.fields['is_correct'].label = 'Correct answer'
        else:
            self.fields['text'].label = 'Варіант відповіді'
            self.fields['is_correct'].label = 'Правильна відповідь'

    class Meta:
        model = Answer
        fields = ('text', 'is_correct')


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=False,
)
