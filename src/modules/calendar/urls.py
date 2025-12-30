"""URL configuration for calendar API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"appointment-types", views.AppointmentTypeViewSet, basename="appointment-type")
router.register(r"availability-profiles", views.AvailabilityProfileViewSet, basename="availability-profile")
router.register(r"booking-links", views.BookingLinkViewSet, basename="booking-link")
router.register(r"appointments", views.AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]
