from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import ConfirmToken


@shared_task
def send_email_task(user_id):
    token, created = ConfirmToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        subject=f"Password Reset Token for {token.user.email}",
        body=token.key,
        from_email=settings.EMAIL_HOST_USER,
        to=[token.user.email]
    )
    msg.send()
