"""
Celery async tasks for booking email notifications.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(self, inquiry_pk: int) -> None:
    """
    Send a booking confirmation email to the customer.

    Retries up to 3 times with 60-second backoff on failure.
    """
    from .models import Inquiry

    try:
        inquiry = Inquiry.objects.select_related("tour", "departure").get(pk=inquiry_pk)
    except Inquiry.DoesNotExist:
        logger.error("Inquiry %s not found for confirmation email", inquiry_pk)
        return

    subject = f"Booking Confirmed – {inquiry.confirmation_number}"
    context = {"inquiry": inquiry, "SITE_NAME": settings.SITE_NAME}
    html_body = render_to_string("emails/booking_confirmation.html", context)
    text_body = render_to_string("emails/booking_confirmation.txt", context)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inquiry.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info("Confirmation email sent for inquiry %s", inquiry.confirmation_number)
    except Exception as exc:
        logger.exception("Failed to send confirmation for inquiry %s", inquiry_pk)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_admin_notification(self, inquiry_pk: int) -> None:
    """
    Notify the admin team about a new inquiry or booking.
    """
    from .models import Inquiry

    try:
        inquiry = Inquiry.objects.select_related("tour", "hotel").get(pk=inquiry_pk)
    except Inquiry.DoesNotExist:
        return

    subject = f"[New {inquiry.get_inquiry_type_display()}] {inquiry.full_name} – {inquiry.confirmation_number}"
    admin_url = "{}/{}bookings/inquiry/{}/change/".format(
        settings.SITE_URL.rstrip("/"),
        getattr(settings, "ADMIN_URL", "admin/"),
        inquiry.pk,
    )
    context = {"inquiry": inquiry, "SITE_NAME": settings.SITE_NAME, "admin_url": admin_url}
    html_body = render_to_string("emails/booking_admin_notification.html", context)
    text_body = strip_tags(html_body)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.SITE_EMAIL],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
    except Exception as exc:
        logger.exception("Admin notification failed for inquiry %s", inquiry_pk)
        raise self.retry(exc=exc)
