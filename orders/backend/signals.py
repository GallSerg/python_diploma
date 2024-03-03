from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from .models import ConfirmToken, User
from .tasks import send_email_task, password_reset_task, new_order_task

new_user_registered = Signal()

new_order = Signal()

social_auth_user = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    password_reset_task.delay(reset_password_token.user, reset_password_token.user.email, reset_password_token.key)


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    token, i = ConfirmToken.objects.get_or_create(user_id=user_id)
    send_email_task.delay(user_id, token.key, token.user.email)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(id=user_id)
    new_order_task.delay(user.email)
