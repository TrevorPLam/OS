# Data Migration Template

When creating a database migration:

1. **Django migrations**: `python manage.py makemigrations [module-name]`
2. **Migration files**: Created in `backend/modules/[module-name]/migrations/`
3. **Data migrations**: Use `RunPython` for data transformations
4. **Schema migrations**: Use Django's migration operations

## Best Practices
- Always test migrations on a copy of production data
- Make migrations reversible when possible
- Document breaking changes in migration comments
