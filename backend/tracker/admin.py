"""
ORBIT-EDU Django Admin Configuration
======================================
Registering models here makes them appear in Django's built-in admin panel.
Visit /admin in your browser (after creating a superuser) to:
  - View all satellite position records
  - Browse every APOD image we've cached
  - See all ISS pass events
  - Manually add/edit/delete any record

The @admin.register() decorator is a shortcut for:
  admin.site.register(ModelName, ModelNameAdmin)
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Satellite, SatellitePosition, APODImage, SpaceEvent


# ─── SATELLITE ADMIN ──────────────────────────────────────────────────────────
@admin.register(Satellite)
class SatelliteAdmin(admin.ModelAdmin):
    """
    Customizes how Satellite records appear in the admin panel.
    """

    # Columns shown in the list view (like a spreadsheet)
    list_display = ['name', 'norad_id', 'altitude_km', 'orbital_period_min', 'is_active']

    # Add a sidebar filter by is_active
    list_filter = ['is_active']

    # Enable a search bar that searches these fields
    search_fields = ['name', 'norad_id']

    # Fields that can be edited directly in the list view (click to edit)
    list_editable = ['is_active']

    # How the form is organized when you click on a record
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'norad_id', 'description', 'is_active')
        }),
        ('Orbital Parameters', {
            'fields': ('altitude_km', 'orbital_period_min'),
            'classes': ('collapse',)   # Collapsed by default
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # These are auto-set so they're read-only in the form
    readonly_fields = ['created_at', 'updated_at']


# ─── SATELLITE POSITION ADMIN ─────────────────────────────────────────────────
@admin.register(SatellitePosition)
class SatellitePositionAdmin(admin.ModelAdmin):
    """
    Shows the history of recorded positions.
    """

    list_display = ['satellite', 'latitude', 'longitude', 'altitude', 'velocity', 'timestamp']
    list_filter = ['satellite']
    search_fields = ['satellite__name']
    readonly_fields = ['recorded_at']

    # Show newest records first
    ordering = ['-timestamp']

    # Paginate to 25 records per page (we might have thousands)
    list_per_page = 25

    # Date-based navigation in the right sidebar
    date_hierarchy = 'timestamp'


# ─── APOD ADMIN ───────────────────────────────────────────────────────────────
@admin.register(APODImage)
class APODImageAdmin(admin.ModelAdmin):
    """
    Shows NASA APOD cache with a preview of the image.
    """

    list_display = ['date', 'title', 'media_type', 'image_preview', 'fetched_at']
    list_filter = ['media_type']
    search_fields = ['title', 'explanation']
    readonly_fields = ['fetched_at', 'image_preview']
    ordering = ['-date']
    date_hierarchy = 'date'

    def image_preview(self, obj):
        """
        Custom column that shows a small thumbnail of the APOD image.
        format_html() safely creates HTML — never use plain string formatting with HTML!
        """
        if obj.media_type == 'image' and obj.url:
            return format_html(
                '<img src="{}" style="max-height:50px; max-width:100px; object-fit:cover;" />',
                obj.url
            )
        elif obj.media_type == 'video':
            return format_html('<span style="color: orange;">📹 Video</span>')
        return '—'

    # Column header name for the admin table
    image_preview.short_description = 'Preview'


# ─── SPACE EVENT ADMIN ────────────────────────────────────────────────────────
@admin.register(SpaceEvent)
class SpaceEventAdmin(admin.ModelAdmin):
    """
    Shows upcoming ISS passes.
    """

    list_display = ['location_name', 'latitude', 'longitude', 'rise_time', 'duration_seconds']
    search_fields = ['location_name']
    ordering = ['rise_time']
    readonly_fields = ['created_at']
    date_hierarchy = 'rise_time'

    list_per_page = 20
