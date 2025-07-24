# healthcare_app_motihari/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as config_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('accounts/', include('users.urls')),
    path('', config_views.landing_page, name='landing_page'),
    path('about_us/', config_views.about_us, name='about_us'),
    path('ai/', include('ai_assistant.urls')),
    path('chat/', include('chat.urls')), # <--- ADD THIS LINE to include chat app URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)