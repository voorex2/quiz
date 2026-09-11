from django.urls import path

from .views import quiz_create_view, quiz_detail_view, quiz_list_view


urlpatterns = [
    path('', quiz_list_view, name='quiz_list'),
    path('create/', quiz_create_view, name='quiz_create'),
    path('<int:pk>/', quiz_detail_view, name='quiz_detail'),
]
