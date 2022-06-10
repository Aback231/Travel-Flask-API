from typing import List
from requests import Response, post

FAILED_LOAD_API_KEY = "Failed to load Mailgun API key."
FAILED_LOAD_DOMAIN = "Failed to load Mailgun domain."
ERROR_SENDING_EMAIL = "Error in sending email."


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    MAILGUN_API_KEY = "4626f9437f08a8afd18885cdfc685b84-523596d9-6927e3db"
    MAILGUN_DOMAIN = "sandbox0a208a4ab1c347a980f0b30250a6ef1e.mailgun.org"

    FROM_TITLE = "RBT Travel Agency"
    FROM_EMAIL = f"do-not-reply@{MAILGUN_DOMAIN}"

    @classmethod
    def send_email(cls, email: List[str], subject: str, html: str) -> Response:
        if cls.MAILGUN_API_KEY is None:
            raise MailGunException(FAILED_LOAD_API_KEY)

        if cls.MAILGUN_DOMAIN is None:
            raise MailGunException(FAILED_LOAD_DOMAIN)

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

        if response.status_code != 200:
            raise MailGunException(ERROR_SENDING_EMAIL)

        return response
