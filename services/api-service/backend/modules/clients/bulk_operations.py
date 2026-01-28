"""
Contact bulk operations utilities.

Provides functionality for:
- CSV/Excel import with field mapping
- Duplicate detection and merging
- Bulk updates
"""
import csv
import io
from typing import Dict, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from modules.clients.models import Client, Contact, ContactImport, ContactBulkUpdate


class ContactDuplicateDetector:
    """Detect duplicate contacts based on various matching strategies."""
    
    @staticmethod
    def find_duplicates_by_email(client: Client, email: str) -> List[Contact]:
        """Find contacts with matching email in the same client."""
        return list(Contact.objects.filter(
            client=client,
            email__iexact=email,
        ))
    
    @staticmethod
    def find_duplicates_by_name(
        client: Client,
        first_name: str,
        last_name: str,
    ) -> List[Contact]:
        """Find contacts with matching name in the same client."""
        return list(Contact.objects.filter(
            client=client,
            first_name__iexact=first_name,
            last_name__iexact=last_name,
        ))
    
    @staticmethod
    def find_duplicates_by_phone(client: Client, phone: str) -> List[Contact]:
        """Find contacts with matching phone number in the same client."""
        if not phone:
            return []
        # Remove common phone formatting characters for comparison
        clean_phone = ''.join(c for c in phone if c.isdigit())
        if not clean_phone:
            return []
        
        # Find contacts and filter by cleaned phone number
        contacts = Contact.objects.filter(
            client=client,
            phone__isnull=False,
        ).exclude(phone='')
        
        duplicates = []
        for contact in contacts:
            contact_clean_phone = ''.join(c for c in contact.phone if c.isdigit())
            if contact_clean_phone == clean_phone:
                duplicates.append(contact)
        
        return duplicates
    
    @staticmethod
    def find_best_match(
        client: Client,
        email: str,
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
    ) -> Optional[Contact]:
        """
        Find the best matching contact based on multiple criteria.
        
        Priority:
        1. Exact email match (most reliable)
        2. Name + phone match
        3. Name match only
        """
        # Priority 1: Email match
        if email:
            email_matches = ContactDuplicateDetector.find_duplicates_by_email(client, email)
            if email_matches:
                return email_matches[0]
        
        # Priority 2: Name + phone match
        if first_name and last_name and phone:
            name_matches = ContactDuplicateDetector.find_duplicates_by_name(
                client, first_name, last_name
            )
            phone_matches = ContactDuplicateDetector.find_duplicates_by_phone(client, phone)
            
            # Find intersection
            name_ids = {c.id for c in name_matches}
            for contact in phone_matches:
                if contact.id in name_ids:
                    return contact
        
        # Priority 3: Name match only
        if first_name and last_name:
            name_matches = ContactDuplicateDetector.find_duplicates_by_name(
                client, first_name, last_name
            )
            if name_matches:
                return name_matches[0]
        
        return None


class ContactImporter:
    """Handle CSV/Excel import of contacts with duplicate detection."""
    
    def __init__(self, contact_import: ContactImport):
        self.contact_import = contact_import
        self.firm = contact_import.firm
        self.duplicate_detector = ContactDuplicateDetector()
    
    def parse_csv(self, file_content: bytes) -> List[Dict[str, str]]:
        """Parse CSV file content into list of dictionaries."""
        try:
            # Try UTF-8 first
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to Latin-1
            content = file_content.decode('latin-1')
        
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
        return list(reader)
    
    def map_fields(self, row: Dict[str, str]) -> Dict[str, any]:
        """Map CSV columns to Contact model fields using field_mapping."""
        field_mapping = self.contact_import.field_mapping
        mapped_data = {}
        
        for csv_field, model_field in field_mapping.items():
            if csv_field in row:
                value = row[csv_field].strip() if row[csv_field] else ""
                if value:  # Only include non-empty values
                    mapped_data[model_field] = value
        
        return mapped_data
    
    def create_or_update_contact(
        self,
        client: Client,
        contact_data: Dict[str, any],
    ) -> Tuple[Contact, bool, str]:
        """
        Create or update a contact based on duplicate strategy.
        
        Returns:
            Tuple of (contact, created, status_message)
            - contact: The Contact instance (or None if skipped)
            - created: True if new contact was created
            - status_message: Description of what happened
        """
        email = contact_data.get('email', '')
        first_name = contact_data.get('first_name', '')
        last_name = contact_data.get('last_name', '')
        phone = contact_data.get('phone', '')
        
        # Find potential duplicate
        duplicate = self.duplicate_detector.find_best_match(
            client, email, first_name, last_name, phone
        )
        
        if duplicate:
            self.contact_import.duplicates_found += 1
            
            if self.contact_import.duplicate_strategy == ContactImport.DUPLICATE_SKIP:
                return (None, False, f"Skipped duplicate: {email or first_name}")
            
            elif self.contact_import.duplicate_strategy == ContactImport.DUPLICATE_UPDATE:
                # Update existing contact
                for field, value in contact_data.items():
                    setattr(duplicate, field, value)
                duplicate.save()
                return (duplicate, False, f"Updated existing contact: {duplicate.email}")
        
        # Create new contact (no duplicate or CREATE_NEW strategy)
        contact_data['client'] = client
        contact_data['created_by'] = self.contact_import.created_by
        
        try:
            contact = Contact(**contact_data)
            contact.full_clean()  # Validate
            contact.save()
            return (contact, True, f"Created new contact: {contact.email}")
        except ValidationError as e:
            raise ValidationError(f"Validation error: {str(e)}")
    
    def process_import(self, file_content: bytes, client: Client) -> Dict[str, any]:
        """
        Process the entire import operation.
        
        Returns:
            Dictionary with import results
        """
        try:
            self.contact_import.mark_as_processing()
            
            # Parse CSV
            rows = self.parse_csv(file_content)
            self.contact_import.total_rows = len(rows)
            self.contact_import.save(update_fields=['total_rows'])
            
            results = {
                'successful': [],
                'failed': [],
                'skipped': [],
            }
            
            # Process each row
            with transaction.atomic():
                for i, row in enumerate(rows, start=1):
                    try:
                        # Map fields
                        contact_data = self.map_fields(row)
                        
                        if not contact_data:
                            self.contact_import.skipped_rows += 1
                            results['skipped'].append({
                                'row': i,
                                'reason': 'No data after field mapping',
                            })
                            continue
                        
                        # Create or update contact
                        contact, created, message = self.create_or_update_contact(
                            client, contact_data
                        )
                        
                        if contact is None:
                            # Skipped (duplicate)
                            self.contact_import.skipped_rows += 1
                            results['skipped'].append({
                                'row': i,
                                'reason': message,
                            })
                        else:
                            # Success
                            self.contact_import.successful_imports += 1
                            results['successful'].append({
                                'row': i,
                                'contact_id': contact.id,
                                'message': message,
                            })
                    
                    except Exception as e:
                        # Error
                        self.contact_import.failed_imports += 1
                        results['failed'].append({
                            'row': i,
                            'error': str(e),
                            'data': row,
                        })
            
            # Update import status
            if self.contact_import.failed_imports > 0:
                self.contact_import.mark_as_partially_completed()
            else:
                self.contact_import.mark_as_completed()
            
            self.contact_import.error_details = {
                'failed_rows': results['failed'],
                'skipped_rows': results['skipped'],
            }
            self.contact_import.save(update_fields=['error_details'])
            
            return results
        
        except Exception as e:
            self.contact_import.mark_as_failed(str(e))
            raise


class ContactBulkUpdater:
    """Handle bulk updates of contacts."""
    
    def __init__(self, bulk_update: ContactBulkUpdate):
        self.bulk_update = bulk_update
        self.firm = bulk_update.firm
    
    def update_contacts(self, contact_ids: List[int], update_data: Dict[str, any]) -> Dict[str, any]:
        """
        Perform bulk update on specified contacts.
        
        Returns:
            Dictionary with update results
        """
        try:
            self.bulk_update.status = ContactBulkUpdate.STATUS_PROCESSING
            self.bulk_update.save(update_fields=['status'])
            
            # Get contacts to update
            contacts = Contact.objects.filter(
                id__in=contact_ids,
                client__firm=self.firm,  # Ensure firm isolation
            )
            
            self.bulk_update.total_contacts = contacts.count()
            self.bulk_update.save(update_fields=['total_contacts'])
            
            results = {
                'successful': [],
                'failed': [],
            }
            
            # Update each contact
            with transaction.atomic():
                for contact in contacts:
                    try:
                        for field, value in update_data.items():
                            setattr(contact, field, value)
                        contact.full_clean()  # Validate
                        contact.save()
                        
                        self.bulk_update.successful_updates += 1
                        results['successful'].append({
                            'contact_id': contact.id,
                            'email': contact.email,
                        })
                    
                    except Exception as e:
                        self.bulk_update.failed_updates += 1
                        results['failed'].append({
                            'contact_id': contact.id,
                            'error': str(e),
                        })
            
            # Update status
            self.bulk_update.status = ContactBulkUpdate.STATUS_COMPLETED
            self.bulk_update.completed_at = timezone.now()
            self.bulk_update.error_details = {
                'failed_updates': results['failed'],
            }
            self.bulk_update.save()
            
            return results
        
        except Exception as e:
            self.bulk_update.status = ContactBulkUpdate.STATUS_FAILED
            self.bulk_update.error_message = str(e)
            self.bulk_update.completed_at = timezone.now()
            self.bulk_update.save()
            raise
