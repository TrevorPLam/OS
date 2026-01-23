"""
Jobs Module.

Provides background job queue, DLQ, and worker infrastructure.
Implements docs/03-reference/requirements/DOC-20.md WORKERS_AND_QUEUES.
"""

default_app_config = "modules.jobs.apps.JobsConfig"
