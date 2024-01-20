from django.urls import path
from .views import UserRegister, EmailConfirm

app_name = 'backend'

urlpatterns = [
    path('user/register', UserRegister.as_view(), name='user-register'),
    path('user/register/confirm', EmailConfirm.as_view(), name='email-confirm'),
]
