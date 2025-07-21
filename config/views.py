# healthcare_app_motihari/config/views.py (or users/views.py)

from django.shortcuts import render

def landing_page(request):
    return render(request, 'index.html') # Or 'landing_page/index.html' if you use a subfolder