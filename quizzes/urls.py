from django.urls import path

from .views import (
    question_create_view,
    quiz_create_view,
    quiz_detail_view,
    quiz_list_view,
    quiz_result_view,
    quiz_take_view,
)


urlpatterns = [
    path('', quiz_list_view, name='quiz_list'),
    path('create/', quiz_create_view, name='quiz_create'),
    path('<int:pk>/', quiz_detail_view, name='quiz_detail'),
    path('<int:pk>/questions/add/', question_create_view, name='question_create'),
    path('<int:pk>/take/', quiz_take_view, name='quiz_take'),
    path('<int:pk>/result/', quiz_result_view, name='quiz_result'),
]
