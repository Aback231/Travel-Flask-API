from requests import Response, post
from typing import List
import os

from constants.http_status_codes import HTTP_200_OK, HTTP_403_FORBIDDEN
from libs.strings import get_text


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']
    MAILGUN_DOMAIN = os.environ['MAILGUN_DOMAIN']
    FROM_TITLE = "RBT Travel Agency"
    FROM_EMAIL = f"do-not-reply@{MAILGUN_DOMAIN}"


    @classmethod
    def send_email(cls, email: List[str], subject: str, html: str) -> Response:
        if cls.MAILGUN_API_KEY is None:
            raise MailGunException(get_text("LIBS_MAILGUN_FAILED_LOAD_API_KEY"))

        if cls.MAILGUN_DOMAIN is None:
            raise MailGunException(get_text("LIBS_MAILGUN_FAILED_LOAD_DOMAIN"))

        response = post(
            f"https://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages",
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                "from": f"{cls.FROM_TITLE} <{cls.FROM_EMAIL}>",
                "to": email,
                "subject": subject,
                "html": html,
            },
        )

        if response.status_code not in [HTTP_200_OK, HTTP_403_FORBIDDEN]:
            raise MailGunException(get_text("LIBS_MAILGUN_ERROR_SENDING_EMAIL").format(response.status_code))

        return response
