# PERMISSIONS.md — Authorization Model
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: ARCHITECTURE.md

## Authorization Layers

ConsultantPro uses a multi-layered authorization model:

1. **Authentication** - Valid JWT token required
2. **Firm Membership** - User belongs to the firm
3. **Role-Based Access** - User has required role(s)
4. **Permission-Based Access** - User has specific permissions
5. **Object-Level Access** - User can access specific object
6. **Row-Level Security** - Database enforces tenant isolation

## User Types

### Platform Operators
- Platform staff (read metadata only)
- Break-glass operators (audited content access)

### Firm Users
- Firm Master Admin (Owner) - Full control, overrides
- Firm Admin - Granular permissions management
- Staff - Least privilege, permissions enabled explicitly

### Client Portal Users
- Client-scoped access only
- Cannot access firm data
- Limited to assigned projects/documents

## Permission Model

### Django Built-in Permissions
- `add_<model>`
- `change_<model>`
- `delete_<model>`
- `view_<model>`

### Custom Permissions
- `<module>.<action>_<resource>`
- Example: `crm.export_leads`, `finance.void_invoice`

### Permission Groups
- Group permissions for common role combinations
- Examples: `sales_team`, `project_managers`, `accountants`

## Role Hierarchy (Example)

```
Platform Operator (metadata only)
  ├─ Platform Admin (full platform access)
  └─ Break-Glass Operator (emergency content access)

Firm Owner (full firm access)
  ├─ Firm Admin (delegated permissions)
  │   ├─ Department Head (department scope)
  │   └─ Team Lead (team scope)
  └─ Staff (limited permissions)
      ├─ Sales Rep
      ├─ Project Manager
      └─ Accountant

Client Portal User (client-scoped only)
```

## API Permission Classes

### Django REST Framework
- `IsAuthenticated` - Requires valid JWT
- `IsFirmMember` - User belongs to firm
- `HasFirmPermission` - User has specific firm permission
- `IsOwnerOrAdmin` - User owns object or is admin

### Custom Permission Classes
```python
from rest_framework.permissions import BasePermission

class IsFirmMember(BasePermission):
    def has_permission(self, request, view):
        return request.user.firm_id == view.get_firm_id()

class HasFirmPermission(BasePermission):
    required_permission = None
    
    def has_permission(self, request, view):
        return request.user.has_perm(
            self.required_permission,
            firm=request.user.firm
        )
```

## Object-Level Permissions

### Django Guardian (Optional)
- Per-object permissions
- Useful for granular access control
- Example: Share document with specific users

### Manual Checks
```python
def has_object_permission(self, request, view, obj):
    # Object must belong to user's firm
    if obj.firm_id != request.user.firm_id:
        return False
    
    # Check ownership
    if obj.owner == request.user:
        return True
    
    # Check admin status
    if request.user.is_firm_admin:
        return True
    
    return False
```

## Break-Glass Access

### Requirements
- Reason (dropdown + text)
- Time limit (default: 1 hour, max: 24 hours)
- Approval (for production)
- Audit log entry

### Implementation
- Temporary permission elevation
- Automatic expiration
- Alert notifications to firm owner
- Review and justification required

### Audit Log Entry
```json
{
  "timestamp": "2026-01-03T12:00:00Z",
  "operator_id": 1,
  "firm_id": 456,
  "action": "break_glass_access",
  "reason": "customer_support_ticket_123",
  "duration_seconds": 3600,
  "resources_accessed": ["Document:789", "Message:101"],
  "approved_by": 2,
  "expires_at": "2026-01-03T13:00:00Z"
}
```

## Client Portal Permissions

### Default Deny
- Client users have no firm access
- Cannot list other clients
- Cannot access unassigned resources

### Explicit Grants
- Project assignments
- Document shares
- Message threads
- Invoice access

## Permission Verification

### In Views
```python
@permission_required('crm.export_leads', raise_exception=True)
def export_leads(request):
    # Implementation
    pass
```

### In Serializers
```python
class ProposalSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # Verify user has permission
        if not self.context['request'].user.has_perm('crm.create_proposal'):
            raise PermissionDenied()
        return super().create(validated_data)
```

### In Templates (Admin)
```django
{% if perms.crm.delete_lead %}
  <button>Delete Lead</button>
{% endif %}
```

## Best Practices

1. **Least Privilege** - Grant minimum necessary permissions
2. **Explicit Grants** - No implicit permissions
3. **Audit Everything** - Log all permission checks
4. **Regular Review** - Audit user permissions quarterly
5. **Separation of Duties** - Critical operations require multiple roles
6. **Time-Limited Elevation** - Temporary permissions expire automatically

## Testing Permissions

```python
def test_non_admin_cannot_delete_lead():
    user = create_user(is_admin=False)
    lead = create_lead(firm=user.firm)
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    response = client.delete(f'/api/v1/leads/{lead.id}/')
    assert response.status_code == 403
```

See module-specific documentation for detailed permission requirements.
