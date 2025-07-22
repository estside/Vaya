# healthcare_app_motihari/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as config_views # Ensure this import is correct

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('accounts/', include('users.urls')),
    path('', config_views.landing_page, name='landing_page'),
    path('about_us/', config_views.about_us, name='about_us'), # <--- NEW URL for About Us
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)