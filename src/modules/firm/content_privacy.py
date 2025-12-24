"""
Content Privacy Utilities (TIER 0.5)

Utilities for enforcing metadata-only access for platform operators.
These utilities help identify and filter content fields from API responses.
"""
from typing import List, Dict, Any, Optional


def get_content_fields(model_class) -> List[str]:
    """
    Get list of content fields for a model.
    
    Content fields are protected from platform operators and require
    break-glass access.
    
    Args:
        model_class: Django model class
        
    Returns:
        List of field names that contain protected content
    """
    if hasattr(model_class, 'CONTENT_FIELDS'):
        return model_class.CONTENT_FIELDS
    return []


def filter_content_fields(data: Dict[str, Any], model_class) -> Dict[str, Any]:
    """
    Remove content fields from a dictionary (for platform operators).
    
    This is used to filter API responses when the requester is a
    platform operator with metadata-only access.
    
    Args:
        data: Dictionary of model data
        model_class: Django model class
        
    Returns:
        Dictionary with content fields removed/redacted
    """
    content_fields = get_content_fields(model_class)
    filtered_data = data.copy()
    
    for field in content_fields:
        if field in filtered_data:
            # Replace content with redaction marker
            filtered_data[field] = '[REDACTED - REQUIRES BREAK-GLASS]'
    
    return filtered_data


def is_content_field(model_class, field_name: str) -> bool:
    """
    Check if a field is marked as content (protected).
    
    Args:
        model_class: Django model class
        field_name: Name of the field to check
        
    Returns:
        True if field contains protected content
    """
    content_fields = get_content_fields(model_class)
    return field_name in content_fields


# Registry of models with content fields
# This is used by admin interfaces and API documentation
CONTENT_BEARING_MODELS = [
    'documents.Document',
    'documents.Folder', 
    'documents.Version',
    'crm.Lead',
    'crm.Prospect',
    'crm.Proposal',
    'crm.Contract',
    'finance.Invoice',
    'finance.Bill',
    'projects.Project',
    'projects.Task',
    'projects.TimeEntry',
]


def get_metadata_only_queryset(queryset, user):
    """
    Return a queryset that will filter content fields for platform operators.
    
    This is a placeholder - the actual filtering happens in serializers.
    This function exists to make the intent clear in views.
    
    Args:
        queryset: Django queryset
        user: Request user
        
    Returns:
        Queryset (content filtering happens at serialization)
    """
    # Note: We can't filter at the queryset level because we need to
    # show that records exist but redact their content.
    # The actual filtering happens in serializers using filter_content_fields()
    return queryset


def add_content_field_markers(model_class, fields: List[str]):
    """
    Helper to add CONTENT_FIELDS to a model class dynamically.
    
    This is useful for models that don't have it defined yet.
    
    Args:
        model_class: Django model class
        fields: List of field names to mark as content
    """
    if not hasattr(model_class, 'CONTENT_FIELDS'):
        model_class.CONTENT_FIELDS = fields
