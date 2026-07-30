"""Booking and inquiry forms."""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field

from .models import Inquiry


class BookingForm(forms.ModelForm):
    """
    Tour booking form (maps to Inquiry model).

    Collects essentials: first name, last name, phone, email.
    The tour's category is automatically captured from the selected tour.
    """

    class Meta:
        model = Inquiry
        fields = ["tour", "departure", "first_name", "last_name", "phone", "email"]
        widgets = {
            "tour": forms.HiddenInput(),
            "departure": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tour"].required = False
        self.fields["departure"].required = False
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = False
        self.fields["email"].help_text = _("Optional")
        self.fields["first_name"].widget.attrs.setdefault("placeholder", _("First name"))
        self.fields["last_name"].widget.attrs.setdefault("placeholder", _("Last name"))
        self.fields["phone"].widget.attrs.setdefault("placeholder", "+998 90 123 45 67")
        self.fields["email"].widget.attrs.setdefault("placeholder", "you@example.com")

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("tour"),
            Field("departure"),
            Row(
                Column("first_name", css_class="col-md-6"),
                Column("last_name", css_class="col-md-6"),
            ),
            Row(
                Column("phone", css_class="col-md-6"),
                Column("email", css_class="col-md-6"),
            ),
            Submit("submit", _("Confirm Booking"), css_class="btn-primary"),
        )


class InquiryForm(forms.ModelForm):
    """Generic inquiry / contact form."""

    category_choice = forms.ChoiceField(
        label=_("Tur kategoriyasi (Category)"),
        required=False,
    )
    custom_category = forms.CharField(
        label=_("Boshqa kategoriya (Custom category)"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Kategoriya nomini kiriting..."), "class": "form-control"}),
    )

    class Meta:
        model = Inquiry
        fields = [
            "inquiry_type", "category", "custom_category", "first_name", "last_name",
            "email", "phone", "country_of_origin",
            "travel_date", "num_adults", "num_children",
            "budget_range", "special_requests",
        ]
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date"}),
            "special_requests": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.tours.models import TourCategory
        categories = TourCategory.objects.all()
        choices = [("", _("-- Tur kategoriyasini tanlang --"))]
        for cat in categories:
            choices.append((str(cat.pk), cat.name))
        choices.append(("other", _("Boshqa (Kategoriyani o'zim kiritaman)")))
        self.fields["category_choice"].choices = choices

        if self.initial.get("category"):
            self.fields["category_choice"].initial = str(self.initial["category"])
        elif self.initial.get("custom_category"):
            self.fields["category_choice"].initial = "other"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("inquiry_type", css_class="col-md-6"),
                Column("category_choice", css_class="col-md-6"),
            ),
            Row(
                Column("custom_category", css_class="col-md-12", id="custom_category_col"),
            ),
            Row(
                Column("first_name", css_class="col-md-6"),
                Column("last_name", css_class="col-md-6"),
            ),
            Row(
                Column("email", css_class="col-md-6"),
                Column("phone", css_class="col-md-6"),
            ),
            Row(
                Column("country_of_origin", css_class="col-md-6"),
                Column("travel_date", css_class="col-md-6"),
            ),
            Row(
                Column("num_adults", css_class="col-md-4"),
                Column("num_children", css_class="col-md-4"),
                Column("budget_range", css_class="col-md-4"),
            ),
            "special_requests",
            Submit("submit", _("Send Inquiry"), css_class="btn-primary"),
        )

    def clean(self):
        cleaned_data = super().clean()
        cat_choice = cleaned_data.get("category_choice")
        cust_cat = cleaned_data.get("custom_category", "").strip()

        if cat_choice and cat_choice != "other":
            try:
                from apps.tours.models import TourCategory
                cleaned_data["category"] = TourCategory.objects.get(pk=cat_choice)
                cleaned_data["custom_category"] = ""
            except (ValueError, TourCategory.DoesNotExist):
                cleaned_data["category"] = None
        elif cat_choice == "other":
            cleaned_data["category"] = None
            cleaned_data["custom_category"] = cust_cat
        return cleaned_data
