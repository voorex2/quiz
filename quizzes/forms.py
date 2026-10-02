from django import forms
from django.forms import formset_factory, inlineformset_factory
from django.utils.translation import gettext as _

from .models import Answer, Question, Quiz


class QuizForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = _('Quiz title')
        self.fields['description'].label = _('Description')
        self.fields['is_published'].label = _('Publish quiz')
        self.fields['is_private'].label = _('Private quiz with invite code')

    class Meta:
        model = Quiz
        fields = ('title', 'description', 'is_published', 'is_private')


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = _('Question text')
        self.fields['question_type'].label = _('Question type')
        self.fields['media_url'].label = _('Image or video URL')
        self.fields['time_limit'].label = _('Time limit (seconds)')
        self.fields['order'].label = _('Question order')
        self.fields['question_type'].choices = (
            ('text', _('Text')),
            ('image', _('Image')),
            ('video', _('Video')),
        )

    class Meta:
        model = Question
        fields = ('text', 'question_type', 'media_url', 'time_limit', 'order')


class AnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = _('Answer option')
        self.fields['is_correct'].label = _('Correct answer')

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
        labels = (
            ('text', _('Question text')),
            ('question_type', _('Question type')),
            ('media_url', _('Image or video URL')),
            ('time_limit', _('Time limit (seconds)')),
            ('answer_1', _('Answer 1')),
            ('answer_2', _('Answer 2')),
            ('answer_3', _('Answer 3')),
            ('answer_4', _('Answer 4')),
            ('correct_answer', _('Correct answer')),
        )
        for field_name, label in labels:
            self.fields[field_name].label = label
        self.fields['DELETE'].label = _('Remove question')
        self.fields['question_type'].choices = (
            ('text', _('Text')), ('image', _('Image')), ('video', _('Video'))
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
            raise forms.ValidationError(_('Choose a question type.'))
        if not cleaned_data.get('time_limit'):
            raise forms.ValidationError(_('Enter a time limit.'))
        answers = [cleaned_data.get(f'answer_{index}', '').strip() for index in range(1, 5)]
        if len([answer for answer in answers if answer]) < 2:
            raise forms.ValidationError(_('Add at least two answer options.'))
        correct_answer = cleaned_data.get('correct_answer')
        if not cleaned_data.get('text', '').strip():
            raise forms.ValidationError(_('Enter the question text.'))
        if not correct_answer:
            raise forms.ValidationError(_('Select the correct answer.'))
        if correct_answer and not answers[int(correct_answer) - 1]:
            raise forms.ValidationError(_('The correct answer cannot be empty.'))
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
