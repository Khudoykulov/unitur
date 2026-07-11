"""Tests for the bookings app: Inquiry model, forms, and confirmation codes."""

import pytest
from django.test import RequestFactory

from apps.bookings.forms import BookingForm, InquiryForm
from apps.bookings.models import Inquiry, _generate_confirmation_number
from tests import factories as f

pytestmark = pytest.mark.django_db


class TestConfirmationNumber:
    def test_format(self):
        code = _generate_confirmation_number()
        assert len(code) == 8
        assert code == code.upper()

    def test_unique_ish(self):
        codes = {_generate_confirmation_number() for _ in range(50)}
        assert len(codes) > 45  # extremely unlikely to collide


class TestInquiry:
    def test_confirmation_number_assigned_on_create(self):
        inquiry = f.make_inquiry()
        assert inquiry.confirmation_number
        assert len(inquiry.confirmation_number) == 8

    def test_str(self):
        inquiry = f.make_inquiry(first_name="Ali", last_name="Valiev", inquiry_type="tour")
        assert inquiry.confirmation_number in str(inquiry)
        assert "Ali Valiev" in str(inquiry)

    def test_full_name(self):
        inquiry = f.make_inquiry(first_name="Ali", last_name="Valiev")
        assert inquiry.full_name == "Ali Valiev"

    def test_full_name_strips(self):
        inquiry = f.make_inquiry(first_name="Ali", last_name="")
        assert inquiry.full_name == "Ali"

    def test_total_travelers(self):
        inquiry = f.make_inquiry(num_adults=2, num_children=3)
        assert inquiry.total_travelers == 5

    def test_get_client_ip_direct(self):
        inquiry = f.make_inquiry()
        req = RequestFactory().get("/", REMOTE_ADDR="10.0.0.1")
        assert inquiry.get_client_ip(req) == "10.0.0.1"

    def test_get_client_ip_forwarded(self):
        inquiry = f.make_inquiry()
        req = RequestFactory().get("/")
        req.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4, 5.6.7.8"
        assert inquiry.get_client_ip(req) == "1.2.3.4"


class TestBookingForm:
    def test_valid_minimal(self):
        form = BookingForm(
            data={"first_name": "Ali", "last_name": "Valiev", "phone": "+998901112233"}
        )
        assert form.is_valid(), form.errors

    def test_email_optional(self):
        form = BookingForm(
            data={"first_name": "Ali", "last_name": "Valiev", "phone": "1234567"}
        )
        assert form.is_valid(), form.errors

    def test_missing_required_fields(self):
        form = BookingForm(data={"first_name": "Ali"})
        assert not form.is_valid()
        assert "last_name" in form.errors
        assert "phone" in form.errors

    def test_phone_too_short_rejected(self):
        form = BookingForm(
            data={"first_name": "Ali", "last_name": "Valiev", "phone": "123"}
        )
        assert not form.is_valid()
        assert "phone" in form.errors


class TestInquiryForm:
    def test_valid(self):
        form = InquiryForm(
            data={
                "inquiry_type": "custom",
                "first_name": "Ali",
                "last_name": "Valiev",
                "phone": "+998901112233",
                "num_adults": 2,
                "num_children": 0,
            }
        )
        assert form.is_valid(), form.errors

    def test_requires_names_and_phone(self):
        form = InquiryForm(data={"inquiry_type": "custom"})
        assert not form.is_valid()
        assert "first_name" in form.errors
        assert "phone" in form.errors
