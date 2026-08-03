"""Dashboard API views for Hotel Amenities."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.dashboard.autotranslate import autofill_translations
from apps.hotels.models import HotelAmenity


from django.conf import settings


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
                'amenity': {'id': existing.pk, 'name': existing.name, 'icon': existing.icon},
                'message': _('Amenity already exists')
            })

        # Create new amenity with all language fields set to initial name
        amenity = HotelAmenity(name=name, icon=icon)
        for code, lang_name in settings.LANGUAGES:
            setattr(amenity, f"name_{code}", name)
        amenity.save()

        try:
            autofill_translations(amenity, source_lang=request.LANGUAGE_CODE, overwrite=True)
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'amenity': {'id': amenity.pk, 'name': amenity.name, 'icon': amenity.icon},
            'message': _('Amenity created successfully!')
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': _('Invalid JSON')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_POST
@login_required
def update_amenity_api(request, pk):
    """Update an existing hotel amenity via AJAX."""
    try:
        from django.shortcuts import get_object_or_404
        amenity = get_object_or_404(HotelAmenity, pk=pk)
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        icon = data.get('icon', 'check').strip()

        if not name:
            return JsonResponse({'success': False, 'message': _('Name is required')}, status=400)

        # Set all language fields to the updated name so no stale translation overwrites it
        amenity.name = name
        for code, lang_name in settings.LANGUAGES:
            setattr(amenity, f"name_{code}", name)
        if icon:
            amenity.icon = icon
        amenity.save()

        try:
            autofill_translations(amenity, source_lang=request.LANGUAGE_CODE, overwrite=True)
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'amenity': {'id': amenity.pk, 'name': amenity.name, 'icon': amenity.icon},
            'message': _('Amenity updated successfully!')
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': _('Invalid JSON')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_POST
@login_required
def delete_amenity_api(request, pk):
    """Delete a hotel amenity via AJAX."""
    try:
        from django.shortcuts import get_object_or_404
        amenity = get_object_or_404(HotelAmenity, pk=pk)
        amenity_id = amenity.pk
        amenity.delete()

        return JsonResponse({
            'success': True,
            'amenity_id': amenity_id,
            'message': _('Amenity deleted successfully!')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
