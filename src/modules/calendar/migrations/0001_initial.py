# Generated migration for calendar module

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("firm", "0001_initial"),
        ("crm", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AppointmentType",
            fields=[
                ("appointment_type_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(help_text="Display name for this appointment type", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Description shown to bookers")),
                ("duration_minutes", models.IntegerField(help_text="Meeting duration in minutes")),
                ("buffer_before_minutes", models.IntegerField(default=0, help_text="Buffer time before meeting (minutes)")),
                ("buffer_after_minutes", models.IntegerField(default=0, help_text="Buffer time after meeting (minutes)")),
                ("location_mode", models.CharField(choices=[("video", "Video Call"), ("phone", "Phone Call"), ("in_person", "In Person"), ("custom", "Custom")], default="video", help_text="How the meeting will be conducted", max_length=20)),
                ("location_details", models.TextField(blank=True, help_text="Additional location info (e.g., Zoom link, address)")),
                ("allow_portal_booking", models.BooleanField(default=True, help_text="Can portal users book this type?")),
                ("allow_staff_booking", models.BooleanField(default=True, help_text="Can staff book this type?")),
                ("allow_public_prospect_booking", models.BooleanField(default=False, help_text="Can public prospects book this type?")),
                ("requires_approval", models.BooleanField(default=False, help_text="Does this appointment need approval before confirmation?")),
                ("routing_policy", models.CharField(choices=[("fixed_staff", "Fixed Staff Member"), ("round_robin_pool", "Round Robin Pool"), ("engagement_owner", "Engagement Owner"), ("service_line_owner", "Service Line Owner")], default="fixed_staff", help_text="How to route appointments to staff", max_length=30)),
                ("intake_questions", models.JSONField(blank=True, default=list, help_text="List of intake questions to ask during booking (JSON array)")),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", help_text="Active or inactive", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_appointment_types", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(help_text="Firm this appointment type belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="appointment_types", to="firm.firm")),
                ("fixed_staff_user", models.ForeignKey(blank=True, help_text="If routing_policy = fixed_staff, this is the assigned user", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="fixed_appointment_types", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calendar_appointment_types",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="AvailabilityProfile",
            fields=[
                ("availability_profile_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("owner_type", models.CharField(choices=[("staff", "Staff Member"), ("team", "Team Pool")], default="staff", help_text="Staff or team", max_length=20)),
                ("owner_team_name", models.CharField(blank=True, help_text="If owner_type = team, this is the team name", max_length=255)),
                ("name", models.CharField(help_text="Profile name", max_length=255)),
                ("timezone", models.CharField(default="UTC", help_text="Timezone for availability computation", max_length=100)),
                ("weekly_hours", models.JSONField(default=dict, help_text="Weekly availability by day (JSON: {monday: [{start: '09:00', end: '17:00'}], ...})")),
                ("exceptions", models.JSONField(default=list, help_text="Exception dates (JSON array of {date: 'YYYY-MM-DD', reason: 'Holiday'})")),
                ("min_notice_minutes", models.IntegerField(default=60, help_text="Minimum notice required before booking (minutes)")),
                ("max_future_days", models.IntegerField(default=60, help_text="Maximum days in advance for booking")),
                ("slot_rounding_minutes", models.IntegerField(default=15, help_text="Round slots to nearest N minutes")),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", help_text="Active or inactive", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_availability_profiles", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(help_text="Firm this profile belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="availability_profiles", to="firm.firm")),
                ("owner_staff_user", models.ForeignKey(blank=True, help_text="If owner_type = staff, this is the user", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="availability_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calendar_availability_profiles",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="BookingLink",
            fields=[
                ("booking_link_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("visibility", models.CharField(choices=[("portal_only", "Portal Only"), ("staff_only", "Staff Only"), ("public", "Public")], default="portal_only", help_text="Who can access this link", max_length=20)),
                ("slug", models.SlugField(help_text="URL slug for this booking link", max_length=100, unique=True)),
                ("token", models.UUIDField(default=uuid.uuid4, help_text="Unique token for security", unique=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", help_text="Active or inactive", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.ForeignKey(blank=True, help_text="Optional: link to specific account", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="booking_links", to="crm.account")),
                ("appointment_type", models.ForeignKey(help_text="Appointment type for this link", on_delete=django.db.models.deletion.CASCADE, related_name="booking_links", to="calendar.appointmenttype")),
                ("availability_profile", models.ForeignKey(blank=True, help_text="Availability profile (optional; used for routing)", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="booking_links", to="calendar.availabilityprofile")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_booking_links", to=settings.AUTH_USER_MODEL)),
                ("engagement", models.ForeignKey(blank=True, help_text="Optional: link to specific engagement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="booking_links", to="crm.engagement")),
                ("firm", models.ForeignKey(help_text="Firm this link belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="booking_links", to="firm.firm")),
            ],
            options={
                "db_table": "calendar_booking_links",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("appointment_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("start_time", models.DateTimeField(help_text="Appointment start time (UTC)")),
                ("end_time", models.DateTimeField(help_text="Appointment end time (UTC)")),
                ("timezone", models.CharField(default="UTC", help_text="Timezone for display", max_length=100)),
                ("intake_responses", models.JSONField(blank=True, default=dict, help_text="Responses to intake questions (JSON)")),
                ("status", models.CharField(choices=[("requested", "Requested (Needs Approval)"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed"), ("no_show", "No Show")], default="confirmed", help_text="Appointment status", max_length=20)),
                ("status_reason", models.TextField(blank=True, help_text="Reason for status (e.g., cancellation reason)")),
                ("external_event_id", models.CharField(blank=True, help_text="External calendar event ID (if synced)", max_length=512)),
                ("booked_at", models.DateTimeField(auto_now_add=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.ForeignKey(blank=True, help_text="Account for this appointment (if applicable)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="appointments", to="crm.account")),
                ("appointment_type", models.ForeignKey(help_text="Appointment type", on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="calendar.appointmenttype")),
                ("booked_by", models.ForeignKey(help_text="User who booked this appointment", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="booked_appointments", to=settings.AUTH_USER_MODEL)),
                ("booking_link", models.ForeignKey(blank=True, help_text="Booking link used (if applicable)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="appointments", to="calendar.bookinglink")),
                ("contact", models.ForeignKey(blank=True, help_text="Contact for this appointment (if applicable)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="appointments", to="crm.contact")),
                ("firm", models.ForeignKey(help_text="Firm this appointment belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to="firm.firm")),
                ("staff_user", models.ForeignKey(help_text="Staff member for this appointment", on_delete=django.db.models.deletion.PROTECT, related_name="staff_appointments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calendar_appointments",
                "ordering": ["start_time"],
            },
        ),
        migrations.CreateModel(
            name="AppointmentStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(help_text="Previous status", max_length=20)),
                ("to_status", models.CharField(help_text="New status", max_length=20)),
                ("reason", models.TextField(blank=True, help_text="Reason for status change")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("appointment", models.ForeignKey(help_text="Appointment for this status change", on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="calendar.appointment")),
                ("changed_by", models.ForeignKey(help_text="User who changed the status", null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "calendar_appointment_status_history",
                "ordering": ["-changed_at"],
            },
        ),
        # Indexes
        migrations.AddIndex(
            model_name="appointmenttype",
            index=models.Index(fields=["firm", "status"], name="calendar_ap_firm_id_3a8e2d_idx"),
        ),
        migrations.AddIndex(
            model_name="availabilityprofile",
            index=models.Index(fields=["firm", "owner_type", "owner_staff_user"], name="calendar_av_firm_id_7d4c1a_idx"),
        ),
        migrations.AddIndex(
            model_name="bookinglink",
            index=models.Index(fields=["firm", "status"], name="calendar_bo_firm_id_5e9b2f_idx"),
        ),
        migrations.AddIndex(
            model_name="bookinglink",
            index=models.Index(fields=["slug"], name="calendar_bo_slug_8a3d4e_idx"),
        ),
        migrations.AddIndex(
            model_name="bookinglink",
            index=models.Index(fields=["token"], name="calendar_bo_token_2f6c1b_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["firm", "staff_user", "start_time"], name="calendar_ap_firm_id_9b2e5a_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["firm", "account"], name="calendar_ap_firm_id_4c7d1f_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["firm", "status"], name="calendar_ap_firm_id_6e3a8b_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["external_event_id"], name="calendar_ap_externa_1d5f9c_idx"),
        ),
        migrations.AddIndex(
            model_name="appointmentstatushistory",
            index=models.Index(fields=["appointment", "changed_at"], name="calendar_ap_appoint_7a4e2d_idx"),
        ),
    ]
