# AGENTS.md — Knowledge Module (SOPs & Training)

Last Updated: 2026-01-06
Applies To: `src/modules/knowledge/`

## Purpose

Knowledge base system for SOPs, training materials, and playbooks.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | KnowledgeCategory, KnowledgeArticle, ArticleVersion |
| `views.py` | Knowledge endpoints |
| `serializers.py` | Knowledge serializers |

## Domain Model

```
KnowledgeCategory (hierarchical folders)
    └── KnowledgeArticle (content)
            └── ArticleVersion (version history)
```

## Key Models

### KnowledgeCategory

Hierarchical organization:

```python
class KnowledgeCategory(models.Model):
    firm: FK[Firm]
    parent: FK[self]                  # Nested categories
    
    name: str
    description: str
    order: int
    
    visibility: str                   # internal, client_portal
```

### KnowledgeArticle

Knowledge content:

```python
class KnowledgeArticle(models.Model):
    firm: FK[Firm]
    category: FK[KnowledgeCategory]
    
    title: str
    slug: str
    
    # Content
    content_html: str
    content_markdown: str
    
    # Metadata
    article_type: str                 # sop, training, playbook, faq
    status: str                       # draft, published, archived
    
    # Visibility
    visibility: str                   # internal, client_portal
    
    # Tracking
    view_count: int
    helpful_count: int
    
    published_at: DateTime
    author: FK[User]
```

## Dependencies

- **Depends on**: `firm/`
- **Used by**: Client portal (visible articles)

## URLs

All routes under `/api/v1/knowledge/`:

```
GET/POST   /categories/
GET/PUT    /categories/{id}/

GET/POST   /articles/
GET/PUT    /articles/{id}/
POST       /articles/{id}/publish/
GET        /articles/{id}/versions/
POST       /articles/{id}/helpful/
```
