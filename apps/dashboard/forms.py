"""Dashboard forms."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.core.models import FAQ, FAQCategory, HeroSlide
from apps.destinations.models import Attraction, City, Continent, Country
from apps.hotels.models import Hotel, HotelCategory
from apps.tours.models import Tour, TourCategory, TourDay, TourStop


class AttractionForm(forms.ModelForm):
    """Form for creating and editing attractions (Diqqatga sazovor joylar)."""

    class Meta:
        model = Attraction
        fields = [
            "name", "city", "category", "image", "description",
            "entrance_fee", "opening_hours", "google_maps_url", "is_active",
        ]


class HotelForm(forms.ModelForm):
    """Form for creating and editing hotels with dynamic category choices."""

    class Meta:
        model = Hotel
        fields = [
            "name", "city", "category", "stars", "cover_image",
            "address", "latitude", "longitude", "phone", "email",
            "website", "description", "amenities",
            "check_in_time", "check_out_time", "price_from",
        ]
        widgets = {
            "amenities": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(Hotel.CATEGORY_CHOICES)
        existing_keys = {c[0] for c in choices}

        for cat in HotelCategory.objects.all():
            key = cat.slug or cat.name.lower().replace(" ", "_")
            if key not in existing_keys:
                choices.append((key, cat.name))
                existing_keys.add(key)

        used_cats = Hotel.objects.values_list("category", flat=True).distinct()
        for c in used_cats:
            if c and c not in existing_keys:
                choices.append((c, c.title()))
                existing_keys.add(c)

        self.fields["category"].widget = forms.Select(choices=choices)
from apps.hotels.models import Hotel, HotelCategory
from apps.tours.models import Tour, TourCategory, TourDay, TourStop

User = get_user_model()

# Domestic ("Ichki Turlar") tours are built from Uzbek cities. Matched by name
# so the link survives slug/id changes (mirrors apps.ichki_turlar.admin).
DOMESTIC_COUNTRY = "Uzbek"

ROLE_CHOICES = [
    ("user", _("User — public site only")),
    ("operator", _("Operator — bookings & reviews")),
    ("manager", _("Manager — full content management")),
    ("superuser", _("Superuser — full access")),
]


class UserCreateForm(forms.Form):
    """Create a new account from the dashboard and assign a role.

    The site logs in by email, so the email doubles as the username. Role is
    applied separately (see ``apply_role``) since it maps to flags/groups
    rather than model fields.
    """

    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(label=_("First name"), max_length=150, required=False)
    last_name = forms.CharField(label=_("Last name"), max_length=150, required=False)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, min_length=8)
    role = forms.ChoiceField(label=_("Role"), choices=ROLE_CHOICES, initial="user")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(
            username__iexact=email
        ).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self):
        data = self.cleaned_data
        user = User(
            username=data["email"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        user.set_password(data["password"])
        user.save()
        return user


class UserEditForm(forms.ModelForm):
    """Edit an existing account's details, role and (optionally) password.

    Email doubles as the login username, so the two are kept in sync. Password
    is only changed when a new value is supplied.
    """

    role = forms.ChoiceField(label=_("Role"), choices=ROLE_CHOICES)
    password = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput,
        required=False,
        min_length=8,
        help_text=_("Leave blank to keep the current password."),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active"]
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "is_active": _("Active (can log in)"),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        clash = (
            User.objects.filter(email__iexact=email)
            | User.objects.filter(username__iexact=email)
        ).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError(_("Another user with this email already exists."))
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class IchkiTurForm(forms.ModelForm):
    """Create/edit a domestic multi-city tour ("Ichki Tur").

    The itinerary stops (which make it multi-city) are handled by the
    ``TourStopFormSet`` alongside this form.
    """

    class Meta:
        model = Tour
        # Difficulty is intentionally omitted: domestic city tours don't need a
        # difficulty rating (it stays at the model default).
        fields = [
            "title", "category", "duration_days",
            "group_size_min", "group_size_max",
            "price_per_person", "price_currency", "discount_percent",
            "cover_image", "overview", "includes", "excludes",
            "important_notes",
        ]


class TourStopForm(forms.ModelForm):
    """A single itinerary stop, restricted to domestic (Uzbek) cities."""

    class Meta:
        model = TourStop
        fields = ["city", "order", "nights"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Match on the language-independent English name; under modeltranslation
        # ``country__name`` would resolve to the active language (e.g. name_uz =
        # "O'zbekiston") and never contain "Uzbek".
        self.fields["city"].queryset = City.objects.filter(
            country__name_en__icontains=DOMESTIC_COUNTRY
        ).order_by("name")


# At least two stops are required — that is what makes a tour "Ichki Turlar".
TourStopFormSet = inlineformset_factory(
    Tour,
    TourStop,
    form=TourStopForm,
    extra=2,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


class TourDayForm(forms.ModelForm):
    """A single day of the day-by-day itinerary (mirrors TourStopForm)."""

    class Meta:
        model = TourDay
        fields = [
            "day_number", "title", "description",
            "meals_included", "accommodation", "transport", "image",
        ]


# The day-by-day itinerary is optional supplementary content (the tour detail
# page renders it only when days exist), so no minimum is enforced — unlike
# stops, requiring a day would block editing existing tours that have none.
TourDayFormSet = inlineformset_factory(
    Tour,
    TourDay,
    form=TourDayForm,
    extra=1,
    can_delete=True,
)


class DomesticCityForm(forms.ModelForm):
    """Create/edit a domestic (Uzbek) city used to build Ichki Tur routes.

    New cities are always attached to Uzbekistan, so the country isn't shown.
    The country assignment is handled by DomesticCityCreateView.form_valid().
    """

    class Meta:
        model = City
        # is_featured, order and is_active are omitted: featured/order have no
        # effect for cities (listed alphabetically), and visibility is toggled
        # from the city list, not this form.
        fields = ["name", "cover_image", "overview"]


class TourCategoryForm(forms.ModelForm):
    """Create/edit a tour category (the "Category" filter on the tours page)."""

    class Meta:
        model = TourCategory
        # ``order`` is omitted — it stays at the model default (creation order);
        # visibility isn't a concept for categories, so no is_active either.
        fields = ["name", "icon", "description", "image"]
        help_texts = {
            "icon": _("Tabler icon name, e.g. compass, building, beach, chef-hat, paw."),
        }


class ContinentForm(forms.ModelForm):
    """Create/edit a continent (groups countries in the Destinations menu)."""

    class Meta:
        model = Continent
        fields = ["name", "image"]


class FAQCategoryForm(forms.ModelForm):
    """Create/edit a category for FAQs."""

    class Meta:
        model = FAQCategory
        fields = ["name", "icon", "description", "order", "is_active"]
        help_texts = {
            "icon": _("Tabler icon name, e.g. help, credit-card, map-pin, passport, info-circle."),
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Booking & Payment"}),
            "icon": forms.TextInput(attrs={"placeholder": "e.g. credit-card"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Category description (optional)"}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }


class FAQForm(forms.ModelForm):
    """Create/edit a FAQ item."""

    class Meta:
        model = FAQ
        fields = ["category", "question", "answer", "order", "is_active"]
        widgets = {
            "question": forms.TextInput(attrs={"placeholder": "e.g. How do I book a tour?"}),
            "answer": forms.Textarea(attrs={"rows": 5, "placeholder": "Detailed answer..."}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }


class HeroSlideForm(forms.ModelForm):
    """Upload a rotating hero background image for a page."""

    class Meta:
        model = HeroSlide
        fields = ["page", "image", "alt", "order", "is_active"]
        widgets = {
            "alt": forms.TextInput(attrs={"placeholder": "Image description (optional)"}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order"].required = False
        if self.instance and self.instance.pk:
            self.fields["image"].required = False


class HotelForm(forms.ModelForm):
    """Form for creating and editing hotels with dynamic category choices."""

    class Meta:
        model = Hotel
        fields = [
            "name", "city", "category", "stars", "cover_image",
            "address", "latitude", "longitude", "phone", "email",
            "website", "description", "amenities",
            "check_in_time", "check_out_time", "price_from",
        ]
        widgets = {
            "amenities": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(Hotel.CATEGORY_CHOICES)
        existing_keys = {c[0] for c in choices}

        for cat in HotelCategory.objects.all():
            key = cat.slug or cat.name.lower().replace(" ", "_")
            if key not in existing_keys:
                choices.append((key, cat.name))
                existing_keys.add(key)

        used_cats = Hotel.objects.values_list("category", flat=True).distinct()
        for c in used_cats:
            if c and c not in existing_keys:
                choices.append((c, c.title()))
                existing_keys.add(c)

        self.fields["category"].widget = forms.Select(choices=choices)


