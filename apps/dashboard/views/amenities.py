"""Dashboard API views for Hotel Amenities."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.dashboard.autotranslate import autofill_translations
from apps.hotels.models import HotelAmenity


@require_POST
@login_required
def create_amenity_api(request):
    """Create a new hotel amenity via AJAX and return JSON."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        icon = data.get('icon', 'check').strip()

        if not name:
            return JsonResponse({'success': False, 'message': _('Name is required')}, status=400)

        # Check if already exists
        if HotelAmenity.objects.filter(name__iexact=name).exists():
            existing = HotelAmenity.objects.get(name__iexact=name)
            return JsonResponse({
                'success': True,
                'amenity': {'id': existing.pk, 'name': existing.name},
                'message': _('Amenity already exists')
            })

        # Create new amenity
        amenity = HotelAmenity.objects.create(name=name, icon=icon)
        try:
            autofill_translations(amenity)
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'amenity': {'id': amenity.pk, 'name': amenity.name},
            'message': _('Amenity created successfully!')
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': _('Invalid JSON')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
