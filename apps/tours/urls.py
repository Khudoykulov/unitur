"""Tour URL patterns."""

from django.urls import path

from .views import TourDetailView, TourListView

app_name = "tours"

urlpatterns = [
    path("", TourListView.as_view(), name="list"),
    path("<slug:slug>/", TourDetailView.as_view(), name="detail"),
]
