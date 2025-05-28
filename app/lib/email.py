from flask import current_app as app

from app.lib.logger import get_logger

logger = get_logger(__name__)


def send_email(to_email: str, subject: str, html: str):
    """
    Sends an email

    `to_email`: List of email receipients as a comma separated string
    `subject`: The mail subject line
    `html`: The HTML mail body
    """
    from postmark import PMMail, PMMailSendException

    message = PMMail(
        api_key=app.config["POSTMARK_API_KEY"],
        sender=app.config["FROM_EMAIL"],
        to=to_email,
        subject=subject,
        html_body=html,
    )

    try:
        response = message.send()
        return response
    except PMMailSendException as e:
        logger.exception(e)
