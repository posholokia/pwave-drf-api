from templated_mail.mail import BaseEmailMessage
from pulsewave import settings
from taskmanager.token import token_generator


class ChangeEmail(BaseEmailMessage):
    template_name = "email/change_email.html"

    def get_context_data(self):
        context = super().get_context_data()

        new_email = context['new_email']
        user = context['user']
        user_id = user.id
        current_email = user.email

        payload = {
            'user_id': user_id,
            'current_email': current_email,
            'new_email': new_email,
        }

        context['token'] = token_generator.token_encode(payload)
        context['url'] = settings.DJOSER['CHANGE_EMAIL_URL'].format(**context)
        return context
