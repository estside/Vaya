# healthcare_app_motihari/config/urls.py

from django.contrib import admin
from django.urls import path, include
from . import views as config_views # Assuming landing_page is in config/views.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('accounts/', include('users.urls')), # <--- Add this line for user authentication
    path('', config_views.landing_page, name='landing_page'),
]