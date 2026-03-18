from django.urls import path

from rest_api.member.api import UserLoginView


urlpatterns = [
    # Endpoint for user login
    path('login/', UserLoginView.as_view(), name='user-login'),
]
