# Document AI Research: AWS Textract vs Google Document AI

**Status:** Research Complete  
**Date:** January 2, 2026  
**Related Features:** Document Intelligence Features (DOC-INT-1 through DOC-INT-4)  
**Priority:** MEDIUM

## Executive Summary

This document evaluates AI-powered document processing solutions for intelligent document management, including OCR (Optical Character Recognition), data extraction, document classification, and document comparison.

## Use Cases Requiring Document AI

### High Priority
1. **Document Classification** (DOC-INT-2: Document DNA Fingerprinting)
   - Automatically classify documents by type (W2, 1099, invoice, contract, etc.)
   - Detect altered versions of documents
   - Duplicate detection with fuzzy matching

2. **Auto-Extraction Engine** (E6)
   - Extract structured data from documents (OCR + LLM)
   - Extract key-value pairs (name, date, amount, etc.)
   - Table extraction from invoices and forms

3. **Version Comparison** (DOC-INT-4)
   - Visual diff for Word documents
   - PDF diff (highlight changed text/images)
   - Excel diff (cell-by-cell comparison)

4. **Client Document Request Intelligence** (DOC-INT-3)
   - Auto-identify document types from uploads
   - Validate completeness (is this a complete W2?)
   - Quality checks (is document legible?)

## Solution Comparison

### Option 1: AWS Textract (Recommended)

**Website:** https://aws.amazon.com/textract/  
**Pricing:** Pay-per-use ($1.50 per 1000 pages for basic OCR, $50-65 per 1000 pages for form/table extraction)  
**Limits:** 15 pages per second, 3000 pages per day (soft limit, can request increase)

#### Pros
- ✅ **Best-in-class accuracy** - Industry-leading OCR accuracy (98%+)
- ✅ **Form extraction** - Automatically detects and extracts key-value pairs
- ✅ **Table extraction** - Extracts tables with rows/columns preserved
- ✅ **Handwriting support** - Can read handwritten text
- ✅ **Signature detection** - Identifies signature blocks
- ✅ **Query-based extraction** - Ask questions like "What is the invoice total?"
- ✅ **No training required** - Works out of the box
- ✅ **AWS integration** - Seamless with S3, Lambda, etc.
- ✅ **Compliance** - HIPAA, SOC, PCI DSS certified
- ✅ **Identity documents** - Specialized support for IDs, passports, driver's licenses

#### Cons
- ⚠️ **Cost** - Can get expensive at high volumes ($50-65/1000 pages for advanced features)
- ⚠️ **Vendor lock-in** - AWS-specific, not portable
- ⚠️ **No document classification** - Need separate ML model or service for classification
- ⚠️ **Limited language support** - English, Spanish, German, French, Italian, Portuguese primarily

#### Pricing Breakdown

| Feature | Price per 1000 pages | Use Case |
|---------|----------------------|----------|
| Basic OCR (Detect Document Text) | $1.50 | Simple text extraction |
| Form Extraction | $50.00 | Extract key-value pairs |
| Table Extraction | $15.00 | Extract tables |
| Query-based Extraction | $65.00 | Ask questions about document |
| Identity Document Analysis | $30.00 | Extract data from IDs, passports |

**Cost Estimate:** For 10,000 documents/month with form extraction: $500/month

#### Example Code

```python
import boto3
from botocore.exceptions import BotoCoreError, ClientError

class AWSTextractService:
    def __init__(self):
        self.textract_client = boto3.client('textract', region_name='us-east-1')
        self.s3_client = boto3.client('s3', region_name='us-east-1')
    
    def extract_text(self, bucket_name, document_key):
        """
        Extract text from document using basic OCR
        
        Args:
            bucket_name: S3 bucket name
            document_key: S3 object key
        
        Returns:
            Extracted text
        """
        try:
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document_key
                    }
                }
            )
            
            # Extract text blocks
            text = ""
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text += block['Text'] + '\n'
            
            return text
        
        except (BotoCoreError, ClientError) as error:
            print(f"Error extracting text: {error}")
            return None
    
    def extract_forms(self, bucket_name, document_key):
        """
        Extract key-value pairs from forms
        
        Returns:
            Dict of key-value pairs
        """
        try:
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document_key
                    }
                },
                FeatureTypes=['FORMS']
            )
            
            # Parse key-value pairs
            key_values = {}
            for block in response['Blocks']:
                if block['BlockType'] == 'KEY_VALUE_SET':
                    if 'KEY' in block['EntityTypes']:
                        key = self._get_text(block, response['Blocks'])
                        value_block = self._find_value_block(block, response['Blocks'])
                        if value_block:
                            value = self._get_text(value_block, response['Blocks'])
                            key_values[key] = value
            
            return key_values
        
        except (BotoCoreError, ClientError) as error:
            print(f"Error extracting forms: {error}")
            return None
    
    def extract_tables(self, bucket_name, document_key):
        """
        Extract tables from document
        
        Returns:
            List of tables (each table is list of rows)
        """
        try:
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document_key
                    }
                },
                FeatureTypes=['TABLES']
            )
            
            # Parse tables
            tables = []
            for block in response['Blocks']:
                if block['BlockType'] == 'TABLE':
                    table = self._parse_table(block, response['Blocks'])
                    tables.append(table)
            
            return tables
        
        except (BotoCoreError, ClientError) as error:
            print(f"Error extracting tables: {error}")
            return None
    
    def query_document(self, bucket_name, document_key, queries):
        """
        Ask questions about document
        
        Args:
            queries: List of questions (e.g., "What is the invoice total?")
        
        Returns:
            Dict of question -> answer
        """
        try:
            query_config = {
                'Queries': [{'Text': q, 'Alias': f'Q{i}'} for i, q in enumerate(queries)]
            }
            
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document_key
                    }
                },
                FeatureTypes=['QUERIES'],
                QueriesConfig=query_config
            )
            
            # Parse answers
            answers = {}
            for block in response['Blocks']:
                if block['BlockType'] == 'QUERY_RESULT':
                    query_alias = block['Query']['Alias']
                    query_text = block['Query']['Text']
                    answer_text = block['Text']
                    confidence = block['Confidence']
                    answers[query_text] = {
                        'answer': answer_text,
                        'confidence': confidence
                    }
            
            return answers
        
        except (BotoCoreError, ClientError) as error:
            print(f"Error querying document: {error}")
            return None
    
    def analyze_identity_document(self, bucket_name, document_key):
        """
        Extract data from ID, passport, driver's license
        
        Returns:
            Dict with extracted fields
        """
        try:
            response = self.textract_client.analyze_id(
                DocumentPages=[
                    {
                        'S3Object': {
                            'Bucket': bucket_name,
                            'Name': document_key
                        }
                    }
                ]
            )
            
            # Parse identity fields
            identity_data = {}
            for document in response['IdentityDocuments']:
                for field in document['IdentityDocumentFields']:
                    field_type = field['Type']['Text']
                    field_value = field.get('ValueDetection', {}).get('Text', '')
                    confidence = field.get('ValueDetection', {}).get('Confidence', 0)
                    identity_data[field_type] = {
                        'value': field_value,
                        'confidence': confidence
                    }
            
            return identity_data
        
        except (BotoCoreError, ClientError) as error:
            print(f"Error analyzing ID: {error}")
            return None
```

#### Integration with Django

```python
# models.py
from django.db import models

class DocumentExtractionJob(models.Model):
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE)
    job_id = models.CharField(max_length=255)  # Textract job ID
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    ])
    extracted_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict)  # Key-value pairs, tables, etc.
    confidence_score = models.FloatField(null=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

# tasks.py (Celery)
from celery import shared_task

@shared_task
def process_document_extraction(document_id):
    """Extract data from document using AWS Textract"""
    from modules.documents.models import Document
    
    document = Document.objects.get(id=document_id)
    
    # Upload to S3 if not already there
    s3_bucket = 'consultantpro-documents'
    s3_key = f'documents/{document.firm_id}/{document.id}/{document.filename}'
    
    # Extract text and forms
    textract = AWSTextractService()
    text = textract.extract_text(s3_bucket, s3_key)
    forms = textract.extract_forms(s3_bucket, s3_key)
    tables = textract.extract_tables(s3_bucket, s3_key)
    
    # Save results
    DocumentExtractionJob.objects.create(
        document=document,
        status='succeeded',
        extracted_text=text,
        extracted_data={
            'forms': forms,
            'tables': tables
        }
    )
    
    # Trigger document classification (separate ML model)
    classify_document.delay(document_id)
```

### Option 2: Google Document AI

**Website:** https://cloud.google.com/document-ai  
**Pricing:** $0.002 per page (basic OCR), $0.01-0.10 per page for specialized processors  
**Limits:** 300 pages per minute, 50,000 pages per day

#### Pros
- ✅ **Pre-trained processors** - W2, 1099, invoice, receipt, contract processors ready to use
- ✅ **Custom processors** - Train custom models for your document types
- ✅ **Lower cost for specialized documents** - $0.01 per invoice vs $50/1000 for Textract forms
- ✅ **Document classification** - Built-in document type detection
- ✅ **Entity extraction** - Pre-trained entity extractors (dates, amounts, names)
- ✅ **Multi-language** - 200+ languages supported
- ✅ **Google Cloud integration** - Works with GCS, Cloud Functions

#### Cons
- ⚠️ **Requires Google Cloud** - Vendor lock-in to GCP
- ⚠️ **Learning curve** - More complex setup than Textract
- ⚠️ **Less mature** - Newer product, less battle-tested
- ⚠️ **Limited identity document support** - Not as specialized as Textract for IDs

#### Pricing Breakdown

| Processor Type | Price per 1000 pages | Use Case |
|----------------|----------------------|----------|
| OCR | $2.00 | Basic text extraction |
| Invoice Parser | $10.00 | Extract invoice data |
| Receipt Parser | $10.00 | Extract receipt data |
| W2 Parser | $10.00 | Extract W2 data |
| 1099 Parser | $10.00 | Extract 1099 data |
| Custom Processor | $30.00 | Custom document types |

**Cost Estimate:** For 10,000 documents/month with specialized parsers: $100/month

#### Example Code

```python
from google.cloud import documentai_v1 as documentai

class GoogleDocumentAIService:
    def __init__(self, project_id, location='us'):
        self.project_id = project_id
        self.location = location
        self.client = documentai.DocumentProcessorServiceClient()
    
    def process_document(self, processor_id, document_path, mime_type='application/pdf'):
        """
        Process document with specific processor
        
        Args:
            processor_id: Processor ID (e.g., 'invoice-parser')
            document_path: Local file path or GCS URI
            mime_type: Document MIME type
        
        Returns:
            Document object with extracted data
        """
        # Read document
        with open(document_path, 'rb') as doc:
            document_content = doc.read()
        
        # Configure request
        name = self.client.processor_path(
            self.project_id, self.location, processor_id
        )
        
        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
        )
        
        # Process document
        result = self.client.process_document(request=request)
        document = result.document
        
        return document
    
    def extract_invoice_data(self, document):
        """Extract invoice-specific fields"""
        invoice_data = {
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
            'vendor_name': None,
            'line_items': []
        }
        
        # Extract entities
        for entity in document.entities:
            entity_type = entity.type_
            entity_value = entity.mention_text
            confidence = entity.confidence
            
            if entity_type == 'invoice_id':
                invoice_data['invoice_number'] = entity_value
            elif entity_type == 'invoice_date':
                invoice_data['invoice_date'] = entity_value
            elif entity_type == 'total_amount':
                invoice_data['total_amount'] = entity_value
            elif entity_type == 'supplier_name':
                invoice_data['vendor_name'] = entity_value
            elif entity_type == 'line_item':
                # Line items are nested entities
                line_item = {}
                for property in entity.properties:
                    line_item[property.type_] = property.mention_text
                invoice_data['line_items'].append(line_item)
        
        return invoice_data
```

### Option 3: Azure Form Recognizer / Azure AI Document Intelligence

**Website:** https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence  
**Pricing:** $1.50 per 1000 pages (OCR), $10-50 per 1000 pages for prebuilt models

#### Pros
- ✅ **Microsoft ecosystem integration** - Works with Azure, Office 365
- ✅ **Prebuilt models** - Invoice, receipt, ID, business card models
- ✅ **Custom models** - Train on your document types
- ✅ **Good accuracy** - Comparable to AWS Textract

#### Cons
- ⚠️ **Azure lock-in** - Requires Azure infrastructure
- ⚠️ **Not as feature-rich as Textract** - Limited query capabilities
- ⚠️ **Less popular** - Smaller community and fewer examples

**Verdict:** Only if already on Azure infrastructure

### Option 4: Open Source (Tesseract + PyPDF2 + Custom ML)

**Components:**
- Tesseract OCR (Google's open source OCR engine)
- PyPDF2 / pdfplumber for PDF text extraction
- Custom ML model for classification (scikit-learn)

#### Pros
- ✅ **Free and open source** - No per-page costs
- ✅ **Full control** - Can customize and optimize
- ✅ **No vendor lock-in** - Runs anywhere

#### Cons
- ❌ **Lower accuracy** - 85-90% vs 98%+ for commercial solutions
- ❌ **No form/table extraction** - Manual parsing required
- ❌ **Significant development time** - 100-200 hours to build comparable features
- ❌ **Maintenance burden** - Need to update and improve models
- ❌ **No handwriting support** - Tesseract struggles with handwriting
- ❌ **Slow processing** - Not optimized for batch processing

**Verdict:** Not recommended unless extreme cost sensitivity

## Comparison Matrix

| Feature | AWS Textract | Google Document AI | Azure Form Recognizer | Open Source |
|---------|--------------|--------------------|-----------------------|-------------|
| OCR Accuracy | ⭐⭐⭐⭐⭐ (98%+) | ⭐⭐⭐⭐⭐ (98%+) | ⭐⭐⭐⭐ (95%+) | ⭐⭐⭐ (85-90%) |
| Form Extraction | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Table Extraction | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Document Classification | ⭐⭐ (need custom) | ⭐⭐⭐⭐⭐ (built-in) | ⭐⭐⭐⭐ | ⭐⭐⭐ (custom) |
| Handwriting Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Identity Documents | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Cost (10k pages/mo) | $500-650 | $100-300 | $150-500 | $0 (dev time) |
| Setup Complexity | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cloud Integration | AWS only | GCP only | Azure only | Any |
| Custom Training | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Query Capability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ No |

## Recommendation

### **Hybrid Approach: AWS Textract (Primary) + Google Document AI (Specialized)** ✅

#### Justification

**Use AWS Textract for:**
1. ✅ **General OCR** - Text extraction from any document
2. ✅ **Identity documents** - Driver's licenses, passports, IDs
3. ✅ **Query-based extraction** - "What is the invoice total?"
4. ✅ **Handwriting** - Reading handwritten forms

**Use Google Document AI for:**
1. ✅ **Document classification** - Automatically identify document type
2. ✅ **Specialized tax forms** - W2, 1099 extraction (cheaper at $10/1000 vs $50/1000)
3. ✅ **Invoice processing** - Structured invoice data extraction
4. ✅ **Receipt processing** - Expense receipt extraction

#### Cost Optimization Strategy

```python
class DocumentProcessingRouter:
    """Route documents to optimal AI service based on document type"""
    
    def process_document(self, document):
        # First, classify document (Google Document AI - cheap)
        doc_type = self.classify_document(document)  # $2/1000 pages
        
        if doc_type in ['w2', 'w9', '1099']:
            # Use Google Document AI specialized processors ($10/1000)
            return self.process_with_google_ai(document, doc_type)
        
        elif doc_type in ['drivers_license', 'passport', 'id_card']:
            # Use AWS Textract identity document analysis ($30/1000)
            return self.process_with_textract_identity(document)
        
        elif doc_type in ['handwritten_form']:
            # Use AWS Textract (best handwriting support)
            return self.process_with_textract(document)
        
        else:
            # Default to AWS Textract for general documents
            return self.process_with_textract(document)
```

**Estimated Cost for 10,000 documents/month:**
- Classification (all): 10,000 × $0.002 = $20
- Tax forms (20%): 2,000 × $0.01 = $20
- Identity docs (10%): 1,000 × $0.03 = $30
- General docs (70%): 7,000 × $0.05 = $350
- **Total: ~$420/month** (vs $500-650 for Textract only)

## Implementation Plan

### Phase 1: AWS Textract Integration (16-24 hours)

#### Week 1: Core Integration
- Set up AWS Textract client in Django
- Create DocumentExtractionJob model
- Implement basic OCR (Detect Document Text)
- Implement form extraction (AnalyzeDocument with FORMS)
- Implement table extraction (AnalyzeDocument with TABLES)
- Build Celery task for async processing
- Create admin UI for viewing extracted data

### Phase 2: Google Document AI Integration (12-16 hours)

#### Week 2: Specialized Processing
- Set up Google Document AI client
- Configure specialized processors (W2, 1099, invoice, receipt)
- Implement document classification
- Build routing logic (choose AWS vs Google based on document type)
- Add cost tracking per document

### Phase 3: Document Intelligence Features (20-28 hours)

#### Week 3-4: Advanced Features
- Implement document DNA fingerprinting (perceptual hashing)
- Build document comparison engine (diff detection)
- Create confidence scoring system
- Add quality checks (is document legible?)
- Build admin dashboard for document intelligence

### Total Estimated Effort: 48-68 hours

## Code Structure

```
src/modules/document_ai/
├── __init__.py
├── models.py                          # DocumentExtractionJob, DocumentClassification
├── services/
│   ├── __init__.py
│   ├── textract.py                   # AWS Textract integration
│   ├── google_doc_ai.py              # Google Document AI integration
│   ├── router.py                     # Route to optimal service
│   └── fingerprint.py                # Document fingerprinting
├── tasks.py                           # Celery tasks for async processing
├── api/
│   ├── __init__.py
│   ├── views.py                      # API endpoints
│   └── serializers.py                # DRF serializers
└── utils/
    ├── __init__.py
    ├── pdf_utils.py                  # PDF manipulation
    └── image_utils.py                # Image preprocessing
```

## Security & Compliance

- [ ] **Data residency** - Process documents in customer's region
- [ ] **Encryption in transit** - TLS for all API calls
- [ ] **Encryption at rest** - Encrypt extracted data in database
- [ ] **Access logging** - Audit who accessed extracted data
- [ ] **PII detection** - Flag documents containing PII
- [ ] **Retention policy** - Auto-delete extracted data after 90 days (configurable)
- [ ] **HIPAA compliance** - Use HIPAA-eligible AWS/GCP services
- [ ] **Data minimization** - Only extract fields actually needed

## Performance Benchmarks

### AWS Textract
- **Basic OCR:** 1-2 seconds per page
- **Form extraction:** 2-4 seconds per page
- **Table extraction:** 3-5 seconds per page
- **Batch processing:** Up to 15 pages per second (parallel)

### Google Document AI
- **OCR:** 0.5-1 second per page
- **Specialized processor:** 1-2 seconds per page
- **Batch processing:** Up to 300 pages per minute

## References

- AWS Textract Documentation: https://docs.aws.amazon.com/textract/
- Google Document AI Documentation: https://cloud.google.com/document-ai/docs
- Azure Form Recognizer: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract

## Next Steps

1. ✅ **Research Complete** - AWS Textract + Google Document AI hybrid approach selected
2. [ ] Set up AWS Textract client (4 hours)
3. [ ] Implement basic OCR integration (6-8 hours)
4. [ ] Build document classification with Google Document AI (8-12 hours)
5. [ ] Create routing logic (4-6 hours)
6. [ ] Update P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md to mark research task as complete

---

**Research Completed By:** Development Team  
**Approved By:** [Pending Review]  
**Implementation Target:** Q1 2026
