"""Dashboard API view for Hotel Categories."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.dashboard.autotranslate import autofill_translations
from apps.hotels.models import HotelCategory


@require_POST
@login_required
def create_hotel_category_api(request):
    """Create a new hotel category via AJAX and return JSON."""
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()

        if not name:
            return JsonResponse({"success": False, "message": _("Category name is required")}, status=400)

        slug = slugify(name)
        val = slug or name.lower().replace(" ", "_")

        # Check if already exists in HotelCategory model
        existing = HotelCategory.objects.filter(name__iexact=name).first()
        if existing:
            return JsonResponse({
                "success": True,
                "category": {"val": existing.slug or val, "name": existing.name},
                "message": _("Category already exists"),
            })

        # Create new HotelCategory
        category = HotelCategory.objects.create(name=name, slug=slug)
        try:
            autofill_translations(category)
        except Exception:
            pass

        return JsonResponse({
            "success": True,
            "category": {"val": category.slug or val, "name": category.name},
            "message": _("Category created successfully!"),
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": _("Invalid JSON")}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
