"""Dashboard URL configuration."""

from django.urls import path

from apps.dashboard.views.articles import (
    ArticleCreateView,
    ArticleDeleteView,
    ArticleEditView,
    ArticleListView,
)
from apps.dashboard.views.bookings import (
    BookingDetailView,
    BookingListView,
    booking_export_csv,
)
from apps.dashboard.views.destinations import (
    ContinentCreateView,
    ContinentDeleteView,
    ContinentEditView,
    ContinentListView,
    CountryCreateView,
    CountryDeleteView,
    CountryEditView,
    DestinationListView,
)
from apps.dashboard.views.cities import (
    DomesticCityCreateView,
    DomesticCityDeleteView,
    DomesticCityEditView,
    DomesticCityListView,
)
from apps.dashboard.views.hero import (
    HeroSlideCreateView,
    HeroSlideDeleteView,
    HeroSlideEditView,
    HeroSlideListView,
)
from apps.dashboard.views.home import DashboardHomeView, dashboard_stats_api
from apps.dashboard.views.ichki_turlar import (
    IchkiTurCreateView,
    IchkiTurDeleteView,
    IchkiTurEditView,
    IchkiTurListView,
)
from apps.dashboard.views.hotels import (
    HotelCreateView,
    HotelDeleteView,
    HotelEditView,
    HotelListView,
)
from apps.dashboard.views.reviews import ReviewListView
from apps.dashboard.views.toggle import ToggleActiveView
from apps.dashboard.views.tour_categories import (
    TourCategoryCreateView,
    TourCategoryDeleteView,
    TourCategoryEditView,
    TourCategoryListView,
)
from apps.dashboard.views.tours import (
    TourCreateView,
    TourDeleteView,
    TourEditView,
    TourListView,
)
from apps.dashboard.views.users import (
    UserCreateView,
    UserDeleteView,
    UserEditView,
    UserListView,
    UserRoleUpdateView,
)

app_name = "dashboard"

urlpatterns = [
    # Home
    path("", DashboardHomeView.as_view(), name="home"),
    path("api/stats/", dashboard_stats_api, name="stats_api"),

    # Tours
    path("tours/", TourListView.as_view(), name="tours_list"),
    path("tours/create/", TourCreateView.as_view(), name="tours_create"),
    path("tours/<int:pk>/edit/", TourEditView.as_view(), name="tours_edit"),
    path("tours/<int:pk>/delete/", TourDeleteView.as_view(), name="tours_delete"),

    # Tour categories (the "Category" filter on the public tours page)
    path("tour-categories/", TourCategoryListView.as_view(), name="tour_categories_list"),
    path("tour-categories/create/", TourCategoryCreateView.as_view(), name="tour_categories_create"),
    path("tour-categories/<int:pk>/edit/", TourCategoryEditView.as_view(), name="tour_categories_edit"),
    path("tour-categories/<int:pk>/delete/", TourCategoryDeleteView.as_view(), name="tour_categories_delete"),

    # Ichki Turlar (domestic multi-city tours)
    path("ichki-turlar/", IchkiTurListView.as_view(), name="ichki_turlar_list"),
    path("ichki-turlar/create/", IchkiTurCreateView.as_view(), name="ichki_turlar_create"),
    path("ichki-turlar/<int:pk>/edit/", IchkiTurEditView.as_view(), name="ichki_turlar_edit"),
    path("ichki-turlar/<int:pk>/delete/", IchkiTurDeleteView.as_view(), name="ichki_turlar_delete"),

    # Domestic cities (building blocks for Ichki Tur routes)
    path("cities/", DomesticCityListView.as_view(), name="cities_list"),
    path("cities/create/", DomesticCityCreateView.as_view(), name="cities_create"),
    path("cities/<int:pk>/edit/", DomesticCityEditView.as_view(), name="cities_edit"),
    path("cities/<int:pk>/delete/", DomesticCityDeleteView.as_view(), name="cities_delete"),

    # Hero slides (rotating background images)
    path("hero/", HeroSlideListView.as_view(), name="hero_list"),
    path("hero/create/", HeroSlideCreateView.as_view(), name="hero_create"),
    path("hero/<int:pk>/edit/", HeroSlideEditView.as_view(), name="hero_edit"),
    path("hero/<int:pk>/delete/", HeroSlideDeleteView.as_view(), name="hero_delete"),

    # Hotels
    path("hotels/", HotelListView.as_view(), name="hotels_list"),
    path("hotels/create/", HotelCreateView.as_view(), name="hotels_create"),
    path("hotels/<int:pk>/edit/", HotelEditView.as_view(), name="hotels_edit"),
    path("hotels/<int:pk>/delete/", HotelDeleteView.as_view(), name="hotels_delete"),

    # Destinations
    path("destinations/", DestinationListView.as_view(), name="destinations_list"),
    path("destinations/create/", CountryCreateView.as_view(), name="destinations_create"),
    path("destinations/<int:pk>/edit/", CountryEditView.as_view(), name="destinations_edit"),
    path("destinations/<int:pk>/delete/", CountryDeleteView.as_view(), name="destinations_delete"),

    # Continents (groups countries in the Destinations mega-menu)
    path("continents/", ContinentListView.as_view(), name="continents_list"),
    path("continents/create/", ContinentCreateView.as_view(), name="continents_create"),
    path("continents/<int:pk>/edit/", ContinentEditView.as_view(), name="continents_edit"),
    path("continents/<int:pk>/delete/", ContinentDeleteView.as_view(), name="continents_delete"),

    # Bookings
    path("bookings/", BookingListView.as_view(), name="bookings_list"),
    path("bookings/export/", booking_export_csv, name="bookings_export"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="booking_detail"),

    # Articles
    path("articles/", ArticleListView.as_view(), name="articles_list"),
    path("articles/create/", ArticleCreateView.as_view(), name="articles_create"),
    path("articles/<int:pk>/edit/", ArticleEditView.as_view(), name="articles_edit"),
    path("articles/<int:pk>/delete/", ArticleDeleteView.as_view(), name="articles_delete"),

    # Quick visibility toggle (show / hide) for content records
    path("toggle-active/<str:model>/<int:pk>/", ToggleActiveView.as_view(), name="toggle_active"),

    # Reviews
    path("reviews/", ReviewListView.as_view(), name="reviews_list"),

    # Users
    path("users/", UserListView.as_view(), name="users_list"),
    path("users/create/", UserCreateView.as_view(), name="users_create"),
    path("users/<int:pk>/edit/", UserEditView.as_view(), name="users_edit"),
    path("users/<int:pk>/role/", UserRoleUpdateView.as_view(), name="users_role"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="users_delete"),
]
