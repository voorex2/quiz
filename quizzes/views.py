from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuizForm
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
