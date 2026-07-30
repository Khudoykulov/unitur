"""Public-facing review submission form."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Review


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, "getlist"):
            return files.getlist(name)
        return files.get(name)


class ReviewCreateForm(forms.ModelForm):
    """Let visitors submit a review from the public reviews page.

    Kept deliberately short: rating, the review text and who's writing. The
    review type, title, travel date and moderation status are all derived at
    save time (see ``ReviewCreateView.form_valid``) rather than asked for.
    ``tour`` is optional — pick one to tie the review to a specific trip.
    """

    images = forms.FileField(
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
        required=False,
        label=_("Rasmlar (Photos)"),
    )

    class Meta:
        model = Review
        fields = [
            "tour",
            "rating",
            "body",
            "guest_name",
        ]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{'★' * i} ({i})") for i in range(5, 0, -1)]),
            "body": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "tour": _("Tour (optional)"),
            "guest_name": _("Your name"),
            "body": _("Your review"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tour"].required = False
        self.fields["guest_name"].required = True
        # A consistent, compact look for every widget.
        base = (
            "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm "
            "focus:ring-primary focus:border-primary"
        )
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} {base}".strip()
