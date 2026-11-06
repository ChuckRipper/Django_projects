from django import forms

from .models import ReviewLog


class ReviewForm(forms.Form):
    card_id = forms.IntegerField(widget=forms.HiddenInput)
    rating = forms.TypedChoiceField(choices=ReviewLog.Rating.choices, coerce=int)
    response_ms = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput)
