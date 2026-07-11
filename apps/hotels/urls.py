"""Hotel URL patterns."""

from django.urls import path

from .views import HotelDetailView, HotelListView

app_name = "hotels"

urlpatterns = [
    path("", HotelListView.as_view(), name="list"),
    path("<slug:slug>/", HotelDetailView.as_view(), name="detail"),
]
