"""Background job handlers with explicit tenant guards."""
from job_guards import require_firm_for_job, require_client_for_job
from modules.firm.utils import expire_overdue_break_glass_sessions


def expire_overdue_break_glass_sessions_job(*, firm_id=None):
    """Expire overdue break-glass sessions for a firm with firm guard."""
    firm = require_firm_for_job(firm_id)
    return expire_overdue_break_glass_sessions(firm)


def noop_client_job(*, firm_id=None, client_id=None):
    """Example job illustrating firm+client guard enforcement."""
    firm, client = require_client_for_job(firm_id, client_id)
    return f"validated firm={firm.id} client={client.id}"
