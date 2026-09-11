from django.shortcuts import render

from quizzes.models import Quiz


def home_view(request):
    popular_quizzes = Quiz.objects.filter(is_published=True, is_private=False).order_by('-likes__created_at', '-created_at').distinct()[:3]
    new_quizzes = Quiz.objects.filter(is_published=True, is_private=False).order_by('-created_at')[:3]
    return render(request, 'main/home.html', {'popular_quizzes': popular_quizzes, 'new_quizzes': new_quizzes})
