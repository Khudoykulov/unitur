"""Guide / article URL patterns."""

from django.urls import path

from .views import ArticleByCategoryView, ArticleDetailView, ArticleListView

app_name = "guides"

urlpatterns = [
    path("", ArticleListView.as_view(), name="list"),
    path("category/<slug:slug>/", ArticleByCategoryView.as_view(), name="by_category"),
    path("<slug:slug>/", ArticleDetailView.as_view(), name="detail"),
]
