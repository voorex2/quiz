from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuestionEditorFormSet, QuizForm
from .models import Answer, Question, Quiz


def quiz_list_view(request):
    quizzes = Quiz.objects.filter(is_published=True).select_related('owner')
    return render(request, 'quizzes/quiz_list.html', {'quizzes': quizzes})


@login_required
def quiz_create_view(request):
    form = QuizForm(request.POST or None)
    question_data = _question_formset_data(request)
    question_formset = QuestionEditorFormSet(question_data, prefix='questions')
    if request.method == 'POST' and form.is_valid() and question_formset.is_valid():
        quiz = form.save(commit=False)
        quiz.owner = request.user
        quiz.save()
        _save_question_forms(quiz, question_formset)
        return redirect('quiz_detail', pk=quiz.pk)

    return render(
        request,
        'quizzes/quiz_form.html',
        {'form': form, 'question_formset': question_formset, 'is_editing': False},
    )


@login_required
def quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)
    initial = _question_initial(quiz)
    form = QuizForm(request.POST or None, instance=quiz)
    question_formset = QuestionEditorFormSet(
        _question_formset_data(request),
        initial=initial if request.method != 'POST' else None,
        prefix='questions',
    )
    if request.method == 'POST' and form.is_valid() and question_formset.is_valid():
        quiz = form.save()
        _save_question_forms(quiz, question_formset)
        return redirect('quiz_detail', pk=quiz.pk)

    return render(
        request,
        'quizzes/quiz_form.html',
        {'form': form, 'question_formset': question_formset, 'is_editing': True, 'quiz': quiz},
    )


def quiz_detail_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)
    return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz})


@login_required
def question_create_view(request, pk):
    get_object_or_404(Quiz, pk=pk, owner=request.user)
    return redirect('quiz_edit', pk=pk)


def _question_formset_data(request):
    if request.method != 'POST':
        return None
    data = request.POST.copy()
    if 'questions-TOTAL_FORMS' not in data:
        data.update({
            'questions-TOTAL_FORMS': '0',
            'questions-INITIAL_FORMS': '0',
            'questions-MIN_NUM_FORMS': '0',
            'questions-MAX_NUM_FORMS': '1000',
        })
    return data


def _question_initial(quiz):
    initial = []
    for question in quiz.questions.prefetch_related('answers').all():
        answers = list(question.answers.all())
        initial.append({
            'text': question.text,
            'question_type': question.question_type,
            'media_url': question.media_url,
            'time_limit': question.time_limit,
            **{f'answer_{index}': answers[index - 1].text if len(answers) >= index else '' for index in range(1, 5)},
            'correct_answer': str(next((index for index, answer in enumerate(answers, 1) if answer.is_correct), 1)),
        })
    return initial


@transaction.atomic
def _save_question_forms(quiz, question_formset):
    quiz.questions.all().delete()
    for order, form in enumerate(question_formset, 1):
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            continue
        data = form.cleaned_data
        question = Question.objects.create(
            quiz=quiz,
            text=data['text'],
            question_type=data['question_type'],
            media_url=data.get('media_url', ''),
            time_limit=data['time_limit'],
            order=order,
        )
        correct_answer = int(data['correct_answer'])
        for index in range(1, 5):
            answer_text = data.get(f'answer_{index}', '').strip()
            if answer_text:
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=index == correct_answer,
                )


def quiz_take_view(request, pk):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__answers'), pk=pk, is_published=True)
    questions = list(quiz.questions.all())

    if request.method == 'POST':
        score = sum(
            1
            for question in questions
            if request.POST.get(f'question_{question.pk}')
            and question.answers.filter(
                pk=request.POST[f'question_{question.pk}'], is_correct=True
            ).exists()
        )
        request.session[f'quiz_result_{quiz.pk}'] = {'score': score, 'total': len(questions)}
        return redirect('quiz_result', pk=quiz.pk)

    return render(request, 'quizzes/quiz_take.html', {'quiz': quiz, 'questions': questions})


def quiz_result_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)
    result = request.session.pop(f'quiz_result_{quiz.pk}', None)
    if result is None:
        return redirect('quiz_detail', pk=quiz.pk)
    return render(request, 'quizzes/quiz_result.html', {'quiz': quiz, 'result': result})
