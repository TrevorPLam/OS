"""
URL routes for Projects API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet, TimeEntryViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'time-entries', TimeEntryViewSet, basename='timeentry')

urlpatterns = [
    path('', include(router.urls)),
]
