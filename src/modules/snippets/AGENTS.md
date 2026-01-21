# AGENTS.md — Snippets Module

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/snippets/`

## Purpose

Quick text insertion system (HubSpot-style snippets) for common phrases.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Snippet, SnippetCategory |
| `views.py` | Snippet endpoints |
| `serializers.py` | Snippet serializers |

## Domain Model

```
SnippetCategory (organization)
    └── Snippet (text template)
```

## Key Models

### Snippet

Quick insert text:

```python
class Snippet(models.Model):
    firm: FK[Firm]
    category: FK[SnippetCategory]
    
    name: str
    shortcut: str                     # Keyboard shortcut trigger
    content: str                      # Text content with variables
    
    # Variables
    available_variables: JSONField    # ["first_name", "company"]
    
    usage_count: int
```

## Usage

Snippets can include variables:

```
Hello {{first_name}},

Thank you for your interest in {{company}}.

Best regards,
{{sender_name}}
```

## Dependencies

- **Depends on**: `firm/`
- **Used by**: Email composition, message writing

## URLs

All routes under `/api/v1/snippets/`:

```
GET/POST   /categories/
GET/POST   /snippets/
GET/PUT    /snippets/{id}/
POST       /snippets/{id}/use/        # Track usage
```
