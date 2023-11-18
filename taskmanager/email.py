from templated_mail.mail import BaseEmailMessage
from pulsewave import settings
from taskmanager.token import token_generator
from django.contrib.auth.tokens import default_token_generator
from djoser import utils


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


class InviteToWorkspaceEmail(BaseEmailMessage):
    template_name = "email/workspace_invite.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context['user']
        context['wp_uid'] = utils.encode_uid(context['workspace'].id)
        context['uid'] = utils.encode_uid(user.id)
        context['token'] = default_token_generator.make_token(user)
        context['url'] = 'auth/invite/{wp_uid}/{uid}/{token}'.format(**context)
        return context
