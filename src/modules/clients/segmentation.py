"""
Contact segmentation utilities.

Provides advanced segmentation and filtering capabilities:
- Geographic segmentation (radius search, region filtering)
- Behavioral segmentation
- Advanced segment builder with nested conditions
- Dynamic segment evaluation
"""
from typing import Dict, List, Optional, Any
from django.db import connection
from django.db.models import Q, F, Count, Avg, Sum, Max, Min, Value, FloatField, Func
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Cos, Sin, Radians
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import math

from modules.clients.models import Contact, Client


class GeographicSegmenter:
    """Handle geographic-based contact segmentation."""
    
    # Approximate radius of Earth in kilometers
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two geographic points using Haversine formula.
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
        
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return GeographicSegmenter.EARTH_RADIUS_KM * c
    
    @staticmethod
    def filter_by_radius(
        queryset,
        center_lat: float,
        center_lon: float,
        radius_km: float,
    ):
        """
        Filter contacts within a radius of a center point.
        
        **KNOWN LIMITATION / TODO:**
        This is a placeholder implementation that returns the queryset unchanged.
        To implement proper geographic filtering, you need to:
        
        1. Add geographic fields (latitude, longitude) to the Contact model or
           a related Address model
        2. Use a spatial database extension like PostGIS for PostgreSQL
        3. Create spatial indexes for performance
        4. Implement the Haversine distance formula in a database function
        
        Example implementation with PostGIS:
        ```python
        from django.contrib.gis.db.models.functions import Distance
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D
        
        center = Point(center_lon, center_lat, srid=4326)
        return queryset.filter(
            location__distance_lte=(center, D(km=radius_km))
        ).annotate(distance=Distance('location', center))
        ```
        
        Args:
            queryset: Contact queryset to filter
            center_lat, center_lon: Center point coordinates
            radius_km: Radius in kilometers
        
        Returns:
            Filtered queryset (currently unchanged - placeholder)
        """
        queryset = queryset.filter(latitude__isnull=False, longitude__isnull=False)

        if connection.vendor == "sqlite":
            contact_coords = queryset.values("id", "latitude", "longitude")
            matching_ids = [
                row["id"]
                for row in contact_coords
                if GeographicSegmenter.calculate_distance(
                    center_lat,
                    center_lon,
                    float(row["latitude"]),
                    float(row["longitude"]),
                )
                <= radius_km
            ]
            return queryset.filter(id__in=matching_ids)

        lat1 = Value(center_lat)
        lon1 = Value(center_lon)

        distance_expr = ExpressionWrapper(
            GeographicSegmenter.EARTH_RADIUS_KM
            * Func(
                Cos(Radians(lat1))
                * Cos(Radians(F("latitude")))
                * Cos(Radians(F("longitude")) - Radians(lon1))
                + Sin(Radians(lat1)) * Sin(Radians(F("latitude"))),
                function="ACOS",
            ),
            output_field=FloatField(),
        )

        return queryset.annotate(distance_km=distance_expr).filter(distance_km__lte=radius_km)
    
    @staticmethod
    def filter_by_country(queryset, countries: List[str]):
        """
        Filter contacts by country.
        
        Falls back to client country when contact country is empty.
        """
        return queryset.filter(
            Q(country__in=countries) |
            Q(country__isnull=True, client__country__in=countries) |
            Q(country__exact="", client__country__in=countries)
        )
    
    @staticmethod
    def filter_by_state(queryset, states: List[str]):
        """
        Filter contacts by state/province.
        
        Falls back to client state when contact state is empty.
        """
        return queryset.filter(
            Q(state__in=states) |
            Q(state__isnull=True, client__state__in=states) |
            Q(state__exact="", client__state__in=states)
        )
    
    @staticmethod
    def filter_by_city(queryset, cities: List[str]):
        """
        Filter contacts by city.
        
        Falls back to client city when contact city is empty.
        """
        return queryset.filter(
            Q(city__in=cities) |
            Q(city__isnull=True, client__city__in=cities) |
            Q(city__exact="", client__city__in=cities)
        )
    
    @staticmethod
    def filter_by_postal_code(queryset, postal_codes: List[str]):
        """
        Filter contacts by postal code.
        
        Falls back to client postal code when contact postal code is empty.
        """
        return queryset.filter(
            Q(postal_code__in=postal_codes) |
            Q(postal_code__isnull=True, client__postal_code__in=postal_codes) |
            Q(postal_code__exact="", client__postal_code__in=postal_codes)
        )


class SegmentCondition:
    """
    Represents a single condition in a segment.
    
    Example:
        SegmentCondition('status', 'equals', 'active')
        SegmentCondition('created_at', 'greater_than', '2024-01-01')
    """
    
    OPERATORS = {
        'equals': lambda field, value: Q(**{field: value}),
        'not_equals': lambda field, value: ~Q(**{field: value}),
        'contains': lambda field, value: Q(**{f"{field}__icontains": value}),
        'not_contains': lambda field, value: ~Q(**{f"{field}__icontains": value}),
        'starts_with': lambda field, value: Q(**{f"{field}__istartswith": value}),
        'ends_with': lambda field, value: Q(**{f"{field}__iendswith": value}),
        'in': lambda field, value: Q(**{f"{field}__in": value}),
        'not_in': lambda field, value: ~Q(**{f"{field}__in": value}),
        'greater_than': lambda field, value: Q(**{f"{field}__gt": value}),
        'greater_than_or_equal': lambda field, value: Q(**{f"{field}__gte": value}),
        'less_than': lambda field, value: Q(**{f"{field}__lt": value}),
        'less_than_or_equal': lambda field, value: Q(**{f"{field}__lte": value}),
        'is_null': lambda field, value: Q(**{f"{field}__isnull": True}),
        'is_not_null': lambda field, value: Q(**{f"{field}__isnull": False}),
        'between': lambda field, value: Q(**{f"{field}__gte": value[0], f"{field}__lte": value[1]}),
    }
    
    def __init__(self, field: str, operator: str, value: Any):
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator}")
        
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_q(self) -> Q:
        """Convert condition to Django Q object."""
        return self.OPERATORS[self.operator](self.field, self.value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to dictionary for serialization."""
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SegmentCondition':
        """Create condition from dictionary."""
        return cls(
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
        )


class SegmentGroup:
    """
    A group of conditions combined with AND or OR logic.
    
    Supports nested groups for complex conditions.
    """
    
    def __init__(self, logic: str = 'AND'):
        if logic not in ['AND', 'OR']:
            raise ValueError("Logic must be 'AND' or 'OR'")
        
        self.logic = logic
        self.conditions: List[SegmentCondition] = []
        self.groups: List['SegmentGroup'] = []
    
    def add_condition(self, condition: SegmentCondition):
        """Add a condition to this group."""
        self.conditions.append(condition)
    
    def add_group(self, group: 'SegmentGroup'):
        """Add a nested group to this group."""
        self.groups.append(group)
    
    def to_q(self) -> Q:
        """Convert group to Django Q object."""
        q_objects = []
        
        # Add conditions
        for condition in self.conditions:
            q_objects.append(condition.to_q())
        
        # Add nested groups
        for group in self.groups:
            q_objects.append(group.to_q())
        
        if not q_objects:
            return Q()  # Empty Q object
        
        # Combine with AND or OR
        if self.logic == 'AND':
            result = q_objects[0]
            for q in q_objects[1:]:
                result &= q
        else:  # OR
            result = q_objects[0]
            for q in q_objects[1:]:
                result |= q
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary for serialization."""
        return {
            'logic': self.logic,
            'conditions': [c.to_dict() for c in self.conditions],
            'groups': [g.to_dict() for g in self.groups],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SegmentGroup':
        """Create group from dictionary."""
        group = cls(logic=data.get('logic', 'AND'))
        
        # Add conditions
        for cond_data in data.get('conditions', []):
            group.add_condition(SegmentCondition.from_dict(cond_data))
        
        # Add nested groups
        for group_data in data.get('groups', []):
            group.add_group(cls.from_dict(group_data))
        
        return group


class ContactSegment:
    """
    Advanced contact segmentation with nested conditions.
    
    Example usage:
        segment = ContactSegment(firm, "Active Marketing Contacts")
        
        # Add simple condition
        segment.add_condition('status', 'equals', 'active')
        
        # Add nested group
        group = SegmentGroup('OR')
        group.add_condition(SegmentCondition('job_title', 'contains', 'Manager'))
        group.add_condition(SegmentCondition('job_title', 'contains', 'Director'))
        segment.add_group(group)
        
        # Get contacts
        contacts = segment.get_contacts()
    """
    
    def __init__(self, client: Client = None, name: str = "Untitled Segment"):
        self.client = client
        self.name = name
        self.root_group = SegmentGroup('AND')
    
    def add_condition(self, field: str, operator: str, value: Any):
        """Add a condition to the root group."""
        condition = SegmentCondition(field, operator, value)
        self.root_group.add_condition(condition)
    
    def add_group(self, group: SegmentGroup):
        """Add a nested group to the root group."""
        self.root_group.add_group(group)
    
    def get_query(self) -> Q:
        """Get the Django Q object for this segment."""
        return self.root_group.to_q()
    
    def get_contacts(self):
        """Get contacts matching this segment."""
        queryset = Contact.objects.all()
        
        # Filter by client if specified
        if self.client:
            queryset = queryset.filter(client=self.client)
        
        # Apply segment conditions
        return queryset.filter(self.get_query())
    
    def count_contacts(self) -> int:
        """Count contacts matching this segment."""
        return self.get_contacts().count()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary for serialization."""
        return {
            'name': self.name,
            'client_id': self.client.id if self.client else None,
            'conditions': self.root_group.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], client: Client = None) -> 'ContactSegment':
        """Create segment from dictionary."""
        segment = cls(
            client=client,
            name=data.get('name', 'Untitled Segment'),
        )
        
        if 'conditions' in data:
            segment.root_group = SegmentGroup.from_dict(data['conditions'])
        
        return segment


class PrebuiltSegments:
    """Pre-built segment definitions for common use cases."""
    
    @staticmethod
    def active_contacts(client: Client) -> ContactSegment:
        """Segment for active contacts."""
        segment = ContactSegment(client, "Active Contacts")
        segment.add_condition('status', 'equals', Contact.STATUS_ACTIVE)
        return segment
    
    @staticmethod
    def marketing_contacts(client: Client) -> ContactSegment:
        """Segment for contacts who can receive marketing."""
        segment = ContactSegment(client, "Marketing Contacts")
        segment.add_condition('status', 'equals', Contact.STATUS_ACTIVE)
        segment.add_condition('opt_out_marketing', 'equals', False)
        return segment
    
    @staticmethod
    def bounced_contacts(client: Client) -> ContactSegment:
        """Segment for bounced contacts."""
        segment = ContactSegment(client, "Bounced Contacts")
        segment.add_condition('status', 'equals', Contact.STATUS_BOUNCED)
        return segment
    
    @staticmethod
    def inactive_contacts(client: Client, days: int = 180) -> ContactSegment:
        """Segment for contacts inactive for specified days."""
        segment = ContactSegment(client, f"Inactive for {days}+ Days")
        cutoff_date = timezone.now() - timedelta(days=days)
        segment.add_condition('updated_at', 'less_than', cutoff_date)
        return segment
    
    @staticmethod
    def recent_contacts(client: Client, days: int = 30) -> ContactSegment:
        """Segment for recently added contacts."""
        segment = ContactSegment(client, f"Added in Last {days} Days")
        cutoff_date = timezone.now() - timedelta(days=days)
        segment.add_condition('created_at', 'greater_than_or_equal', cutoff_date)
        return segment
    
    @staticmethod
    def primary_contacts(client: Client) -> ContactSegment:
        """Segment for primary contacts."""
        segment = ContactSegment(client, "Primary Contacts")
        segment.add_condition('is_primary_contact', 'equals', True)
        return segment
    
    @staticmethod
    def billing_contacts(client: Client) -> ContactSegment:
        """Segment for contacts who receive billing emails."""
        segment = ContactSegment(client, "Billing Contacts")
        segment.add_condition('receives_billing_emails', 'equals', True)
        return segment
