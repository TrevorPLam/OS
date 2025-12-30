"""
Delivery Templates Models (DOC-12.1 per docs/12 DELIVERY_TEMPLATES_SPEC).

Implements:
- DeliveryTemplate: Versioned templates for creating WorkItems
- DeliveryNode: Individual nodes in the template DAG
- DeliveryEdge: Dependencies between nodes
- TemplateInstantiation: Tracks when templates are instantiated

TIER 0: All delivery records belong to exactly one Firm for tenant isolation.
DOC-12.1: Templates are validated as DAG and immutable when published.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class DeliveryTemplate(models.Model):
    """
    DeliveryTemplate model per docs/12 section 2.1.

    A versioned template for creating a set of WorkItems.

    Invariants:
    - Published templates MUST be immutable
    - Instantiation MUST reference template_id + version
    - Graph MUST be acyclic (DAG)
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("deprecated", "Deprecated"),
    ]

    APPLIES_TO_CHOICES = [
        ("engagement", "Engagement"),
        ("engagement_line", "EngagementLine"),
        ("service_code", "ServiceCode"),
        ("product_code", "ProductCode"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="delivery_templates",
        help_text="Firm (workspace) this template belongs to",
    )

    # Template identity
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this template",
    )
    code = models.CharField(
        max_length=100,
        help_text="Stable code identifier for this template",
    )
    version = models.IntegerField(
        default=1,
        help_text="Monotonic version number (increments on each publish)",
    )

    # Scope
    applies_to = models.CharField(
        max_length=50,
        choices=APPLIES_TO_CHOICES,
        default="engagement",
        help_text="What object type this template applies to",
    )

    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Description of this delivery template",
    )

    # Defaults
    defaults = models.JSONField(
        default=dict,
        help_text="Default values for assignees, due offsets, tags, etc.",
    )

    # Validation
    validation_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of template structure for validation",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template was published",
    )
    deprecated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template was deprecated",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_delivery_templates",
    )
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "delivery_template"
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["firm", "code", "-version"]),
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "applies_to"]),
        ]
        unique_together = [["firm", "code", "version"]]

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({self.status})"

    def compute_validation_hash(self) -> str:
        """Compute SHA-256 hash of template structure."""
        # Gather all nodes and edges in canonical order
        nodes_data = list(
            self.nodes.values("node_id", "type", "title").order_by("node_id")
        )
        edges_data = list(
            self.edges.values("from_node_id", "to_node_id").order_by(
                "from_node_id", "to_node_id"
            )
        )

        structure = {
            "nodes": nodes_data,
            "edges": edges_data,
            "defaults": self.defaults,
        }

        normalized = json.dumps(structure, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode()).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Update validation hash before saving."""
        # Don't compute hash on first save (no nodes/edges yet)
        if self.pk:
            self.validation_hash = self.compute_validation_hash()
        super().save(*args, **kwargs)

    def validate_dag(self) -> List[str]:
        """
        Validate that the template forms a valid DAG.

        Returns:
            List of validation error messages (empty if valid).

        DOC-12.1: Templates MUST be validated at authoring time.
        """
        errors = []

        # Get all nodes and edges
        nodes = {node.node_id: node for node in self.nodes.all()}
        edges = list(self.edges.values_list("from_node_id", "to_node_id"))

        # Validate edge references
        for from_id, to_id in edges:
            if from_id not in nodes:
                errors.append(f"Edge references non-existent from_node: {from_id}")
            if to_id not in nodes:
                errors.append(f"Edge references non-existent to_node: {to_id}")

        if errors:
            return errors

        # Check for cycles using DFS
        if self._has_cycle(nodes.keys(), edges):
            errors.append("Template contains a cycle (not a DAG)")

        # Validate node IDs are unique (enforced by model but check anyway)
        node_ids = [node.node_id for node in nodes.values()]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Template contains duplicate node IDs")

        # Validate approval gates have required fields
        for node in nodes.values():
            if node.type == "approval_gate":
                if not node.approval_policy:
                    errors.append(
                        f"Approval gate node {node.node_id} missing approval_policy"
                    )

        return errors

    def _has_cycle(
        self, node_ids: Set[str], edges: List[Tuple[str, str]]
    ) -> bool:
        """
        Detect cycles using DFS.

        Returns:
            True if cycle detected, False otherwise.
        """
        # Build adjacency list
        graph: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
        for from_id, to_id in edges:
            if from_id in graph and to_id in graph:
                graph[from_id].append(to_id)

        # Track visited nodes and recursion stack
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check each connected component
        for node_id in node_ids:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def publish(self, user=None) -> "DeliveryTemplate":
        """
        Publish this template, making it immutable.

        DOC-12.1: Published templates MUST be immutable.

        Returns:
            Self if already published, or raises error if validation fails.
        """
        if self.status == "published":
            return self

        # Validate template before publishing
        validation_errors = self.validate_dag()
        if validation_errors:
            raise ValidationError({"template": validation_errors})

        self.status = "published"
        self.published_at = timezone.now()
        self.validation_hash = self.compute_validation_hash()
        self.save()
        return self

    def clean(self) -> None:
        """Validate template data integrity."""
        errors = {}

        # Published templates cannot be modified
        if self.pk:
            try:
                existing = DeliveryTemplate.objects.get(pk=self.pk)
                if existing.status == "published":
                    # Check if structure changed
                    if self.compute_validation_hash() != existing.validation_hash:
                        errors["status"] = (
                            "Published templates cannot be modified. "
                            "Create a new version instead."
                        )
            except DeliveryTemplate.DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)


class DeliveryNode(models.Model):
    """
    DeliveryNode model per docs/12 section 2.2.

    Represents a unit of planned work that becomes a WorkItem.

    Node types:
    - task: Becomes WorkItem
    - milestone: May become WorkItem or structural
    - gateway: AND/OR join/split (structural only)
    - approval_gate: Requires approval before downstream release
    """

    NODE_TYPE_CHOICES = [
        ("task", "Task"),
        ("milestone", "Milestone"),
        ("gateway", "Gateway"),
        ("approval_gate", "Approval Gate"),
    ]

    ASSIGNEE_POLICY_CHOICES = [
        ("fixed", "Fixed User"),
        ("role_based", "Role-Based"),
        ("unassigned", "Unassigned"),
    ]

    DUE_POLICY_CHOICES = [
        ("absolute", "Absolute Date"),
        ("offset_from_activation", "Offset from Activation"),
        ("offset_from_node_completion", "Offset from Node Completion"),
    ]

    GATEWAY_TYPE_CHOICES = [
        ("and_join", "AND Join"),
        ("and_split", "AND Split"),
        ("or_join", "OR Join"),
        ("or_split", "OR Split"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="delivery_nodes",
    )

    # Parent template
    template = models.ForeignKey(
        DeliveryTemplate,
        on_delete=models.CASCADE,
        related_name="nodes",
    )

    # Node identity
    node_id = models.CharField(
        max_length=100,
        help_text="Stable identifier within template (e.g., 'task_01', 'gate_approval')",
    )

    # Node type
    type = models.CharField(
        max_length=20,
        choices=NODE_TYPE_CHOICES,
        default="task",
    )

    # Content
    title = models.CharField(
        max_length=255,
        help_text="Title of the work item",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the work",
    )

    # Assignment policy
    assignee_policy = models.CharField(
        max_length=20,
        choices=ASSIGNEE_POLICY_CHOICES,
        default="unassigned",
    )
    fixed_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_delivery_nodes",
        help_text="Fixed assignee (if assignee_policy=fixed)",
    )
    assignee_role = models.CharField(
        max_length=100,
        blank=True,
        help_text="Role-based assignment (if assignee_policy=role_based)",
    )

    # Due date policy
    due_policy = models.CharField(
        max_length=50,
        choices=DUE_POLICY_CHOICES,
        default="offset_from_activation",
    )
    offset_days = models.IntegerField(
        default=0,
        help_text="Offset in days for due date calculation",
    )
    upstream_node_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Node to offset from (if due_policy=offset_from_node_completion)",
    )

    # Gateway configuration
    gateway_type = models.CharField(
        max_length=20,
        choices=GATEWAY_TYPE_CHOICES,
        blank=True,
        help_text="Gateway type (if type=gateway)",
    )

    # Approval gate configuration
    approval_policy = models.JSONField(
        default=dict,
        blank=True,
        help_text="Approval policy (who can approve, conditions)",
    )

    # Tags and metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags/labels for this node",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "delivery_node"
        ordering = ["node_id"]
        indexes = [
            models.Index(fields=["firm", "template"]),
            models.Index(fields=["type"]),
        ]
        unique_together = [["template", "node_id"]]

    def __str__(self) -> str:
        return f"{self.template.name} - {self.node_id}: {self.title}"

    def clean(self) -> None:
        """Validate node data integrity."""
        errors = {}

        # Validate assignee policy consistency
        if self.assignee_policy == "fixed" and not self.fixed_assignee:
            errors["fixed_assignee"] = (
                "Fixed assignee required when assignee_policy=fixed"
            )
        if self.assignee_policy == "role_based" and not self.assignee_role:
            errors["assignee_role"] = (
                "Assignee role required when assignee_policy=role_based"
            )

        # Validate due policy consistency
        if (
            self.due_policy == "offset_from_node_completion"
            and not self.upstream_node_id
        ):
            errors["upstream_node_id"] = (
                "Upstream node ID required when due_policy=offset_from_node_completion"
            )

        # Validate gateway configuration
        if self.type == "gateway" and not self.gateway_type:
            errors["gateway_type"] = "Gateway type required when type=gateway"

        # Validate approval gate configuration
        if self.type == "approval_gate" and not self.approval_policy:
            errors["approval_policy"] = (
                "Approval policy required when type=approval_gate"
            )

        if errors:
            raise ValidationError(errors)


class DeliveryEdge(models.Model):
    """
    DeliveryEdge model per docs/12 section 2.3.

    Directed edge defining dependencies between nodes.

    DOC-12.1: All edges MUST reference existing nodes.
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="delivery_edges",
    )

    # Parent template
    template = models.ForeignKey(
        DeliveryTemplate,
        on_delete=models.CASCADE,
        related_name="edges",
    )

    # Edge definition
    from_node_id = models.CharField(
        max_length=100,
        help_text="Source node ID",
    )
    to_node_id = models.CharField(
        max_length=100,
        help_text="Target node ID",
    )

    # Optional condition (for future use)
    condition = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional condition for edge activation",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "delivery_edge"
        ordering = ["from_node_id", "to_node_id"]
        indexes = [
            models.Index(fields=["firm", "template"]),
            models.Index(fields=["from_node_id"]),
            models.Index(fields=["to_node_id"]),
        ]
        unique_together = [["template", "from_node_id", "to_node_id"]]

    def __str__(self) -> str:
        return f"{self.template.name}: {self.from_node_id} → {self.to_node_id}"

    def clean(self) -> None:
        """Validate edge data integrity."""
        errors = {}

        # Validate that from and to nodes exist in template
        if self.template_id:
            from_exists = DeliveryNode.objects.filter(
                template=self.template, node_id=self.from_node_id
            ).exists()
            to_exists = DeliveryNode.objects.filter(
                template=self.template, node_id=self.to_node_id
            ).exists()

            if not from_exists:
                errors["from_node_id"] = (
                    f"Node {self.from_node_id} does not exist in template"
                )
            if not to_exists:
                errors["to_node_id"] = (
                    f"Node {self.to_node_id} does not exist in template"
                )

        # Validate no self-loops
        if self.from_node_id == self.to_node_id:
            errors["to_node_id"] = "Self-loops are not allowed"

        if errors:
            raise ValidationError(errors)


class TemplateInstantiation(models.Model):
    """
    TemplateInstantiation model per docs/12 section 4.

    Tracks when templates are instantiated into WorkItems.

    DOC-12.1: Instantiation trigger MUST be auditable.
    DOC-12.1: Instantiation MUST be deterministic.
    """

    TRIGGER_CHOICES = [
        ("engagement_activation", "Engagement Activation"),
        ("engagement_line_activation", "EngagementLine Activation"),
        ("manual", "Manual Staff Trigger"),
        ("recurrence", "Recurrence Event"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="template_instantiations",
    )

    # Template reference
    template = models.ForeignKey(
        DeliveryTemplate,
        on_delete=models.PROTECT,
        related_name="instantiations",
    )
    template_version = models.IntegerField(
        help_text="Template version at time of instantiation",
    )
    template_hash = models.CharField(
        max_length=64,
        help_text="Template validation hash at time of instantiation",
    )

    # Instantiation context
    trigger = models.CharField(
        max_length=50,
        choices=TRIGGER_CHOICES,
        help_text="What triggered this instantiation",
    )

    # Target object (polymorphic - use generic relation or specific FKs)
    target_engagement = models.ForeignKey(
        "clients.ClientEngagement",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="template_instantiations",
    )
    target_engagement_line = models.ForeignKey(
        "clients.EngagementLine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="template_instantiations",
    )

    # Instantiation inputs (for determinism)
    inputs = models.JSONField(
        default=dict,
        help_text="Input values used for instantiation (dates, assignees, etc.)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        default="completed",
        help_text="Instantiation status (completed/failed/partial)",
    )
    error_log = models.TextField(
        blank=True,
        help_text="Error messages if instantiation failed",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="triggered_instantiations",
    )
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Correlation ID for tracking",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "delivery_template_instantiation"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "-created_at"]),
            models.Index(fields=["template", "-created_at"]),
            models.Index(fields=["target_engagement"]),
            models.Index(fields=["target_engagement_line"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.template.name} v{self.template_version} - {self.trigger}"
