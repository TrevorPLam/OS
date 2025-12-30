"""
Jobs Module.

Provides background job queue, DLQ, and worker infrastructure.
Implements docs/20 WORKERS_AND_QUEUES.
"""

default_app_config = "modules.jobs.apps.JobsConfig"
