from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
from .views import UserRegister, EmailConfirm, UserLogin, ContactView, UserDetails, CategoryView, ShopView, \
    PartnerUpdate, PartnerState, PartnerOrders

app_name = 'backend'

urlpatterns = [
    path('user/register', UserRegister.as_view(), name='user-register'),
    path('user/register/confirm', EmailConfirm.as_view(), name='email-confirm'),
    path('user/login', UserLogin.as_view(), name='user-login'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('user/details', UserDetails.as_view(), name='user-details'),
    path('contact', ContactView.as_view(), name='contact'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
]
