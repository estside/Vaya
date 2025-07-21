# healthcare_app_motihari/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static
from . import views as config_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('accounts/', include('users.urls')),
    path('', config_views.landing_page, name='landing_page'),
]

# --- NEW: Serve media files during development ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# -------------------------------------------------