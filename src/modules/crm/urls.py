"""
URL routes for CRM module API (Pre-Sale).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.crm.views import (
    AccountContactViewSet,
    AccountRelationshipViewSet,
    AccountViewSet,
    CampaignViewSet,
    ContactEnrichmentViewSet,
    ContractViewSet,
    DealTaskViewSet,
    DealViewSet,
    EnrichmentProviderViewSet,
    EnrichmentQualityMetricViewSet,
    IntakeFormViewSet,
    IntakeFormFieldViewSet,
    IntakeFormSubmissionViewSet,
    LeadViewSet,
    PipelineStageViewSet,
    PipelineViewSet,
    ProductConfigurationViewSet,
    ProductOptionViewSet,
    ProductViewSet,
    ProposalViewSet,
    ProspectViewSet,
)
from modules.crm.scoring_views import (
    ScoringRuleViewSet,
    ScoreAdjustmentViewSet,
)

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"account-contacts", AccountContactViewSet, basename="account-contact")
router.register(r"account-relationships", AccountRelationshipViewSet, basename="account-relationship")
router.register(r"leads", LeadViewSet, basename="lead")
router.register(r"prospects", ProspectViewSet, basename="prospect")
router.register(r"campaigns", CampaignViewSet, basename="campaign")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"scoring-rules", ScoringRuleViewSet, basename="scoring-rule")
router.register(r"score-adjustments", ScoreAdjustmentViewSet, basename="score-adjustment")
router.register(r"intake-forms", IntakeFormViewSet, basename="intake-form")  # Task 3.4
router.register(r"intake-form-fields", IntakeFormFieldViewSet, basename="intake-form-field")  # Task 3.4
router.register(r"intake-form-submissions", IntakeFormSubmissionViewSet, basename="intake-form-submission")  # Task 3.4
router.register(r"products", ProductViewSet, basename="product")  # Task 3.5 (CPQ)
router.register(r"product-options", ProductOptionViewSet, basename="product-option")  # Task 3.5 (CPQ)
router.register(r"product-configurations", ProductConfigurationViewSet, basename="product-configuration")  # Task 3.5 (CPQ)
router.register(r"pipelines", PipelineViewSet, basename="pipeline")  # DEAL-1: Pipeline Management
router.register(r"pipeline-stages", PipelineStageViewSet, basename="pipeline-stage")  # DEAL-1: Pipeline Stages
router.register(r"deals", DealViewSet, basename="deal")  # DEAL-1: Deal Management
router.register(r"deal-tasks", DealTaskViewSet, basename="deal-task")  # DEAL-2: Deal Tasks
router.register(r"enrichment-providers", EnrichmentProviderViewSet, basename="enrichment-provider")  # CRM-INT-3: Enrichment Providers
router.register(r"contact-enrichments", ContactEnrichmentViewSet, basename="contact-enrichment")  # CRM-INT-3: Contact Enrichment Data
router.register(r"enrichment-quality-metrics", EnrichmentQualityMetricViewSet, basename="enrichment-quality-metric")  # CRM-INT-3: Quality Metrics

urlpatterns = [
    path("", include(router.urls)),
]
