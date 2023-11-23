from datetime import datetime, timedelta

from jwt import DecodeError, ExpiredSignatureError

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int
from django.utils.crypto import constant_time_compare

from pulsewave.settings import SECRET_KEY as secret
from pulsewave.settings import DJOSER, WORKSAPCES
import jwt


class TokenJWTGenerator:
    algorithm = 'HS256'
    expired = None

    def token_encode(self, payload: dict):
        self.expired = DJOSER.get('CHANGE_EMAIL_URL_EXPIRED', None)

        if self.expired:
            end_time = datetime.now() + timedelta(**self.expired)
            payload.update({'expired': end_time.strftime("%Y-%m-%d %H:%M:%S")})

        token = jwt.encode(payload, secret, algorithm=self.algorithm)
        return token

    def token_decode(self, token) -> dict or Exception:
        try:
            decoded_token = jwt.decode(token, secret, algorithms=self.algorithm)
        except DecodeError as e:
            return e
        except ExpiredSignatureError as e:
            return e
        else:
            return self._token_expired(decoded_token)

    def _token_expired(self, data: dict):
        expired = data.get('expired', None)

        if expired:
            expiration_time = datetime.strptime(expired, '%Y-%m-%d %H:%M:%S')

            if datetime.now() > expiration_time:
                return None

        return data


class TokenUserGenerator(PasswordResetTokenGenerator):
    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                    self._make_token_with_timestamp(user, ts, secret),
                    token,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > WORKSAPCES.get('INVITE_TOKEN_TIMEOUT', 3600*24):
            return False

        return True


token_generator = TokenJWTGenerator()
user_token_generator = TokenUserGenerator()
