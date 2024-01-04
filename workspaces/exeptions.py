from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidAction(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
