from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


@shared_task
def send_email_task(user_id, token, email):
    msg = EmailMultiAlternatives(
        subject=f"Password Reset Token for {email}",
        body=token,
        from_email=settings.EMAIL_HOST_USER,
        to=[email]
    )
    msg.send()


@shared_task
def password_reset_task(user, email, token):
    msg = EmailMultiAlternatives(subject=f"Password Reset Token for {user}",
                                 body=token,
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[email]
                                 )
    msg.send()


@shared_task
def new_order_task(email):
    msg = EmailMultiAlternatives(subject=f"Order status update",
                                 body='Order complete',
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[email]
                                 )
    msg.send()
