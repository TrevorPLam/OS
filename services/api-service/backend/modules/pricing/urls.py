"""
URL configuration for Pricing module (DOC-09.2).

Registers API endpoints for:
- RuleSets: Versioned pricing rule collections
- Quotes: Mutable quote drafts
- QuoteVersions: Immutable quote snapshots (audit-logged)
"""

from rest_framework.routers import DefaultRouter

from modules.pricing.views import QuoteVersionViewSet, QuoteViewSet, RuleSetViewSet

router = DefaultRouter()
router.register(r"rulesets", RuleSetViewSet, basename="ruleset")
router.register(r"quotes", QuoteViewSet, basename="quote")
router.register(r"quote-versions", QuoteVersionViewSet, basename="quoteversion")

urlpatterns = router.urls
