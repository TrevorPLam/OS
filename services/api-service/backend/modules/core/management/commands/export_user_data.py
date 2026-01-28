"""
Management command to export all user data (GDPR Right to Access - ASSESS-L19.3).

Exports all data associated with a user/client in JSON and CSV formats.
"""

import json
import csv
from io import StringIO
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from modules.clients.models import Client
from modules.crm.models import Lead, Prospect
from modules.projects.models import Project, Task, TimeEntry
from modules.finance.models import Invoice, Payment
from modules.documents.models import Document, DocumentVersion


class Command(BaseCommand):
    help = "Export all data for a user/client (GDPR Right to Access - ASSESS-L19.3)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=int,
            help='Client ID to export data for'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to export data for (alternative to client-id)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'both'],
            default='both',
            help='Export format (default: both)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./exports',
            help='Output directory for export files (default: ./exports)'
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        email = options.get('email')
        format_type = options.get('format')
        output_dir = Path(options.get('output_dir'))
        
        # Resolve client
        if not client_id and not email:
            raise CommandError("Must provide either --client-id or --email")
        
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                raise CommandError(f"Client with ID {client_id} not found")
        else:  # email provided
            try:
                client = Client.objects.get(primary_contact_email=email)
            except Client.DoesNotExist:
                raise CommandError(f"Client with email {email} not found")
            except Client.MultipleObjectsReturned:
                raise CommandError(f"Multiple clients found with email {email}. Please use --client-id instead.")
        
        self.stdout.write(f"Exporting data for client: {client.company_name} (ID: {client.id})")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect all data
        export_data = self.collect_user_data(client)
        
        # Export in requested format(s)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"export_{client.id}_{timestamp}"
        
        if format_type in ['json', 'both']:
            json_path = output_dir / f"{base_filename}.json"
            self.export_json(export_data, json_path)
            self.stdout.write(self.style.SUCCESS(f"JSON export saved to: {json_path}"))
        
        if format_type in ['csv', 'both']:
            csv_path = output_dir / f"{base_filename}.csv"
            self.export_csv(export_data, csv_path)
            self.stdout.write(self.style.SUCCESS(f"CSV export saved to: {csv_path}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nExport completed for {client.company_name}"))
        self.stdout.write(f"Total records exported: {self.count_records(export_data)}")

    def collect_user_data(self, client):
        """Collect all data associated with a client."""
        data = {
            'client': self.serialize_client(client),
            'projects': [],
            'invoices': [],
            'payments': [],
            'documents': [],
            'time_entries': [],
            'tasks': [],
            'leads': [],
            'prospects': [],
        }
        
        # Projects
        projects = Project.objects.filter(client=client)
        for project in projects:
            data['projects'].append(self.serialize_project(project))
            
            # Tasks
            tasks = Task.objects.filter(project=project)
            for task in tasks:
                data['tasks'].append(self.serialize_task(task))
            
            # Time entries
            time_entries = TimeEntry.objects.filter(project=project)
            for entry in time_entries:
                data['time_entries'].append(self.serialize_time_entry(entry))
        
        # Invoices
        invoices = Invoice.objects.filter(client=client)
        for invoice in invoices:
            data['invoices'].append(self.serialize_invoice(invoice))
        
        # Payments
        payments = Payment.objects.filter(client=client)
        for payment in payments:
            data['payments'].append(self.serialize_payment(payment))
        
        # Documents
        documents = Document.objects.filter(client=client)
        for doc in documents:
            data['documents'].append(self.serialize_document(doc))
        
        # Leads/Prospects (by email)
        email = client.primary_contact_email
        leads = Lead.objects.filter(contact_email=email)
        for lead in leads:
            data['leads'].append(self.serialize_lead(lead))
        
        prospects = Prospect.objects.filter(primary_contact_email=email)
        for prospect in prospects:
            data['prospects'].append(self.serialize_prospect(prospect))
        
        return data

    def serialize_client(self, client):
        """Serialize client data."""
        return {
            'id': client.id,
            'company_name': client.company_name,
            'primary_contact_name': client.primary_contact_name,
            'primary_contact_email': client.primary_contact_email,
            'primary_contact_phone': client.primary_contact_phone,
            'status': client.status,
            'client_since': str(client.client_since) if client.client_since else None,
            'total_lifetime_value': str(client.total_lifetime_value),
            'retainer_balance': str(client.retainer_balance),
            'marketing_opt_in': client.marketing_opt_in,
            'consent_timestamp': str(client.consent_timestamp) if client.consent_timestamp else None,
            'consent_source': client.consent_source,
            'tos_accepted': client.tos_accepted,
            'tos_accepted_at': str(client.tos_accepted_at) if client.tos_accepted_at else None,
            'created_at': str(client.created_at),
            'updated_at': str(client.updated_at),
        }

    def serialize_project(self, project):
        """Serialize project data."""
        return {
            'id': project.id,
            'name': project.name,
            'project_code': project.project_code,
            'status': project.status,
            'billing_type': project.billing_type,
            'budget': str(project.budget) if project.budget else None,
            'start_date': str(project.start_date) if project.start_date else None,
            'end_date': str(project.end_date) if project.end_date else None,
            'created_at': str(project.created_at),
        }

    def serialize_invoice(self, invoice):
        """Serialize invoice data."""
        return {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'status': invoice.status,
            'total_amount': str(invoice.total_amount),
            'amount_paid': str(invoice.amount_paid),
            'issue_date': str(invoice.issue_date),
            'due_date': str(invoice.due_date),
            'paid_date': str(invoice.paid_date) if invoice.paid_date else None,
            'created_at': str(invoice.created_at),
        }

    def serialize_payment(self, payment):
        """Serialize payment data."""
        return {
            'id': payment.id,
            'payment_number': payment.payment_number,
            'amount': str(payment.amount),
            'payment_method': payment.payment_method,
            'payment_date': str(payment.payment_date),
            'created_at': str(payment.created_at),
        }

    def serialize_document(self, doc):
        """Serialize document data."""
        return {
            'id': doc.id,
            'title': doc.title,
            'status': doc.status,
            'created_at': str(doc.created_at),
            'updated_at': str(doc.updated_at),
        }

    def serialize_task(self, task):
        """Serialize task data."""
        return {
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'created_at': str(task.created_at),
            'completed_at': str(task.completed_at) if task.completed_at else None,
        }

    def serialize_time_entry(self, entry):
        """Serialize time entry data."""
        return {
            'id': entry.id,
            'date': str(entry.date),
            'hours': str(entry.hours),
            'is_billable': entry.is_billable,
            'created_at': str(entry.created_at),
        }

    def serialize_lead(self, lead):
        """Serialize lead data."""
        return {
            'id': lead.id,
            'company_name': lead.company_name,
            'contact_name': lead.contact_name,
            'contact_email': lead.contact_email,
            'status': lead.status,
            'source': lead.source,
            'created_at': str(lead.created_at),
        }

    def serialize_prospect(self, prospect):
        """Serialize prospect data."""
        return {
            'id': prospect.id,
            'company_name': prospect.company_name,
            'primary_contact_name': prospect.primary_contact_name,
            'primary_contact_email': prospect.primary_contact_email,
            'stage': prospect.stage,
            'estimated_value': str(prospect.estimated_value),
            'created_at': str(prospect.created_at),
        }

    def export_json(self, data, filepath):
        """Export data to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def export_csv(self, data, filepath):
        """Export data to CSV file (flattened structure)."""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write client data
            writer.writerow(['Section', 'Field', 'Value'])
            for key, value in data['client'].items():
                writer.writerow(['Client', key, value])
            
            # Write projects
            for project in data['projects']:
                for key, value in project.items():
                    writer.writerow(['Project', f"{project.get('name', 'Unknown')}.{key}", value])
            
            # Write invoices
            for invoice in data['invoices']:
                for key, value in invoice.items():
                    writer.writerow(['Invoice', f"{invoice.get('invoice_number', 'Unknown')}.{key}", value])
            
            # Write other sections similarly
            for payment in data['payments']:
                for key, value in payment.items():
                    writer.writerow(['Payment', f"{payment.get('payment_number', 'Unknown')}.{key}", value])

    def count_records(self, data):
        """Count total records in export."""
        return (
            len(data.get('projects', [])) +
            len(data.get('invoices', [])) +
            len(data.get('payments', [])) +
            len(data.get('documents', [])) +
            len(data.get('time_entries', [])) +
            len(data.get('tasks', [])) +
            len(data.get('leads', [])) +
            len(data.get('prospects', []))
        )