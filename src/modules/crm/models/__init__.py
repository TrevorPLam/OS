"""
CRM Models: Lead, Prospect, Proposal, Contract, Campaign, Pipeline, Deal.

This module handles PRE-SALE operations only (Marketing & Sales).
Post-sale Client management moved to modules.clients.

Workflow: Lead → Prospect → Proposal → (Accepted) → Client (in modules.clients)
Deal Workflow: Deal → (Won) → Project conversion

TIER 0: All CRM entities MUST belong to exactly one Firm for tenant isolation.
"""

from .accounts import Account, AccountContact, AccountRelationship
from .activities import Activity
from .leads import Lead
from .prospects import Prospect
from .campaigns import Campaign
from .proposals import Proposal
from .contracts import Contract
from .intake_forms import IntakeForm, IntakeFormField, IntakeFormSubmission
from .products import Product, ProductOption, ProductConfiguration
from .pipelines import Pipeline, PipelineStage
from .deals import Deal, DealTask, DealAssignmentRule, DealStageAutomation, DealAlert
from .enrichment import EnrichmentProvider, ContactEnrichment, EnrichmentQualityMetric

__all__ = [
    'Account',
    'AccountContact',
    'AccountRelationship',
    'Activity',
    'Lead',
    'Prospect',
    'Campaign',
    'Proposal',
    'Contract',
    'IntakeForm',
    'IntakeFormField',
    'IntakeFormSubmission',
    'Product',
    'ProductOption',
    'ProductConfiguration',
    'Pipeline',
    'PipelineStage',
    'Deal',
    'DealTask',
    'DealAssignmentRule',
    'DealStageAutomation',
    'DealAlert',
    'EnrichmentProvider',
    'ContactEnrichment',
    'EnrichmentQualityMetric',
]
