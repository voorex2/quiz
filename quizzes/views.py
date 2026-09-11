from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AnswerFormSet, QuestionForm, QuizForm
from .models import Quiz


def quiz_list_view(request):
    quizzes = Quiz.objects.filter(is_published=True).select_related('owner')
    return render(request, 'quizzes/quiz_list.html', {'quizzes': quizzes})


@login_required
def quiz_create_view(request):
    form = QuizForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.owner = request.user
        quiz.save()
        return redirect('quiz_detail', pk=quiz.pk)

    return render(request, 'quizzes/quiz_form.html', {'form': form})


def quiz_detail_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)
    return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz})


@login_required
def question_create_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)
    question_form = QuestionForm(request.POST or None)
    answer_formset = AnswerFormSet(request.POST or None)

    if request.method == 'POST' and question_form.is_valid() and answer_formset.is_valid():
        question = question_form.save(commit=False)
        question.quiz = quiz
        question.save()
        answer_formset.instance = question
        answer_formset.save()
        return redirect('quiz_detail', pk=quiz.pk)

    return render(
        request,
        'quizzes/question_form.html',
        {'quiz': quiz, 'question_form': question_form, 'answer_formset': answer_formset},
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
