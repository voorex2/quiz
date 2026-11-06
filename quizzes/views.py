import random

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .forms import QuestionEditorFormSet, QuizForm
from .models import (Answer, Question, Quiz, QuizAttempt, QuizLike, Category,
                     Favorite, AttemptAnswer, AuthorFollow, Notification,
                     NotificationPreference)


def quiz_list_view(request):
    search_query = request.GET.get('q', '').strip()
    show_mine = request.GET.get('mine') == '1' and request.user.is_authenticated
    show_favorites = request.GET.get('favorites') == '1'
    if show_favorites and not request.user.is_authenticated:
        return redirect('login')

    if show_mine:
        quizzes = Quiz.objects.filter(owner=request.user)
    else:
        quizzes = Quiz.objects.filter(is_published=True, is_private=False)

    if show_favorites:
        quizzes = quizzes.filter(favorites__user=request.user)
    category = request.GET.get('category', '')
    if category.isdecimal():
        quizzes = quizzes.filter(category_id=category)
    quizzes = quizzes.select_related('owner', 'category').annotate(like_count=Count('likes', distinct=True))

    if search_query:
        query_lower = search_query.lower()
        quizzes = [quiz for quiz in quizzes if query_lower in quiz.title.lower()]

    return render(
        request,
        'quizzes/quiz_list.html',
        {'quizzes': quizzes, 'search_query': search_query, 'show_mine': show_mine,
         'show_favorites': show_favorites, 'categories': Category.objects.all(), 'selected_category': category},
    )


@login_required
@transaction.atomic
def quiz_create_view(request):
    form = QuizForm(request.POST or None)
    question_data = _question_formset_data(request)
    question_formset = QuestionEditorFormSet(question_data, request.FILES or None, prefix='questions')
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
@transaction.atomic
def quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)
    initial = _question_initial(quiz)
    form = QuizForm(request.POST or None, instance=quiz)
    question_formset = QuestionEditorFormSet(
        _question_formset_data(request),
        request.FILES or None,
        initial=initial if request.method != 'POST' else None,
        prefix='questions',
    )
    current_images = {str(question.pk): question.image for question in quiz.questions.all() if question.image}
    for question_form in question_formset:
        question_form.current_image = current_images.get(str(question_form['question_id'].value()))
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
    quiz = get_object_or_404(Quiz.objects.annotate(like_count=Count('likes')), pk=pk)
    if not quiz.is_published and quiz.owner_id != request.user.id:
        raise Http404(_('Quiz not found'))
    can_view_private = not quiz.is_private or quiz.owner_id == request.user.id or request.session.get(f'joined_quiz_{quiz.pk}')
    if not can_view_private:
        return redirect('quiz_join')
    liked = request.user.is_authenticated and QuizLike.objects.filter(quiz=quiz, user=request.user).exists()
    favorite = request.user.is_authenticated and Favorite.objects.filter(quiz=quiz, user=request.user).exists()
    following = request.user.is_authenticated and AuthorFollow.objects.filter(author=quiz.owner, user=request.user).exists()
    return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz, 'liked': liked, 'favorite': favorite, 'following': following})


@login_required
def quiz_like_view(request, pk):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, pk=pk, is_published=True, is_private=False)
        QuizLike.objects.get_or_create(quiz=quiz, user=request.user)
    return redirect('quiz_detail', pk=pk)


@login_required
def quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)
    if request.method == 'POST':
        quiz.delete()
        return redirect('quiz_list')
    return redirect('quiz_detail', pk=pk)


def quiz_join_view(request):
    error = None
    if request.method == 'POST':
        code = request.POST.get('invite_code', '').strip().upper()
        quiz = Quiz.objects.filter(invite_code=code, is_private=True, is_published=True).first()
        if quiz:
            request.session[f'joined_quiz_{quiz.pk}'] = True
            return redirect('quiz_detail', pk=quiz.pk)
        error = _('Quiz with this code was not found.')
    return render(request, 'quizzes/quiz_join.html', {'error': error})


def _can_access_quiz(request, quiz):
    return not quiz.is_private or quiz.owner_id == request.user.id or request.session.get(f'joined_quiz_{quiz.pk}')


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
            'question_id': question.pk,
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
    existing = {question.pk: question for question in quiz.questions.all()}
    retained = []
    for order, form in enumerate(question_formset, 1):
        if not form.cleaned_data or form.cleaned_data.get('DELETE') or not form.cleaned_data.get('text', '').strip():
            continue
        data = form.cleaned_data
        question_id = data.get('question_id')
        if question_id and (question_id not in existing or question_id in retained):
            raise Http404(_('Question not found'))
        question = existing.get(question_id) or Question(quiz=quiz)
        question.text = data['text']
        question.question_type = data['question_type']
        question.media_url = data.get('media_url', '')
        question.time_limit = data['time_limit']
        question.order = order
        if data.get('remove_image'):
            question.image = ''
        if data.get('image'):
            question.image = data['image']
        question.save()
        retained.append(question.pk)
        question.answers.all().delete()
        correct_answer = int(data['correct_answer'])
        for index in range(1, 5):
            answer_text = data.get(f'answer_{index}', '').strip()
            if answer_text:
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=index == correct_answer,
                )
    quiz.questions.exclude(pk__in=retained).delete()


@transaction.atomic
def quiz_take_view(request, pk):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__answers'), pk=pk, is_published=True)
    if not _can_access_quiz(request, quiz):
        return redirect('quiz_join')
    questions = list(quiz.questions.all())

    if request.method == 'POST':
        correct = {question.pk: any(
            str(answer.pk) == request.POST.get(f'question_{question.pk}') and answer.is_correct
            for answer in question.answers.all()
        ) for question in questions}
        score = sum(correct.values())
        total = len(questions)
        percentage = int(round((score / total) * 100)) if total else 0
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user if request.user.is_authenticated else None,
            score=score,
            total=total,
            percentage=percentage,
        )
        AttemptAnswer.objects.bulk_create([
            AttemptAnswer(attempt=attempt, question=question, question_text=question.text, is_correct=correct[question.pk])
            for question in questions
        ])
        request.session[f'quiz_result_{quiz.pk}'] = {
            'score': score,
            'total': total,
            'percentage': percentage,
            'attempt_id': attempt.pk,
        }
        return redirect('quiz_result', pk=quiz.pk)

    if quiz.shuffle_questions:
        random.shuffle(questions)
    for question in questions:
        question.display_answers = list(question.answers.all())
        if quiz.shuffle_answers:
            random.shuffle(question.display_answers)
    return render(request, 'quizzes/quiz_take.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_history_view(request):
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-created_at')
    return render(request, 'quizzes/quiz_history.html', {'attempts': attempts})


def quiz_rating_view(request, pk):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('attempts__user'), pk=pk, is_published=True)
    if not _can_access_quiz(request, quiz):
        return redirect('quiz_join')
    attempts = quiz.attempts.select_related('user').order_by('-percentage', '-score', 'created_at')
    return render(request, 'quizzes/quiz_rating.html', {'quiz': quiz, 'attempts': attempts})


def quiz_result_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)
    result = request.session.pop(f'quiz_result_{quiz.pk}', None)
    if result is None:
        return redirect('quiz_detail', pk=quiz.pk)
    if result.get('attempt_id'):
        attempt = QuizAttempt.objects.filter(pk=result['attempt_id']).first()
        if attempt:
            result['percentage'] = attempt.percentage
    return render(request, 'quizzes/quiz_result.html', {'quiz': quiz, 'result': result})


@login_required
@require_POST
def favorite_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True, is_private=False)
    if request.POST.get('remove') == '1':
        Favorite.objects.filter(user=request.user, quiz=quiz).delete()
    else:
        Favorite.objects.get_or_create(user=request.user, quiz=quiz)
    return redirect('quiz_detail', pk=pk)


@login_required
def statistics_view(request):
    quizzes = Quiz.objects.filter(owner=request.user).annotate(
        attempt_count=Count('attempts'), average=Avg('attempts__percentage'))
    summary = QuizAttempt.objects.filter(quiz__owner=request.user).aggregate(
        attempt_count=Count('pk'), average=Avg('percentage'))
    questions = Question.objects.filter(quiz__owner=request.user).select_related('quiz').annotate(
        response_count=Count('responses'), errors=Count('responses', filter=Q(responses__is_correct=False)))
    questions = list(questions.filter(response_count__gt=0))
    for question in questions:
        question.error_rate = round(question.errors * 100 / question.response_count)
    questions.sort(key=lambda question: (-question.error_rate, -question.response_count))
    return render(request, 'quizzes/statistics.html', {'quizzes': quizzes, 'summary': summary, 'questions': questions})


@login_required
@require_POST
def follow_view(request, pk):
    author = get_object_or_404(get_user_model(), pk=pk)
    if author != request.user:
        if request.POST.get('remove') == '1':
            AuthorFollow.objects.filter(user=request.user, author=author).delete()
        else:
            AuthorFollow.objects.get_or_create(user=request.user, author=author)
    return redirect('notifications')


@login_required
def notifications_view(request):
    preference, _created = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if request.POST.get('action') == 'read':
            request.user.notifications.filter(quiz__is_published=True, quiz__is_private=False).update(is_read=True)
        elif request.POST.get('action') == 'preferences':
            preference.weekly = request.POST.get('weekly') == 'on'
            preference.save()
        return redirect('notifications')
    notifications = request.user.notifications.filter(quiz__is_published=True, quiz__is_private=False).select_related('quiz__owner')
    return render(request, 'quizzes/notifications.html', {
        'notifications': Paginator(notifications, 25).get_page(request.GET.get('page')),
        'preference': preference, 'following': request.user.following.select_related('author'),
    })
