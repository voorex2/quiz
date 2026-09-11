from django import forms
from django.forms import formset_factory, inlineformset_factory
from django.utils.translation import get_language

from .models import Answer, Question, Quiz


class QuizForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == 'en':
            self.fields['title'].label = 'Quiz title'
            self.fields['description'].label = 'Description'
            self.fields['is_published'].label = 'Publish quiz'
            self.fields['is_private'].label = 'Private quiz with invite code'
        else:
            self.fields['title'].label = 'Назва вікторини'
            self.fields['description'].label = 'Опис'
            self.fields['is_published'].label = 'Опублікувати вікторину'
            self.fields['is_private'].label = 'Приватна вікторина за кодом'

    class Meta:
        model = Quiz
        fields = ('title', 'description', 'is_published', 'is_private')


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


class QuestionEditorForm(forms.Form):
    text = forms.CharField(required=False)
    question_type = forms.ChoiceField(choices=Question.QuestionType.choices, required=False)
    media_url = forms.URLField(required=False)
    time_limit = forms.IntegerField(min_value=5, initial=30, required=False)
    answer_1 = forms.CharField(required=False)
    answer_2 = forms.CharField(required=False)
    answer_3 = forms.CharField(required=False)
    answer_4 = forms.CharField(required=False)
    correct_answer = forms.ChoiceField(
        choices=(('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')),
        widget=forms.RadioSelect,
        required=False,
    )
    DELETE = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        english = get_language() == 'en'
        labels = (
            ('text', 'Question text' if english else 'Текст питання'),
            ('question_type', 'Question type' if english else 'Тип питання'),
            ('media_url', 'Image or video URL' if english else 'Посилання на медіа'),
            ('time_limit', 'Time limit (seconds)' if english else 'Час на відповідь (секунди)'),
            ('answer_1', 'Answer 1' if english else 'Відповідь 1'),
            ('answer_2', 'Answer 2' if english else 'Відповідь 2'),
            ('answer_3', 'Answer 3' if english else 'Відповідь 3'),
            ('answer_4', 'Answer 4' if english else 'Відповідь 4'),
            ('correct_answer', 'Correct answer' if english else 'Правильна відповідь'),
        )
        for field_name, label in labels:
            self.fields[field_name].label = label
        self.fields['DELETE'].label = 'Remove question' if english else 'Видалити питання'
        if english:
            self.fields['question_type'].choices = (
                ('text', 'Text'), ('image', 'Image'), ('video', 'Video')
            )
            self.fields['correct_answer'].choices = tuple(
                (str(index), str(index)) for index in range(1, 5)
            )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('DELETE'):
            return cleaned_data
        if not cleaned_data.get('text', '').strip() and not any(
            cleaned_data.get(f'answer_{index}', '').strip() for index in range(1, 5)
        ):
            return cleaned_data
        if not cleaned_data.get('question_type'):
            raise forms.ValidationError('Оберіть тип питання.')
        if not cleaned_data.get('time_limit'):
            raise forms.ValidationError('Вкажіть час на відповідь.')
        answers = [cleaned_data.get(f'answer_{index}', '').strip() for index in range(1, 5)]
        if len([answer for answer in answers if answer]) < 2:
            raise forms.ValidationError('Додайте щонайменше два варіанти відповіді.')
        correct_answer = cleaned_data.get('correct_answer')
        if not cleaned_data.get('text', '').strip():
            raise forms.ValidationError('Додайте текст питання.')
        if not correct_answer:
            raise forms.ValidationError('Оберіть правильну відповідь.')
        if correct_answer and not answers[int(correct_answer) - 1]:
            raise forms.ValidationError('Правильна відповідь має містити текст.')
        return cleaned_data


QuestionEditorFormSet = formset_factory(
    QuestionEditorForm,
    extra=1,
    can_delete=False,
)


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=False,
)
