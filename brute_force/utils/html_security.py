from odoo.tools import html_sanitize
from markupsafe import Markup


def to_safe_html(body):
    """
    Use for chatter (message_post)
    """
    if not body:
        return ""

    return Markup(html_sanitize(
        body,
        sanitize_attributes=False,
        sanitize_style=True,
        strip_classes=False,
    ))


def to_safe_email(body):
    """
    Use for email body_html
    """
    if not body:
        return ""

    return html_sanitize(
        body,
        sanitize_attributes=False,
        sanitize_style=True,
        strip_classes=False,
    )