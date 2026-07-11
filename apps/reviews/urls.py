"""Review URL patterns."""

from django.urls import path

from .views import ReviewCreateView, ReviewListView

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="list"),
    path("write/", ReviewCreateView.as_view(), name="create"),
]
