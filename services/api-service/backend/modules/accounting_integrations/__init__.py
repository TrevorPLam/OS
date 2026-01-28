"""
Accounting Integrations Module.

Provides integrations with accounting platforms:
- QuickBooks Online
- Xero

Features:
- OAuth 2.0 authentication
- Invoice sync (push to accounting system)
- Payment sync (pull from accounting system)
- Customer/Contact sync (bidirectional)
"""

default_app_config = 'modules.accounting_integrations.apps.AccountingIntegrationsConfig'
