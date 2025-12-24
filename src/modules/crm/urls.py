"""
URL routes for CRM module API (Pre-Sale).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from modules.crm.views import (
    LeadViewSet,
    ProspectViewSet,
    CampaignViewSet,
    ProposalViewSet,
    ContractViewSet,
)

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'prospects', ProspectViewSet, basename='prospect')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'proposals', ProposalViewSet, basename='proposal')
router.register(r'contracts', ContractViewSet, basename='contract')

urlpatterns = [
    path('', include(router.urls)),
]
