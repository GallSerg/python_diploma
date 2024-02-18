from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from .models import ConfirmToken, User
from .tasks import send_email_task


new_user_registered = Signal()

new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    msg = EmailMultiAlternatives(subject=f"Password Reset Token for {reset_password_token.user}",
                                 body=reset_password_token.key,
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[reset_password_token.user.email]
                                 )
    msg.send()


# @receiver(new_user_registered)
# def new_user_registered_signal(user_id, **kwargs):
#     token, i = ConfirmToken.objects.get_or_create(user_id=user_id)
#
#     msg = EmailMultiAlternatives(subject=f"Password Reset Token for {token.user.email}",
#                                  body=token.key,
#                                  from_email=settings.EMAIL_HOST_USER,
#                                  to=[token.user.email]
#                                  )
#     msg.send()

@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    # Instead of sending the email directly, call the Celery task
    send_email_task.delay(user_id)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(subject=f"Order status update",
                                 body='Order complete',
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[user.email]
                                 )
    msg.send()
