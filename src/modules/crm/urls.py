"""
URL routes for CRM module API (Pre-Sale).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.crm.views import (
    CampaignViewSet,
    ContractViewSet,
    LeadViewSet,
    ProposalViewSet,
    ProspectViewSet,
)
from modules.crm.scoring_views import (
    ScoringRuleViewSet,
    ScoreAdjustmentViewSet,
)

router = DefaultRouter()
router.register(r"leads", LeadViewSet, basename="lead")
router.register(r"prospects", ProspectViewSet, basename="prospect")
router.register(r"campaigns", CampaignViewSet, basename="campaign")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"scoring-rules", ScoringRuleViewSet, basename="scoring-rule")
router.register(r"score-adjustments", ScoreAdjustmentViewSet, basename="score-adjustment")

urlpatterns = [
    path("", include(router.urls)),
]
