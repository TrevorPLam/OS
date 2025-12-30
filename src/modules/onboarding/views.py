"""
Onboarding Module Views.

Provides API endpoints for client onboarding management.
Implements Karbon-like standardized onboarding workflows.
"""

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin

from .models import (
    OnboardingTemplate,
    OnboardingProcess,
    OnboardingTask,
    OnboardingDocument,
)
from .serializers import (
    OnboardingTemplateSerializer,
    OnboardingProcessSerializer,
    OnboardingProcessDetailSerializer,
    OnboardingTaskSerializer,
    OnboardingDocumentSerializer,
)


class OnboardingTemplateViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Onboarding Template management.

    Templates define standardized onboarding processes.
    Only managers can create/edit templates.
    """

    model = OnboardingTemplate
    serializer_class = OnboardingTemplateSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "service_type"]
    search_fields = ["name", "description", "service_type"]
    ordering_fields = ["name", "times_used", "created_at"]
    ordering = ["name"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate template for use."""
        template = self.get_object()
        template.status = "active"
        template.save(update_fields=["status"])

        return Response(
            {"message": "Template activated", "template": OnboardingTemplateSerializer(template).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive template (no longer available for new processes)."""
        template = self.get_object()
        template.status = "archived"
        template.save(update_fields=["status"])

        return Response(
            {"message": "Template archived", "template": OnboardingTemplateSerializer(template).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def create_process(self, request, pk=None):
        """
        Create a new onboarding process from this template.

        Instantiates all tasks and document requirements from template.
        """
        template = self.get_object()
        client_id = request.data.get("client_id")
        assigned_to_id = request.data.get("assigned_to_id")

        if not client_id:
            return Response(
                {"error": "client_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from modules.clients.models import Client
        try:
            client = Client.objects.get(id=client_id, firm=request.firm)
        except Client.DoesNotExist:
            return Response(
                {"error": "Client not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create process
        process = OnboardingProcess.objects.create(
            firm=request.firm,
            template=template,
            client=client,
            name=f"{template.name} - {client.company_name}",
            assigned_to_id=assigned_to_id,
            created_by=request.user,
        )

        # Create tasks from template steps
        if template.steps:
            for step_num, step in enumerate(template.steps, start=1):
                tasks = step.get("tasks", [])
                for task in tasks:
                    OnboardingTask.objects.create(
                        process=process,
                        name=task.get("task_name", "Unnamed Task"),
                        description=task.get("description", ""),
                        task_type=task.get("task_type", "other"),
                        step_number=step_num,
                        is_required=task.get("required", True),
                        assigned_to_client=task.get("assigned_to_client", False),
                    )

        # Update process task counts
        process.update_progress()

        # Mark template as used
        template.mark_used()

        return Response(
            {
                "message": "Onboarding process created",
                "process": OnboardingProcessDetailSerializer(process).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OnboardingProcessViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Onboarding Process management.

    Processes represent active client onboarding workflows.
    Staff can view all processes; portal users can view their own.
    """

    model = OnboardingProcess
    permission_classes = [IsAuthenticated]  # Both staff and portal users
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "template", "client", "assigned_to"]
    search_fields = ["name", "client__company_name"]
    ordering_fields = ["created_at", "target_completion_date", "progress_percentage"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Use detail serializer for retrieve, list serializer otherwise."""
        if self.action == "retrieve":
            return OnboardingProcessDetailSerializer
        return OnboardingProcessSerializer

    def get_queryset(self):
        """Filter by firm context and portal permissions."""
        queryset = super().get_queryset()

        # Portal users can only see their own onboarding processes
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            queryset = queryset.filter(client__in=self.request.portal_clients)

        return queryset.select_related(
            "template",
            "client",
            "assigned_to",
            "created_by",
        ).prefetch_related(
            "tasks",
            "document_requirements",
        )

    def perform_create(self, serializer):
        """Create onboarding process."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def start(self, request, pk=None):
        """
        Start onboarding process.

        Marks process as in_progress and sets started_at timestamp.
        Staff only action.
        """
        process = self.get_object()

        if process.status != "not_started":
            return Response(
                {"error": "Process has already been started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        process.start()

        return Response(
            {
                "message": "Onboarding process started",
                "process": OnboardingProcessDetailSerializer(process).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def complete(self, request, pk=None):
        """
        Complete onboarding process.

        Marks process as completed and sets completion timestamp.
        Staff only action.
        """
        process = self.get_object()

        if process.status == "completed":
            return Response(
                {"error": "Process is already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        process.complete()

        return Response(
            {
                "message": "Onboarding process completed",
                "process": OnboardingProcessDetailSerializer(process).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        """
        Recalculate progress based on completed tasks.

        Available to both staff and portal users.
        """
        process = self.get_object()
        process.update_progress()

        return Response(
            {
                "message": "Progress updated",
                "process": OnboardingProcessDetailSerializer(process).data,
            },
            status=status.HTTP_200_OK,
        )


class OnboardingTaskViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Onboarding Tasks.

    Tasks represent individual steps in an onboarding process.
    Portal users can complete tasks assigned to them.
    """

    queryset = OnboardingTask.objects.all()
    serializer_class = OnboardingTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["process", "status", "task_type", "assigned_to_client"]
    ordering_fields = ["step_number", "due_date", "created_at"]
    ordering = ["step_number"]

    def get_queryset(self):
        """Filter by process access permissions."""
        queryset = self.queryset

        # Portal users can only see tasks for their onboarding processes
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            queryset = queryset.filter(process__client__in=self.request.portal_clients)

        return queryset.select_related("process", "completed_by", "depends_on")

    def perform_create(self, serializer):
        """Create task and update parent process."""
        task = serializer.save()
        task.process.update_progress()

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Mark task as completed.

        Available to both staff and portal users.
        Portal users can only complete tasks assigned to them.
        """
        task = self.get_object()

        # Portal users can only complete tasks assigned to them
        if hasattr(request, "is_portal_request") and request.is_portal_request:
            if not task.assigned_to_client:
                return Response(
                    {"error": "This task is not assigned to you"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if task.status == "completed":
            return Response(
                {"error": "Task is already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.complete(completed_by=request.user)

        return Response(
            {"message": "Task completed", "task": OnboardingTaskSerializer(task).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def send_reminder(self, request, pk=None):
        """
        Send reminder for incomplete task (if assigned to client).

        Staff only action.
        """
        task = self.get_object()

        if task.send_reminder():
            return Response(
                {"message": "Reminder sent", "task": OnboardingTaskSerializer(task).data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Cannot send reminder for this task"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OnboardingDocumentViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Onboarding Document collection.

    Tracks document requirements and collection status.
    Portal users can upload documents.
    """

    queryset = OnboardingDocument.objects.all()
    serializer_class = OnboardingDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["process", "status", "is_required", "task"]
    ordering_fields = ["document_name", "created_at"]
    ordering = ["document_name"]

    def get_queryset(self):
        """Filter by process access permissions."""
        queryset = self.queryset

        # Portal users can only see documents for their onboarding processes
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            queryset = queryset.filter(process__client__in=self.request.portal_clients)

        return queryset.select_related("process", "task", "document", "reviewed_by")

    @action(detail=True, methods=["post"])
    def upload(self, request, pk=None):
        """
        Upload document (mark as received).

        Available to both staff and portal users.
        """
        doc_req = self.get_object()
        document_id = request.data.get("document_id")

        if not document_id:
            return Response(
                {"error": "document_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from modules.documents.models import Document
        try:
            document = Document.objects.get(id=document_id, firm=request.firm)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        doc_req.mark_received(document)

        return Response(
            {
                "message": "Document uploaded",
                "document_requirement": OnboardingDocumentSerializer(doc_req).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def approve(self, request, pk=None):
        """
        Approve document.

        Staff only action.
        """
        doc_req = self.get_object()
        notes = request.data.get("notes", "")

        if doc_req.status != "received":
            return Response(
                {"error": "Document must be received before it can be approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_req.approve(reviewed_by=request.user, notes=notes)

        return Response(
            {
                "message": "Document approved",
                "document_requirement": OnboardingDocumentSerializer(doc_req).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def reject(self, request, pk=None):
        """
        Reject document (needs update from client).

        Staff only action. Requires review notes explaining rejection.
        """
        doc_req = self.get_object()
        notes = request.data.get("notes")

        if not notes:
            return Response(
                {"error": "notes are required when rejecting a document"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if doc_req.status != "received":
            return Response(
                {"error": "Document must be received before it can be rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_req.reject(reviewed_by=request.user, notes=notes)

        return Response(
            {
                "message": "Document rejected",
                "document_requirement": OnboardingDocumentSerializer(doc_req).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def send_reminder(self, request, pk=None):
        """
        Send reminder for missing document.

        Staff only action.
        """
        doc_req = self.get_object()

        if doc_req.send_reminder():
            return Response(
                {
                    "message": "Reminder sent",
                    "document_requirement": OnboardingDocumentSerializer(doc_req).data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Cannot send reminder for this document"},
                status=status.HTTP_400_BAD_REQUEST,
            )
