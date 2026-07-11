"""Destination URL patterns."""

from django.urls import path

from .views import CityDetailView, CountryDetailView, DestinationListView

app_name = "destinations"

urlpatterns = [
    path("", DestinationListView.as_view(), name="list"),
    path("<slug:slug>/", CountryDetailView.as_view(), name="country"),
    path("<slug:country_slug>/<slug:city_slug>/", CityDetailView.as_view(), name="city"),
]
