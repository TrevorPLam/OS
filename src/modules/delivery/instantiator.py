"""
Template Instantiation Engine (DOC-12.1 per docs/12 section 4).

Implements deterministic template instantiation into WorkItems.

Key requirements:
- Given same template + inputs, produce identical WorkItems
- Track dependencies between WorkItems
- Support release-on-dependency-satisfied semantics
- Audit all instantiation events
"""

import uuid
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from modules.delivery.models import (
    DeliveryTemplate,
    TemplateInstantiation,
)
from modules.firm.audit import AuditEvent


class TemplateInstantiator:
    """
    Deterministic template instantiation engine.

    DOC-12.1: Instantiation MUST be deterministic given same inputs.
    """

    def __init__(self, template: DeliveryTemplate, firm, user):
        """
        Initialize instantiator.

        Args:
            template: The DeliveryTemplate to instantiate
            firm: The Firm context
            user: The user triggering instantiation
        """
        self.template = template
        self.firm = firm
        self.user = user
        self.correlation_id = str(uuid.uuid4())

    @transaction.atomic
    def instantiate(
        self,
        trigger: str,
        target_project=None,
        target_engagement=None,
        target_engagement_line=None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> TemplateInstantiation:
        """
        Instantiate template into WorkItems.

        Args:
            trigger: Instantiation trigger (engagement_activation, manual, etc.)
            target_project: Target project for task creation
            target_engagement: Target engagement (if applicable)
            target_engagement_line: Target engagement line (if applicable)
            inputs: Input values for instantiation (dates, assignees, etc.)

        Returns:
            TemplateInstantiation record

        Raises:
            ValueError: If template not published or validation fails

        DOC-12.1: Instantiation MUST be deterministic.
        """
        if self.template.status != "published":
            raise ValueError("Only published templates can be instantiated")

        # Validate template before instantiation
        validation_errors = self.template.validate_dag()
        if validation_errors:
            raise ValueError(f"Template validation failed: {validation_errors}")

        inputs = inputs or {}

        # Create instantiation record
        instantiation = TemplateInstantiation.objects.create(
            firm=self.firm,
            template=self.template,
            template_version=self.template.version,
            template_hash=self.template.validation_hash,
            trigger=trigger,
            target_engagement=target_engagement,
            target_engagement_line=target_engagement_line,
            inputs=inputs,
            status="in_progress",
            created_by=self.user,
            correlation_id=self.correlation_id,
        )

        if not target_project:
            raise ValueError("target_project is required for instantiation")

        try:
            # Instantiate nodes into Tasks
            tasks = self._create_tasks(instantiation, target_project, inputs)

            # Create dependency links
            self._create_dependencies(tasks)

            # Mark instantiation as completed
            instantiation.status = "completed"
            instantiation.save()

            # Audit the instantiation
            self._audit_instantiation(instantiation, tasks)

            return instantiation

        except Exception as e:
            # Mark instantiation as failed
            instantiation.status = "failed"
            instantiation.error_log = str(e)
            instantiation.save()
            raise

    def _create_tasks(
        self, instantiation: TemplateInstantiation, target_project, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create Tasks from template nodes.

        DOC-12.1: Each task node MUST create exactly one Task.

        Args:
            instantiation: The instantiation record
            target_project: The Project to create tasks in
            inputs: Input values for instantiation

        Returns:
            Dict mapping node_id to Task instance
        """
        from modules.projects.models import Task

        tasks = {}
        nodes = self.template.nodes.all()

        # Get activation date from inputs or use current date
        activation_date = inputs.get("activation_date")
        if isinstance(activation_date, str):
            activation_date = timezone.datetime.fromisoformat(activation_date).date()
        elif not activation_date:
            activation_date = timezone.now().date()

        for node in nodes:
            # Only create WorkItems for task and milestone nodes
            if node.type not in ["task", "milestone"]:
                continue

            # Determine assignee
            assignee = self._determine_assignee(node, inputs)

            # Determine due date
            due_date = self._calculate_due_date(node, activation_date, inputs)

            # Determine initial status
            # Nodes with dependencies start as 'blocked', others as 'todo'
            has_dependencies = self.template.edges.filter(
                to_node_id=node.node_id
            ).exists()
            initial_status = "blocked" if has_dependencies else "todo"

            # Create Task
            task = Task.objects.create(
                project=target_project,
                assigned_to=assignee,
                title=node.title,
                description=node.description,
                status=initial_status,
                due_date=due_date,
                # Template traceability (DOC-12.1 requirement)
                template_id=self.template.id,
                template_version=self.template.version,
                template_node_id=node.node_id,
                instantiation_id=instantiation.id,
                tags=node.tags,
            )

            tasks[node.node_id] = task

        return tasks

    def _determine_assignee(self, node, inputs: Dict[str, Any]):
        """
        Determine assignee for a node based on policy.

        Args:
            node: DeliveryNode instance
            inputs: Input values that may override default assignee

        Returns:
            User instance or None
        """
        # Check for input override
        assignee_overrides = inputs.get("assignee_overrides", {})
        if node.node_id in assignee_overrides:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                return User.objects.get(id=assignee_overrides[node.node_id])
            except User.DoesNotExist:
                pass

        # Use node's assignee policy
        if node.assignee_policy == "fixed":
            return node.fixed_assignee
        elif node.assignee_policy == "role_based":
            # TODO: Implement role-based assignment lookup
            # For now, return None (unassigned)
            return None
        else:
            return None

    def _calculate_due_date(self, node, activation_date, inputs: Dict[str, Any]):
        """
        Calculate due date for a node based on policy.

        Args:
            node: DeliveryNode instance
            activation_date: Base date for offset calculations
            inputs: Input values that may override due dates

        Returns:
            date instance or None
        """
        from datetime import timedelta

        # Check for input override
        due_date_overrides = inputs.get("due_date_overrides", {})
        if node.node_id in due_date_overrides:
            due_str = due_date_overrides[node.node_id]
            if isinstance(due_str, str):
                return timezone.datetime.fromisoformat(due_str).date()
            return due_str

        # Use node's due policy
        if node.due_policy == "absolute":
            # Use provided absolute date from inputs or None
            return inputs.get(f"{node.node_id}_due_date")
        elif node.due_policy == "offset_from_activation":
            return activation_date + timedelta(days=node.offset_days)
        elif node.due_policy == "offset_from_node_completion":
            # Cannot calculate at instantiation time - will be set when upstream completes
            return None
        else:
            return None

    def _create_dependencies(self, tasks: Dict[str, Any]) -> None:
        """
        Create dependency links between Tasks based on template edges.

        Args:
            tasks: Dict mapping node_id to Task instance
        """
        edges = self.template.edges.all()

        for edge in edges:
            # Only create dependencies for Tasks (skip gateways)
            if edge.from_node_id in tasks and edge.to_node_id in tasks:
                # Use the existing depends_on M2M relationship
                tasks[edge.to_node_id].depends_on.add(tasks[edge.from_node_id])

    def _audit_instantiation(
        self, instantiation: TemplateInstantiation, tasks: Dict[str, Any]
    ) -> None:
        """
        Audit template instantiation.

        DOC-12.1: Instantiation trigger MUST be auditable.
        """
        AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_DATA_ACCESS,
            action="delivery_template_instantiated",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=self.user,
            resource_type="TemplateInstantiation",
            resource_id=str(instantiation.id),
            metadata={
                "template_code": self.template.code,
                "template_version": self.template.version,
                "template_hash": self.template.validation_hash,
                "trigger": instantiation.trigger,
                "tasks_created": len(tasks),
                "correlation_id": self.correlation_id,
            },
        )
