"""
ORBIT-EDU Database Models
==========================
Models = Python classes that define your database tables.
Django automatically creates the SQL tables from these classes.

Each class = one database table.
Each attribute = one column in that table.

Tables we create:
  1. Satellite        → Master list of satellites we track
  2. SatellitePosition → Every recorded position (the "trail")
  3. APODImage        → NASA Astronomy Picture of the Day cache
  4. SpaceEvent       → Upcoming ISS passes over a location
"""

from django.db import models
from django.utils import timezone


# ─── MODEL 1: SATELLITE ───────────────────────────────────────────────────────
class Satellite(models.Model):
    """
    Stores the master record for each satellite we track.

    Example row in database:
      id=1, name="International Space Station", norad_id="25544",
      description="Largest human-made object in orbit", is_active=True
    """

    # CharField = text field with a maximum length
    name = models.CharField(
        max_length=200,
        unique=True,           # No two satellites can have the same name
        help_text="Full official name of the satellite"
    )

    # NORAD catalog ID - the official number assigned to every object in orbit
    # The ISS is 25544. Used to fetch data from space-track.org
    norad_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="NORAD Catalog Number (ISS = 25544)"
    )

    # TextField = long text, no max length (for descriptions)
    description = models.TextField(
        blank=True,            # This field is optional
        default='',
        help_text="What is this satellite? What does it do?"
    )

    # The satellite's orbital altitude range in kilometers
    altitude_km = models.FloatField(
        null=True,             # Can be NULL in the database
        blank=True,            # Optional in forms
        help_text="Average orbital altitude in kilometers"
    )

    # Orbital period in minutes (ISS ≈ 92 minutes per orbit)
    orbital_period_min = models.FloatField(
        null=True,
        blank=True,
        help_text="Time to complete one full orbit (minutes)"
    )

    # BooleanField = True/False checkbox in the database
    is_active = models.BooleanField(
        default=True,
        help_text="Is this satellite currently being tracked?"
    )

    # DateTimeField = stores a date AND time
    # auto_now_add=True means: automatically set this to RIGHT NOW when created
    created_at = models.DateTimeField(auto_now_add=True)

    # auto_now=True means: automatically update this every time the record saves
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # How to sort results when you query Satellite.objects.all()
        ordering = ['name']

        # Human-readable names for Django admin panel
        verbose_name = 'Satellite'
        verbose_name_plural = 'Satellites'

    def __str__(self):
        # What shows up in Django admin and print() statements
        return f"{self.name} (NORAD: {self.norad_id})"


# ─── MODEL 2: SATELLITE POSITION ──────────────────────────────────────────────
class SatellitePosition(models.Model):
    """
    Stores every recorded position of a satellite.
    This builds the "trail" you see in the 3D visualization.

    Example row:
      satellite=ISS, latitude=28.5, longitude=-80.6,
      altitude=408.3, velocity=7.66, timestamp=2024-01-15 14:32:00 UTC
    """

    # ForeignKey = links this position to a Satellite record
    # on_delete=CASCADE means: if the Satellite is deleted, delete all its positions too
    # related_name='positions' lets us do: iss.positions.all() to get all ISS positions
    satellite = models.ForeignKey(
        Satellite,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text="Which satellite this position belongs to"
    )

    # Geographic coordinates
    # DecimalField stores numbers with exact decimal precision (important for coordinates)
    # max_digits=9, decimal_places=6 = up to 999.999999 (enough for any lat/lon)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude in degrees (-90 to +90)"
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude in degrees (-180 to +180)"
    )

    # Altitude above sea level in kilometers
    altitude = models.FloatField(
        help_text="Altitude above Earth's surface in kilometers"
    )

    # Speed in km/s (ISS travels at ~7.66 km/s = 27,576 km/h)
    velocity = models.FloatField(
        null=True,
        blank=True,
        help_text="Orbital velocity in km/s"
    )

    # Exact moment this position was recorded (from the API, not when we saved it)
    timestamp = models.DateTimeField(
        help_text="Exact UTC time this position was recorded by the satellite API"
    )

    # When WE saved it to our database (auto-set by Django)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']   # Newest first
        verbose_name = 'Satellite Position'
        verbose_name_plural = 'Satellite Positions'

        # Database index: speeds up queries that filter by satellite + timestamp
        indexes = [
            models.Index(fields=['satellite', '-timestamp']),
        ]

    def __str__(self):
        return (
            f"{self.satellite.name} @ "
            f"({self.latitude}, {self.longitude}) "
            f"at {self.timestamp.strftime('%Y-%m-%d %H:%M UTC')}"
        )


# ─── MODEL 3: APOD IMAGE ──────────────────────────────────────────────────────
class APODImage(models.Model):
    """
    Caches NASA's Astronomy Picture of the Day.

    Why cache? Because:
    1. The NASA API has rate limits (1000 calls/day with DEMO_KEY)
    2. We don't need to fetch it more than once per day
    3. If NASA's API is down, we still have the last image

    Example row:
      date=2024-01-15, title="The Pillars of Creation",
      url="https://apod.nasa.gov/...", media_type="image"
    """

    # DateField = stores just a date (no time)
    # unique=True: only one APOD per day (makes sense — NASA posts one per day)
    date = models.DateField(
        unique=True,
        help_text="Date of this APOD entry (YYYY-MM-DD)"
    )

    title = models.CharField(
        max_length=500,
        help_text="Title of the astronomy picture/video"
    )

    explanation = models.TextField(
        help_text="NASA's explanation of the image"
    )

    # The direct URL to the image or video
    url = models.URLField(
        max_length=1000,
        help_text="Direct URL to the image or video"
    )

    # Sometimes APOD shows a video (YouTube embed) instead of a photo
    hdurl = models.URLField(
        max_length=1000,
        blank=True,
        default='',
        help_text="High-definition image URL (not available for videos)"
    )

    # 'image' or 'video'
    media_type = models.CharField(
        max_length=20,
        default='image',
        help_text="Type of media: 'image' or 'video'"
    )

    # The photographer/copyright holder (NASA images are usually public domain)
    copyright = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Copyright holder (blank = public domain)"
    )

    # When WE fetched and saved this from NASA
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'APOD Image'
        verbose_name_plural = 'APOD Images'

    def __str__(self):
        return f"APOD: {self.title} ({self.date})"


# ─── MODEL 4: SPACE EVENT ─────────────────────────────────────────────────────
class SpaceEvent(models.Model):
    """
    Stores upcoming ISS pass times over specific locations on Earth.
    Uses the 'When the ISS passes above?' endpoint from open-notify.org

    Example row:
      location_name="New Delhi", latitude=28.61, longitude=77.20,
      rise_time=2024-01-16 03:45:00 UTC, duration_seconds=312
    """

    # The name the user gave their location
    location_name = models.CharField(
        max_length=200,
        help_text="User-friendly name for the location (e.g., 'New Delhi')"
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Observer's latitude"
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Observer's longitude"
    )

    # When the ISS will rise above the horizon
    rise_time = models.DateTimeField(
        help_text="UTC time when ISS rises above 10° elevation"
    )

    # How long the pass will last in seconds
    duration_seconds = models.IntegerField(
        help_text="How many seconds the ISS will be visible"
    )

    # Max elevation angle in degrees (90° = directly overhead)
    max_elevation = models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum elevation angle during this pass (degrees)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rise_time']
        verbose_name = 'Space Event'
        verbose_name_plural = 'Space Events'

    def __str__(self):
        return (
            f"ISS pass over {self.location_name} "
            f"at {self.rise_time.strftime('%Y-%m-%d %H:%M UTC')} "
            f"({self.duration_seconds}s)"
        )
