# healthcare_app_motihari/ai_assistant/forms.py

from django import forms

class SymptomCheckerForm(forms.Form):
    symptoms = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your symptoms here (e.g., "headache, fever, body aches for 2 days").'}),
        label="Describe Your Symptoms",
        help_text="Please provide a clear and concise description of your symptoms."
    )