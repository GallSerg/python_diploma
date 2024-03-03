from social_core.pipeline.partial import partial

from .models import ConfirmToken
from .tasks import send_email_task


@partial
def create_and_send_token(strategy, backend, user, *args, **kwargs):
    is_new_user = kwargs.get('is_new', False)
    if is_new_user:
        token, i = ConfirmToken.objects.get_or_create(user_id=user.id)
        send_email_task.delay(user.id, token.key, token.user.email)
        return {'user': user, 'strategy': strategy, 'is_new': True}
    else:
        return {'user': user, 'strategy': strategy, 'is_new': False}
