"""Guards for background jobs to enforce firm/client context."""

from modules.clients.models import Client
from modules.firm.models import Firm
from modules.firm.utils import FirmScopingError


def require_firm_for_job(firm_id):
    """Resolve and return the firm for a job, raising when context is missing."""
    if not firm_id:
        raise FirmScopingError("Background jobs require a firm_id for tenant isolation.")

    try:
        return Firm.objects.get(id=firm_id)
    except Firm.DoesNotExist as exc:
        raise FirmScopingError(f"Firm {firm_id} is not available for job execution.") from exc


def require_client_for_job(firm_id, client_id):
    """Resolve client and firm for a job, enforcing tenant boundaries."""
    firm = require_firm_for_job(firm_id)

    if not client_id:
        raise FirmScopingError("Background jobs require a client_id when operating on client data.")

    try:
        client = Client.objects.get(id=client_id, firm=firm)
    except Client.DoesNotExist as exc:
        raise FirmScopingError(f"Client {client_id} is not available for firm {firm_id} in job execution.") from exc

    return firm, client
