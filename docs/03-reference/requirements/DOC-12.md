# Delivery Templates Specification (DELIVERY_TEMPLATES_SPEC)

Defines DeliveryTemplates as the human-facing plan of work (a DAG) that instantiates into WorkItems.
This is separate from orchestration (machine-enforced steps/retries).

Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. Templates MUST express repeatable delivery plans for professional-services work.
2. Templates MUST be validated at authoring time (acyclic, required fields, consistent references).
3. Instantiation MUST be deterministic given the same inputs.
4. Instantiated WorkItems MUST be traceable back to the template and node.

---

## 2) Core concepts

### 2.1 DeliveryTemplate
A versioned template for creating a set of WorkItems.

Fields (conceptual):
- template_id
- name
- version
- status (draft | published | deprecated)
- applies_to (Engagement | EngagementLine | ServiceCode | ProductCode)
- nodes[] (DeliveryNode)
- edges[] (DeliveryEdge)
- defaults (assignees, due offsets, tags)
- validation_hash/checksum

Invariants:
- Published templates MUST be immutable.
- Instantiation MUST reference template_id + version.

### 2.2 DeliveryNode
Represents a unit of planned work that becomes a WorkItem (or a gateway node that controls ordering).

Node types:
- task (becomes WorkItem)
- milestone (may become WorkItem or purely structural; choose and enforce)
- gateway (AND/OR join/split; structural only)
- approval_gate (requires approval before downstream nodes can be released)

Common node fields:
- node_id (stable within template)
- type
- title
- description (optional)
- required_fields (optional)
- assignee_policy (fixed | role_based | unassigned)
- due_policy (absolute | offset_from_activation | offset_from_node_completion)
- offset_days (if applicable)
- tags/labels (optional)

### 2.3 DeliveryEdge
Directed edge defining dependencies.
- from_node_id
- to_node_id
- condition (optional; if supported later)

---

## 3) Validation rules (MUST)

1. Graph MUST be acyclic (DAG).
2. All edges MUST reference existing nodes.
3. Node IDs MUST be unique within a template version.
4. Required fields MUST be satisfiable (no impossible requirements).
5. Gateway semantics MUST be consistent:
   - AND-join requires all upstream nodes complete
   - OR-join requires at least one upstream node complete
   (If you do not support OR in V1, forbid it explicitly.)

6. Approval gates MUST define:
   - who can approve (role/action in PERMISSIONS_MODEL.md)
   - what constitutes approval outcome

---

## 4) Instantiation semantics

### 4.1 When templates instantiate
Templates MAY instantiate:
- at Engagement activation
- at EngagementLine activation
- on-demand (staff-triggered)
- via recurrence (if recurrence targets template nodes)

Instantiation trigger MUST be auditable.

### 4.2 What gets created
1. Each task node MUST create exactly one WorkItem per instantiation.
2. Each created WorkItem MUST store:
   - template_id
   - template_version
   - template_node_id
   - instantiation_id (batch identifier)
3. If you support “release on dependency satisfied”:
   - downstream WorkItems MAY start as `planned` until dependencies satisfied, then move to `ready`.

### 4.3 Determinism
Given the same:
- template version
- target object (Engagement/EngagementLine)
- instantiation inputs (dates/assignees)
The set of WorkItems and dependency links MUST be identical.

---

## 5) Dependency execution rules

1. A WorkItem that has incomplete upstream dependencies MUST NOT be `ready` unless explicitly overridden.
2. Completion of a WorkItem MUST evaluate downstream nodes:
   - if all required upstream dependencies satisfied, downstream may be released.
3. Manual overrides MUST be permission-gated and auditable.

---

## 6) API/tooling requirements (high-level)
- Create template (draft)
- Validate template
- Publish template (locks immutability)
- Instantiate template into a target
- View instantiated graph (template overlay + runtime statuses)

---

## 7) Testing requirements
- Cycle detection
- Deterministic instantiation
- Dependency release correctness
- Approval gate enforcement
- Permission enforcement on publish/instantiate/override

---
