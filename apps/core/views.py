"""Core views: home page, static pages, and utility views."""

from django.db.models import Avg, Count
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from apps.tours.models import Tour
from apps.destinations.models import Country, Continent
from apps.hotels.models import Hotel
from apps.guides.models import Article
from apps.reviews.forms import ReviewCreateForm
from apps.reviews.models import Review
from .models import FAQ


@method_decorator(ensure_csrf_cookie, name="dispatch")
class HomeView(TemplateView):
    """
    Home page view.

    Aggregates featured content from all sections and computes
    site-wide statistics for the hero counters.
    """

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Active countries for the hero search "Destination" dropdown.
        ctx["destinations"] = (
            Country.objects.filter(is_active=True).order_by("name")
        )

        ctx["featured_tours"] = (
            Tour.objects.filter(is_featured=True, is_active=True)
            .select_related("category")
            .prefetch_related("destinations")
            .order_by("order", "-created_at")[:6]
        )
        ctx["featured_destinations"] = (
            Country.objects.filter(is_featured=True, is_active=True)
            .select_related("continent")
            .annotate(num_tours=Count("tours"))
            .order_by("order")[:8]
        )
        ctx["featured_hotels"] = (
            Hotel.objects.filter(is_featured=True, is_active=True)
            .select_related("city__country")
            .order_by("order")[:4]
        )
        ctx["latest_articles"] = (
            Article.objects.filter(is_published=True, is_active=True)
            .select_related("category", "author")
            .order_by("-published_at")[:3]
        )
        featured_reviews = (
            Review.objects.filter(status="approved", is_featured=True)
            .select_related("user", "tour", "hotel")
            .prefetch_related("images")
            .order_by("-created_at")[:6]
        )
        if not featured_reviews.exists():
            featured_reviews = (
                Review.objects.filter(status="approved")
                .select_related("user", "tour", "hotel")
                .prefetch_related("images")
                .order_by("-helpful_count", "-created_at")[:6]
            )
        ctx["testimonials"] = featured_reviews
        # Empty form powering the inline "Write a Review" panel on the home page.
        ctx["review_form"] = ReviewCreateForm()

        # Site statistics
        ctx["stats"] = {
            "tours_count": Tour.objects.filter(is_active=True).count(),
            "countries_count": Country.objects.filter(is_active=True).count(),
            "years_experience": 10,
            "happy_travelers": 500,
        }
        return ctx


class AboutView(TemplateView):
    """Static about page with team and mission info."""

    template_name = "pages/about.html"


class ContactView(TemplateView):
    """Contact page with form and map."""

    template_name = "pages/contact.html"


class FAQView(TemplateView):
    """FAQ page with expandable accordion of questions and answers."""

    template_name = "pages/faq.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Prefetch
        from apps.core.models import FAQCategory, HeroSlide

        categories = FAQCategory.objects.filter(is_active=True).prefetch_related(
            Prefetch("faqs", queryset=FAQ.objects.filter(is_active=True).order_by("order"))
        ).order_by("order", "name")

        uncategorized_faqs = FAQ.objects.filter(is_active=True, category__isnull=True).order_by("order")

        ctx["categories"] = categories
        ctx["uncategorized_faqs"] = uncategorized_faqs
        ctx["total_faqs"] = FAQ.objects.filter(is_active=True).count()

        # Hero slides for FAQ page
        ctx["hero_slides"] = HeroSlide.objects.filter(
            page="faq", is_active=True
        ).order_by("order")

        return ctx



class RobotsTxtView(View):
    """Serve robots.txt."""

    def get(self, request):
        sitemap_url = request.build_absolute_uri("/sitemap.xml")
        content = (
            "User-agent: *\n"
            "Disallow: /admin/\n"
            "Disallow: /accounts/\n"
            "Disallow: /rosetta/\n"
            f"Sitemap: {sitemap_url}\n"
        )
        return HttpResponse(content, content_type="text/plain")
