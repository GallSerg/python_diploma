from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
from .views import UserRegister, EmailConfirm, UserLogin, ContactView, UserDetails, CategoryView, ShopView, \
    PartnerUpdate, PartnerState, PartnerOrders, BasketView, OrderView, ProductInfoView, custom_login_view


def trigger_error(request):
    division_by_zero = 1 / 0  # sentry trigger


app_name = 'backend'

urlpatterns = [
    path('sentry-debug/', trigger_error),
    path('user/register', UserRegister.as_view(), name='user-register'),
    path('user/register/confirm', EmailConfirm.as_view(), name='email-confirm'),
    path('user/login', UserLogin.as_view(), name='user-login'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('user/details', UserDetails.as_view(), name='user-details'),
    path('user/contact', ContactView.as_view(), name='contact-list'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('products', ProductInfoView.as_view(), name='shops'),
    path('custom_login', custom_login_view, name='custom_login'),
]
