"""
ORBIT-EDU Serializers
======================
Serializers convert Python/Django model objects ↔ JSON.

When our frontend calls /api/iss/location/, Django:
  1. Fetches the latest ISS position from the database (a Python object)
  2. The serializer converts it to a JSON dictionary
  3. Django REST Framework sends that JSON to the browser

Think of a serializer as a "translator" between Python and JSON.

Each serializer class maps to one Model class.
The 'fields' list controls which columns appear in the JSON response.
"""

from rest_framework import serializers
from .models import Satellite, SatellitePosition, APODImage, SpaceEvent


# ─── SATELLITE SERIALIZER ─────────────────────────────────────────────────────
class SatelliteSerializer(serializers.ModelSerializer):
    """
    Converts a Satellite model instance to JSON.

    JSON output example:
    {
        "id": 1,
        "name": "International Space Station",
        "norad_id": "25544",
        "description": "Largest human-made structure in orbit...",
        "altitude_km": 408.0,
        "orbital_period_min": 92.9,
        "is_active": true
    }
    """

    class Meta:
        model = Satellite          # Which model to serialize
        fields = [                 # Which fields to include in JSON
            'id',
            'name',
            'norad_id',
            'description',
            'altitude_km',
            'orbital_period_min',
            'is_active',
            'created_at',
            'updated_at',
        ]
        # read_only_fields: These fields are shown in output but CANNOT be set via API
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── SATELLITE POSITION SERIALIZER ────────────────────────────────────────────
class SatellitePositionSerializer(serializers.ModelSerializer):
    """
    Converts a SatellitePosition to JSON.

    JSON output example:
    {
        "id": 4821,
        "satellite_name": "International Space Station",
        "latitude": "28.500000",
        "longitude": "-80.600000",
        "altitude": 408.3,
        "velocity": 7.66,
        "timestamp": "2024-01-15T14:32:00Z"
    }
    """

    # SerializerMethodField: Add a custom computed field that doesn't exist in the model.
    # It calls the method named 'get_<field_name>' automatically.
    satellite_name = serializers.SerializerMethodField()

    def get_satellite_name(self, obj):
        """
        obj = the SatellitePosition instance being serialized.
        obj.satellite = the related Satellite object (Django fetches it automatically).
        We return just the name string for easy display in the frontend.
        """
        return obj.satellite.name

    class Meta:
        model = SatellitePosition
        fields = [
            'id',
            'satellite_name',   # Custom field defined above
            'latitude',
            'longitude',
            'altitude',
            'velocity',
            'timestamp',
            'recorded_at',
        ]
        read_only_fields = ['id', 'recorded_at']


# ─── APOD SERIALIZER ──────────────────────────────────────────────────────────
class APODImageSerializer(serializers.ModelSerializer):
    """
    Converts a NASA APOD record to JSON.

    JSON output example:
    {
        "id": 7,
        "date": "2024-01-15",
        "title": "The Pillars of Creation",
        "explanation": "These towering clouds of gas and dust...",
        "url": "https://apod.nasa.gov/apod/image/2401/pillars.jpg",
        "hdurl": "https://apod.nasa.gov/apod/image/2401/pillars_hd.jpg",
        "media_type": "image",
        "copyright": ""
    }
    """

    class Meta:
        model = APODImage
        fields = [
            'id',
            'date',
            'title',
            'explanation',
            'url',
            'hdurl',
            'media_type',
            'copyright',
            'fetched_at',
        ]
        read_only_fields = ['id', 'fetched_at']


# ─── SPACE EVENT SERIALIZER ───────────────────────────────────────────────────
class SpaceEventSerializer(serializers.ModelSerializer):
    """
    Converts an ISS pass event to JSON.

    JSON output example:
    {
        "id": 12,
        "location_name": "New Delhi",
        "latitude": "28.610000",
        "longitude": "77.200000",
        "rise_time": "2024-01-16T03:45:00Z",
        "duration_seconds": 312,
        "duration_minutes": 5.2,
        "max_elevation": 67.4
    }
    """

    # Computed field: convert duration from seconds to minutes for convenience
    duration_minutes = serializers.SerializerMethodField()

    def get_duration_minutes(self, obj):
        """Round to 1 decimal place. Example: 312 seconds → 5.2 minutes"""
        return round(obj.duration_seconds / 60, 1)

    class Meta:
        model = SpaceEvent
        fields = [
            'id',
            'location_name',
            'latitude',
            'longitude',
            'rise_time',
            'duration_seconds',
            'duration_minutes',   # Custom computed field
            'max_elevation',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── LIVE ISS DATA SERIALIZER (No Model) ──────────────────────────────────────
class LiveISSSerializer(serializers.Serializer):
    """
    A serializer WITHOUT a model — for validating/formatting live API data.
    We use this to format the raw JSON from open-notify.org into our
    own clean format before sending it to the frontend.

    This is NOT stored in the database — it's just a pass-through formatter.

    JSON output example:
    {
        "latitude": 28.5,
        "longitude": -80.6,
        "altitude": 408.3,
        "velocity": 7.66,
        "timestamp": 1705328520,
        "visibility": "daylight",
        "footprint": 4541.7
    }
    """
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()
    velocity = serializers.FloatField(required=False, default=0)
    timestamp = serializers.IntegerField()
    visibility = serializers.CharField(required=False, default='unknown')
    footprint = serializers.FloatField(required=False, default=0)
