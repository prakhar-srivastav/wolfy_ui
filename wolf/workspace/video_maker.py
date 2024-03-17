from django import forms


def make_video():


class videoForm(forms.Form):

    affects = forms.MultipleChoiceField(
        choices=[get_affects_choices()],
        widget=forms.CheckboxSelectMultiple,
        label="Select your affects"
    )

    def get_affects_choices(self):
        