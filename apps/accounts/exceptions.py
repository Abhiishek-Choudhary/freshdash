from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class APIError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bad_request"

    def __init__(self, message, code=None, status_code=None):
        self.detail = {"message": message, "code": code or self.default_code}
        if status_code:
            self.status_code = status_code


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            if "detail" in response.data and len(response.data) == 1:
                detail = response.data["detail"]
                if isinstance(detail, list):
                    message = str(detail[0])
                else:
                    message = str(detail)
                response.data = {
                    "message": message,
                    "code": getattr(exc, "default_code", "error"),
                }
            elif "non_field_errors" in response.data:
                response.data = {
                    "message": str(response.data["non_field_errors"][0]),
                    "code": "validation_error",
                }
        return response
    return response
