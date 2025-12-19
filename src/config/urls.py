"""
URL Configuration for ConsultantPro.

Organized by business domain modules.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.URLs),

    # API Endpoints (REST Framework)
    path('api/crm/', include('api.crm.urls')),
    path('api/projects/', include('api.projects.urls')),
    path('api/finance/', include('api.finance.urls')),
    path('api/documents/', include('api.documents.urls')),
    path('api/assets/', include('api.assets.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
