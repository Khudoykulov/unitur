"""Core URL patterns: home, about, contact."""

from django.urls import path

from .views import AboutView, ContactView, HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
]
