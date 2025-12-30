"""
Management command to execute erasure/anonymization requests.

Usage:
    python manage.py execute_erasure_request <request_id>

This command:
1. Loads the erasure request
2. Verifies it's approved
3. Executes anonymization
4. Updates request status
5. Creates audit events
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from modules.core.erasure import ErasureRequest, erasure_service


class Command(BaseCommand):
    help = "Execute an approved erasure/anonymization request"

    def add_arguments(self, parser):
        parser.add_argument(
            "request_id",
            type=int,
            help="ID of the erasure request to execute",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be anonymized without executing",
        )

    def handle(self, *args, **options):
        request_id = options["request_id"]
        dry_run = options.get("dry_run", False)

        try:
            request = ErasureRequest.objects.select_related("firm", "requested_by", "approved_by").get(id=request_id)
        except ErasureRequest.DoesNotExist:
            raise CommandError(f"Erasure request {request_id} does not exist")

        self.stdout.write(self.style.WARNING(f"\nErasure Request #{request.id}"))
        self.stdout.write(f"  Firm: {request.firm.name}")
        self.stdout.write(f"  Status: {request.status}")
        self.stdout.write(f"  Legal Basis: {request.get_legal_basis_display()}")
        self.stdout.write(f"  Scope: {request.get_scope_type_display()}")
        self.stdout.write(f"  Entity: {request.scope_entity_model} #{request.scope_entity_id}")
        self.stdout.write(f"  Requested by: {request.requested_by.email if request.requested_by else 'N/A'}")
        self.stdout.write(f"  Approved by: {request.approved_by.email if request.approved_by else 'N/A'}\n")

        # Verify status
        if request.status != ErasureRequest.STATUS_APPROVED:
            raise CommandError(
                f"Erasure request must be in 'approved' status to execute. "
                f"Current status: {request.status}"
            )

        # Show evaluation results
        if request.evaluation_result:
            eval_result = request.evaluation_result
            self.stdout.write(self.style.WARNING("Evaluation Results:"))

            if eval_result.get("blockers"):
                self.stdout.write(self.style.ERROR("  Blockers:"))
                for blocker in eval_result["blockers"]:
                    self.stdout.write(f"    - {blocker}")

            if eval_result.get("warnings"):
                self.stdout.write(self.style.WARNING("  Warnings:"))
                for warning in eval_result["warnings"]:
                    self.stdout.write(f"    - {warning}")

            if eval_result.get("anonymization_plan"):
                self.stdout.write("\n  Anonymization Plan:")
                plan = eval_result["anonymization_plan"]
                for entity, details in plan.items():
                    self.stdout.write(f"    {entity}: {details}")

            self.stdout.write("")

        # Load entity
        self.stdout.write("Loading entity...")
        entity = self._load_entity(request)

        if entity is None:
            raise CommandError(f"Could not load entity: {request.scope_entity_model} #{request.scope_entity_id}")

        self.stdout.write(self.style.SUCCESS(f"  Loaded: {entity}\n"))

        # Dry run
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made\n"))
            self.stdout.write("Would anonymize:")

            if request.scope_type == ErasureRequest.SCOPE_CONTACT:
                self.stdout.write(f"  first_name: {getattr(entity, 'first_name', 'N/A')} → Anonymized")
                self.stdout.write(f"  last_name: {getattr(entity, 'last_name', 'N/A')} → Contact {entity.id}")
                self.stdout.write(f"  email: {getattr(entity, 'email', 'N/A')} → anonymized.{entity.id}@redacted.local")
                self.stdout.write(f"  phone: {getattr(entity, 'phone', 'N/A')} → (empty)")

            elif request.scope_type == ErasureRequest.SCOPE_ACCOUNT:
                company_name = getattr(entity, 'company_name', getattr(entity, 'name', 'N/A'))
                self.stdout.write(f"  company_name: {company_name} → Anonymized Account {entity.id}")

            self.stdout.write("\nDry run complete. Use --execute to perform anonymization.")
            return

        # Confirm execution
        self.stdout.write(self.style.ERROR("\n⚠️  WARNING: This will permanently anonymize data!"))
        self.stdout.write("This operation cannot be undone except via backup restoration.\n")

        confirm = input("Type 'ANONYMIZE' to confirm execution: ")
        if confirm != "ANONYMIZE":
            self.stdout.write(self.style.ERROR("Execution cancelled."))
            return

        # Execute anonymization
        self.stdout.write("\nExecuting anonymization...")

        try:
            with transaction.atomic():
                request.status = ErasureRequest.STATUS_EXECUTING
                request.save()

                if request.scope_type == ErasureRequest.SCOPE_CONTACT:
                    result = erasure_service.execute_contact_anonymization(
                        contact=entity,
                        erasure_request=request,
                    )
                elif request.scope_type == ErasureRequest.SCOPE_ACCOUNT:
                    result = erasure_service.execute_account_anonymization(
                        account=entity,
                        erasure_request=request,
                    )
                else:
                    raise CommandError(f"Unsupported scope type: {request.scope_type}")

                # Update request
                request.status = ErasureRequest.STATUS_COMPLETED
                request.executed_at = result["executed_at"]
                request.execution_result = result
                request.save()

            self.stdout.write(self.style.SUCCESS("\n✓ Anonymization completed successfully!"))
            self.stdout.write(f"\nExecution Results:")
            self.stdout.write(f"  Audit Event ID: {result.get('audit_event_id')}")
            self.stdout.write(f"  Executed at: {result.get('executed_at')}")

            if result.get("anonymized_entities"):
                self.stdout.write(f"\n  Anonymized Entities:")
                for entity_type, count in result["anonymized_entities"].items():
                    self.stdout.write(f"    {entity_type}: {count}")

        except Exception as e:
            request.status = ErasureRequest.STATUS_FAILED
            request.error_message = str(e)
            request.save()

            self.stdout.write(self.style.ERROR(f"\n✗ Anonymization failed: {e}"))
            raise CommandError(f"Execution failed: {e}")

    def _load_entity(self, request):
        """Load the entity to be anonymized."""
        from django.apps import apps

        try:
            model = apps.get_model(request.scope_entity_model)
            return model.objects.get(id=request.scope_entity_id)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error loading entity: {e}"))
            return None
