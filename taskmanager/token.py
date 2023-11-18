from datetime import datetime, timedelta

from jwt import DecodeError, ExpiredSignatureError

from pulsewave.settings import SECRET_KEY as secret
from pulsewave.settings import DJOSER
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


token_generator = TokenJWTGenerator()
