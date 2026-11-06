from django.urls import path

from .views import (
    favorite_view, statistics_view, follow_view, notifications_view,
    question_create_view,
    quiz_create_view,
    quiz_detail_view,
    quiz_delete_view,
    quiz_edit_view,
    quiz_history_view,
    quiz_join_view,
    quiz_like_view,
    quiz_list_view,
    quiz_rating_view,
    quiz_result_view,
    quiz_take_view,
)


urlpatterns = [
    path('statistics/', statistics_view, name='statistics'),
    path('notifications/', notifications_view, name='notifications'),
    path('authors/<int:pk>/follow/', follow_view, name='author_follow'),
    path('<int:pk>/favorite/', favorite_view, name='quiz_favorite'),
    path('', quiz_list_view, name='quiz_list'),
    path('history/', quiz_history_view, name='quiz_history'),
    path('create/', quiz_create_view, name='quiz_create'),
    path('join/', quiz_join_view, name='quiz_join'),
    path('<int:pk>/edit/', quiz_edit_view, name='quiz_edit'),
    path('<int:pk>/rating/', quiz_rating_view, name='quiz_rating'),
    path('<int:pk>/', quiz_detail_view, name='quiz_detail'),
    path('<int:pk>/like/', quiz_like_view, name='quiz_like'),
    path('<int:pk>/delete/', quiz_delete_view, name='quiz_delete'),
    path('<int:pk>/questions/add/', question_create_view, name='question_create'),
    path('<int:pk>/take/', quiz_take_view, name='quiz_take'),
    path('<int:pk>/result/', quiz_result_view, name='quiz_result'),
]
