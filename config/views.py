# healthcare_app_motihari/config/views.py

from django.shortcuts import render

# Assuming landing_page is also defined here
def landing_page(request):
    return render(request, 'index.html')

def about_us(request):
    """
    Renders the About Us page.
    """
    return render(request, 'about_us.html')