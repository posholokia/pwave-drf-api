from templated_mail.mail import BaseEmailMessage
from pulsewave import settings
from taskmanager.token import token_generator, user_token_generator

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


class InviteUserEmail(BaseEmailMessage):
    template_name = "email/workspace_invite.html"

    def get_context_data(self):
        context = super().get_context_data()

        user = context['user']
        workspace = context['workspace']

        context['wuid'] = utils.encode_uid(workspace.id)
        context['uid'] = utils.encode_uid(user.id)
        context['token'] = user_token_generator.make_token(user)

        if context['new_user']:
            url = settings.WORKSAPCES['INVITE_NEW_USER_EMAIL_URL'].format(**context)
        else:
            url = settings.WORKSAPCES['INVITE_EXISTS_USER_EMAIL_URL'].format(**context)

        context['url'] = url
        return context


# class InviteNewUserEmail(BaseEmailMessage):
#     template_name = "email/workspace_invite.html"
#
#     def get_context_data(self):
#         context = super().get_context_data()
#
#         user = context['user']
#         workspace = context['workspace']
#
#         context['wuid'] = utils.encode_uid(workspace.id)
#         print(workspace.id)
#         context['uid'] = utils.encode_uid(user.id)
#         context['token'] = user_token_generator.make_token(user)
#         context['url'] = settings.WORKSAPCES['INVITE_EMAIL_URL'].format(**context)
#         return context

