"""
Active Directory Synchronization URLs

API endpoint routing for AD sync management.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.ad_sync import views

app_name = 'ad_sync'

router = DefaultRouter()
router.register(r'configs', views.ADSyncConfigViewSet, basename='config')
router.register(r'logs', views.ADSyncLogViewSet, basename='log')
router.register(r'rules', views.ADProvisioningRuleViewSet, basename='rule')
router.register(r'groups', views.ADGroupMappingViewSet, basename='group')
router.register(r'users', views.ADUserMappingViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
