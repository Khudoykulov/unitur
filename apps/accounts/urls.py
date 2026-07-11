"""Account URL patterns."""

from django.urls import path

from .views import StaffLoginView, UserProfileView

app_name = "accounts"

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="profile"),
    # Hidden staff-access endpoint (POST-only, behind the Ctrl+Shift+A modal).
    path("staff-access/", StaffLoginView.as_view(), name="staff-login"),
]
