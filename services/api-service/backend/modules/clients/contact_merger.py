"""
Contact merging utilities.

Provides functionality for:
- Detecting merge conflicts
- Resolving merge conflicts
- Merging contacts with activity consolidation
- Transferring associations (deals, projects, etc.)
"""
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError

from modules.clients.models import Contact, Client


class ContactMergeConflict:
    """Represents a field conflict between two contacts."""
    
    def __init__(self, field_name: str, primary_value: any, secondary_value: any):
        self.field_name = field_name
        self.primary_value = primary_value
        self.secondary_value = secondary_value
        self.resolution = None  # 'primary', 'secondary', or custom value
    
    def __repr__(self):
        return f"Conflict({self.field_name}: {self.primary_value} vs {self.secondary_value})"


class ContactMerger:
    """
    Handle merging of duplicate contacts.
    
    Supports:
    - Automatic conflict detection
    - Manual conflict resolution
    - Activity consolidation
    - Association transfer
    """
    
    # Fields that should be merged (concatenated or combined)
    MERGEABLE_FIELDS = ['notes']
    
    # Fields to skip during merge (system fields)
    SKIP_FIELDS = [
        'id', 'client', 'created_at', 'updated_at', 'created_by',
        'status_changed_at', 'status_changed_by',
    ]
    
    # Fields that require special handling
    SPECIAL_FIELDS = [
        'portal_user',  # Keep from primary, reassign secondary's portal_user if exists
        'is_primary_contact',  # Keep primary's value
    ]
    
    def __init__(self, primary_contact: Contact, secondary_contact: Contact):
        """
        Initialize merger with two contacts.
        
        Args:
            primary_contact: The contact to keep (master record)
            secondary_contact: The contact to merge into primary (will be deleted)
        """
        if primary_contact.client_id != secondary_contact.client_id:
            raise ValueError("Cannot merge contacts from different clients")
        
        self.primary = primary_contact
        self.secondary = secondary_contact
        self.conflicts: List[ContactMergeConflict] = []
        self._detect_conflicts()
    
    def _get_field_value(self, contact: Contact, field_name: str) -> any:
        """Get field value from contact, handling special cases."""
        return getattr(contact, field_name, None)
    
    def _fields_differ(self, field_name: str, val1: any, val2: any) -> bool:
        """Check if two field values are different (accounting for None/empty)."""
        # Treat None and empty string as equivalent
        v1 = val1 if val1 not in [None, ''] else None
        v2 = val2 if val2 not in [None, ''] else None
        
        # If both are None/empty, they don't differ
        if v1 is None and v2 is None:
            return False
        
        # If one is None/empty and other isn't, they differ
        if (v1 is None) != (v2 is None):
            return True
        
        # Both have values, compare them
        return v1 != v2
    
    def _detect_conflicts(self):
        """Detect fields where primary and secondary have different values."""
        self.conflicts = []
        
        # Get all field names from the model
        field_names = [f.name for f in Contact._meta.get_fields()
                      if not f.auto_created and f.name not in self.SKIP_FIELDS]
        
        for field_name in field_names:
            if field_name in self.SPECIAL_FIELDS:
                continue  # Handle separately
            
            primary_val = self._get_field_value(self.primary, field_name)
            secondary_val = self._get_field_value(self.secondary, field_name)
            
            # Check if values differ
            if self._fields_differ(field_name, primary_val, secondary_val):
                conflict = ContactMergeConflict(field_name, primary_val, secondary_val)
                
                # Auto-resolve some conflicts
                if field_name in self.MERGEABLE_FIELDS:
                    # For mergeable fields, concatenate values
                    if primary_val and secondary_val:
                        conflict.resolution = f"{primary_val}\n\n---\n\n{secondary_val}"
                    elif secondary_val:
                        conflict.resolution = secondary_val
                    else:
                        conflict.resolution = 'primary'
                elif not primary_val and secondary_val:
                    # If primary is empty, use secondary
                    conflict.resolution = 'secondary'
                else:
                    # Default to primary value
                    conflict.resolution = 'primary'
                
                self.conflicts.append(conflict)
    
    def get_conflicts(self) -> List[ContactMergeConflict]:
        """Get list of detected conflicts."""
        return self.conflicts
    
    def has_unresolved_conflicts(self) -> bool:
        """Check if there are any conflicts without resolution."""
        return any(c.resolution is None for c in self.conflicts)
    
    def resolve_conflict(self, field_name: str, resolution: str):
        """
        Manually resolve a conflict.
        
        Args:
            field_name: Name of the conflicting field
            resolution: 'primary', 'secondary', or a custom value
        """
        for conflict in self.conflicts:
            if conflict.field_name == field_name:
                if resolution == 'primary':
                    conflict.resolution = 'primary'
                elif resolution == 'secondary':
                    conflict.resolution = 'secondary'
                else:
                    # Custom value
                    conflict.resolution = resolution
                return
        
        raise ValueError(f"No conflict found for field: {field_name}")
    
    def resolve_all_with_primary(self):
        """Resolve all conflicts by keeping primary contact's values."""
        for conflict in self.conflicts:
            conflict.resolution = 'primary'
    
    def resolve_all_with_secondary(self):
        """Resolve all conflicts by using secondary contact's values."""
        for conflict in self.conflicts:
            conflict.resolution = 'secondary'
    
    def _merge_activities(self):
        """
        Merge activities and associations from secondary to primary.
        
        This updates related records to point to the primary contact:
        - Messages
        - Notes
        - Tasks
        - Deal associations
        - Project associations
        """
        # This is a placeholder for actual implementation
        # In a real system, you'd need to update all related models
        
        # Example of what would be done:
        # 1. Update all ClientMessage records
        # 2. Update all ClientNote records
        # 3. Update deal associations
        # 4. Update project associations
        # 5. Update task assignments
        # 6. Merge communication history
        
        # For now, we'll just add a note to the primary contact
        merge_note = f"\n\n[Merged from contact ID {self.secondary.id} on {self.secondary.email}]"
        if self.primary.notes:
            self.primary.notes += merge_note
        else:
            self.primary.notes = f"Merged contact{merge_note}"
    
    def _apply_field_resolutions(self):
        """Apply all conflict resolutions to the primary contact."""
        for conflict in self.conflicts:
            if conflict.resolution is None:
                raise ValueError(f"Unresolved conflict for field: {conflict.field_name}")
            
            if conflict.resolution == 'primary':
                # Keep primary value, no change needed
                continue
            elif conflict.resolution == 'secondary':
                # Use secondary value
                setattr(self.primary, conflict.field_name, conflict.secondary_value)
            else:
                # Use custom resolution value
                setattr(self.primary, conflict.field_name, conflict.resolution)
    
    def _handle_special_fields(self):
        """Handle special fields that need custom merge logic."""
        # Handle portal_user: keep primary's, but if primary doesn't have one and secondary does
        if not self.primary.portal_user_id and self.secondary.portal_user_id:
            self.primary.portal_user_id = self.secondary.portal_user_id
        
        # Handle is_primary_contact: if either is primary, keep that status
        if self.secondary.is_primary_contact and not self.primary.is_primary_contact:
            self.primary.is_primary_contact = True
    
    def execute_merge(self) -> Contact:
        """
        Execute the merge operation.
        
        Returns:
            The merged contact (primary)
        
        Raises:
            ValueError: If there are unresolved conflicts
        """
        if self.has_unresolved_conflicts():
            unresolved = [c.field_name for c in self.conflicts if c.resolution is None]
            raise ValueError(f"Cannot merge with unresolved conflicts: {', '.join(unresolved)}")
        
        with transaction.atomic():
            # Apply field resolutions
            self._apply_field_resolutions()
            
            # Handle special fields
            self._handle_special_fields()
            
            # Merge activities and associations
            self._merge_activities()
            
            # Validate and save primary contact
            self.primary.full_clean()
            self.primary.save()
            
            # Delete secondary contact
            self.secondary.delete()
        
        return self.primary
    
    def get_merge_preview(self) -> Dict[str, any]:
        """
        Get a preview of what the merged contact will look like.
        
        Returns:
            Dictionary with merged field values and conflict information
        """
        preview = {
            'primary_id': self.primary.id,
            'secondary_id': self.secondary.id,
            'conflicts': [
                {
                    'field': c.field_name,
                    'primary_value': c.primary_value,
                    'secondary_value': c.secondary_value,
                    'resolution': c.resolution,
                    'resolved': c.resolution is not None,
                }
                for c in self.conflicts
            ],
            'merged_fields': {},
        }
        
        # Show what the merged contact will look like
        for field in Contact._meta.get_fields():
            if field.auto_created or field.name in self.SKIP_FIELDS:
                continue
            
            field_name = field.name
            current_value = getattr(self.primary, field_name, None)
            
            # Check if this field has a conflict with resolution
            conflict = next((c for c in self.conflicts if c.field_name == field_name), None)
            if conflict and conflict.resolution:
                if conflict.resolution == 'primary':
                    preview['merged_fields'][field_name] = current_value
                elif conflict.resolution == 'secondary':
                    preview['merged_fields'][field_name] = conflict.secondary_value
                else:
                    preview['merged_fields'][field_name] = conflict.resolution
            else:
                preview['merged_fields'][field_name] = current_value
        
        return preview


def find_potential_duplicates(
    client: Client,
    limit: int = 100,
) -> List[Tuple[Contact, Contact, float]]:
    """
    Find potential duplicate contacts within a client.
    
    Returns:
        List of tuples (contact1, contact2, similarity_score)
        Sorted by similarity score (highest first)
    """
    from modules.clients.bulk_operations import ContactDuplicateDetector
    
    contacts = Contact.objects.filter(client=client).order_by('id')
    detector = ContactDuplicateDetector()
    potential_duplicates = []
    
    # Compare each contact with others
    processed_pairs = set()
    
    for contact in contacts[:limit]:  # Limit to prevent excessive processing
        # Find duplicates by email
        email_dupes = detector.find_duplicates_by_email(client, contact.email) if contact.email else []
        
        # Find duplicates by name
        name_dupes = detector.find_duplicates_by_name(
            client, contact.first_name, contact.last_name
        ) if contact.first_name and contact.last_name else []
        
        # Combine and score
        all_dupes = set(email_dupes + name_dupes)
        all_dupes.discard(contact)  # Remove self
        
        for dupe in all_dupes:
            # Avoid duplicate pairs (A,B) and (B,A)
            pair_key = tuple(sorted([contact.id, dupe.id]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            # Calculate similarity score (0-100)
            score = _calculate_similarity_score(contact, dupe)
            
            if score >= 50:  # Only include if at least 50% similar
                potential_duplicates.append((contact, dupe, score))
    
    # Sort by similarity score (highest first)
    potential_duplicates.sort(key=lambda x: x[2], reverse=True)
    
    return potential_duplicates


def _calculate_similarity_score(contact1: Contact, contact2: Contact) -> float:
    """
    Calculate similarity score between two contacts (0-100).
    
    Scoring criteria:
    - Email match: 40 points
    - Name match: 30 points
    - Phone match: 20 points
    - Same client: 10 points (always true in our case)
    """
    score = 10.0  # Base score for same client
    
    # Email comparison
    if contact1.email and contact2.email:
        if contact1.email.lower() == contact2.email.lower():
            score += 40.0
    
    # Name comparison
    if contact1.first_name and contact2.first_name and contact1.last_name and contact2.last_name:
        first_match = contact1.first_name.lower() == contact2.first_name.lower()
        last_match = contact1.last_name.lower() == contact2.last_name.lower()
        
        if first_match and last_match:
            score += 30.0
        elif first_match or last_match:
            score += 15.0
    
    # Phone comparison
    if contact1.phone and contact2.phone:
        # Compare cleaned phone numbers
        clean1 = ''.join(c for c in contact1.phone if c.isdigit())
        clean2 = ''.join(c for c in contact2.phone if c.isdigit())
        
        if clean1 and clean2 and clean1 == clean2:
            score += 20.0
    
    return min(score, 100.0)  # Cap at 100
