"""Booking and inquiry forms."""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field

from .models import Inquiry


class BookingForm(forms.ModelForm):
    """
    Tour booking form (maps to Inquiry model).

    Collects only the essentials: first name, last name, phone (required)
    and email (optional). The selected tour/departure are passed as hidden
    fields from the tour page.
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
        # tour/departure come from the page, not the user
        self.fields["tour"].required = False
        self.fields["departure"].required = False
        # Contact fields
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

    class Meta:
        model = Inquiry
        fields = [
            "inquiry_type", "first_name", "last_name",
            "email", "phone", "country_of_origin",
            "travel_date", "num_adults", "num_children",
            "budget_range", "special_requests",
        ]
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date"}),
            "special_requests": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "inquiry_type",
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
