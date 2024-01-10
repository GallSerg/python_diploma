from django.contrib import admin
from django.urls import path

from orders.backend.views import UserRegister, EmailConfirm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/register', UserRegister.as_view(), name='user-register'),
    path('user/register/confirm', EmailConfirm.as_view(), name='email-confirm'),
]
