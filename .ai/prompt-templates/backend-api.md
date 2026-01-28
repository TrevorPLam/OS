# Backend API Template

When creating a new API endpoint in the Django backend:

1. **Create API module**: `backend/api/[feature-name]/`
2. **Structure**:
   - `views.py` - API view classes
   - `serializers.py` - DRF serializers
   - `urls.py` - URL routing
   - `__init__.py` - Package initialization

3. **Domain module**: Create corresponding module in `backend/modules/[feature-name]/`
   - Models, services, and business logic

4. **Follow Django REST Framework patterns**:
   - Use ViewSets for CRUD operations
   - Use Serializers for data validation
   - Register URLs in `backend/config/urls.py`
