"""Booking URL patterns."""

from django.urls import path

from .views import BookingConfirmationView, BookingFormView, InquiryFormView

app_name = "bookings"

urlpatterns = [
    path("", InquiryFormView.as_view(), name="inquiry"),
    path("book/<slug:slug>/", BookingFormView.as_view(), name="book"),
    path("confirmation/<int:pk>/", BookingConfirmationView.as_view(), name="confirmation"),
]
