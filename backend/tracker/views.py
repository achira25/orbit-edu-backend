"""
ORBIT-EDU API Views
====================
Views = the functions that run when someone calls an API endpoint.

When your frontend does: fetch('https://your-app.railway.app/api/iss/location/')
Django routes that request to one of the view functions/classes below.

Each view:
  1. Receives the HTTP request
  2. Does its work (fetch data, query DB, call external API)
  3. Returns a JSON response

Our Endpoints:
  GET /api/iss/location/          → Live ISS position (fetched fresh from open-notify)
  GET /api/iss/history/           → Last 50 recorded ISS positions from our DB
  GET /api/apod/                  → Today's NASA Astronomy Picture of the Day
  GET /api/apod/<date>/           → APOD for a specific date (YYYY-MM-DD)
  GET /api/satellites/            → List of all satellites we track
  GET /api/passes/?lat=28&lon=77  → Upcoming ISS passes over a location
  GET /api/astronauts/            → Currently who is in space
  GET /api/health/                → Simple health check endpoint
"""

import requests
import logging
from datetime import datetime, date, timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .models import Satellite, SatellitePosition, APODImage, SpaceEvent
from .serializers import (
    SatelliteSerializer,
    SatellitePositionSerializer,
    APODImageSerializer,
    SpaceEventSerializer,
    LiveISSSerializer,
)

# Set up logging — these messages appear in Railway's log console
logger = logging.getLogger(__name__)


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def fetch_iss_from_api():
    """
    Fetches the current ISS position from the open-notify.org API.

    API endpoint: http://api.open-notify.org/iss-now.json
    Returns raw JSON like:
    {
        "message": "success",
        "timestamp": 1705328520,
        "iss_position": {
            "latitude": "28.5000",
            "longitude": "-80.6000"
        }
    }

    We also call wheretheiss.at for more detailed data (altitude, velocity).
    Returns: dict with all position data, or None if both APIs fail.
    """

    # ── Primary source: wheretheiss.at (has altitude + velocity) ──────────
    try:
        response = requests.get(
            'https://api.wheretheiss.at/v1/satellites/25544',
            timeout=5    # Give up after 5 seconds so we don't hang
        )
        response.raise_for_status()   # Raise exception if status is 4xx or 5xx
        data = response.json()

        # wheretheiss.at returns:
        # { "id":25544, "name":"iss", "latitude":28.5, "longitude":-80.6,
        #   "altitude":408.3, "velocity":27576, "visibility":"daylight",
        #   "footprint":4541.7, "timestamp":1705328520, ... }
        return {
            'latitude':   data['latitude'],
            'longitude':  data['longitude'],
            'altitude':   data['altitude'],       # km
            'velocity':   data['velocity'] / 3600, # km/h → km/s
            'timestamp':  data['timestamp'],
            'visibility': data.get('visibility', 'unknown'),
            'footprint':  data.get('footprint', 0),
        }

    except requests.RequestException as e:
        logger.warning(f"wheretheiss.at failed: {e}. Trying open-notify fallback...")

    # ── Fallback: open-notify.org (simpler, no altitude/velocity) ──────────
    try:
        response = requests.get(
            f"{settings.ISS_API_BASE_URL}/iss-now.json",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        pos = data['iss_position']
        return {
            'latitude':   float(pos['latitude']),
            'longitude':  float(pos['longitude']),
            'altitude':   408.0,    # Approximate average ISS altitude
            'velocity':   7.66,     # Approximate average ISS velocity
            'timestamp':  data['timestamp'],
            'visibility': 'unknown',
            'footprint':  0,
        }

    except requests.RequestException as e:
        logger.error(f"open-notify fallback also failed: {e}")
        return None


def save_iss_position(position_data):
    """
    Saves a fetched ISS position to our database.
    This builds up the historical trail over time.

    We get-or-create the ISS satellite record first, then save the position.
    """
    try:
        # get_or_create: Look for ISS in DB, create it if it doesn't exist yet
        # Returns a tuple: (satellite_object, was_created_boolean)
        iss, created = Satellite.objects.get_or_create(
            norad_id='25544',
            defaults={
                'name': 'International Space Station',
                'description': (
                    'The ISS is a modular space station in low Earth orbit. '
                    'It is a multinational collaborative project involving NASA, '
                    'Roscosmos, JAXA, ESA, and CSA. The ISS serves as a '
                    'microgravity and space environment research laboratory.'
                ),
                'altitude_km': 408.0,
                'orbital_period_min': 92.9,
            }
        )

        if created:
            logger.info("Created ISS satellite record in database")

        # Convert Unix timestamp to Django timezone-aware datetime
        ts = datetime.fromtimestamp(position_data['timestamp'], tz=timezone.utc)

        # Create the position record
        # get_or_create avoids duplicate entries if called twice in the same second
        pos, created = SatellitePosition.objects.get_or_create(
            satellite=iss,
            timestamp=ts,
            defaults={
                'latitude':  position_data['latitude'],
                'longitude': position_data['longitude'],
                'altitude':  position_data['altitude'],
                'velocity':  position_data.get('velocity', 7.66),
            }
        )

        return pos

    except Exception as e:
        logger.error(f"Failed to save ISS position: {e}")
        return None


def fetch_apod_from_nasa(target_date=None):
    """
    Fetches Astronomy Picture of the Day from NASA's API.

    API: https://api.nasa.gov/planetary/apod
    Params: api_key (your NASA key), date (YYYY-MM-DD, optional)

    NASA APOD JSON response:
    {
        "date": "2024-01-15",
        "title": "The Pillars of Creation",
        "explanation": "...",
        "url": "https://apod.nasa.gov/apod/image/...",
        "hdurl": "https://apod.nasa.gov/apod/image/..._hd.jpg",
        "media_type": "image",
        "copyright": "ESA/Hubble"
    }
    """
    params = {
        'api_key': settings.NASA_API_KEY,
        'thumbs': True,    # If media_type is video, also return a thumbnail
    }

    if target_date:
        params['date'] = str(target_date)   # Must be 'YYYY-MM-DD' string

    try:
        response = requests.get(
            'https://api.nasa.gov/planetary/apod',
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.error(f"NASA APOD API failed: {e}")
        return None


# ─── VIEW 1: LIVE ISS LOCATION ────────────────────────────────────────────────
class ISSLocationView(APIView):
    """
    GET /api/iss/location/

    Fetches the current ISS position from external API,
    saves it to our database, and returns it to the frontend.

    Response JSON:
    {
        "success": true,
        "data": {
            "latitude": 28.5,
            "longitude": -80.6,
            "altitude": 408.3,
            "velocity": 7.66,
            "timestamp": 1705328520,
            "visibility": "daylight",
            "footprint": 4541.7
        },
        "source": "live"
    }
    """

    def get(self, request):
        # Fetch fresh data from the external API
        position_data = fetch_iss_from_api()

        if position_data is None:
            # Both APIs failed — try to return the last known position from DB
            logger.warning("Live APIs failed, returning last known position from DB")

            last_position = SatellitePosition.objects.filter(
                satellite__norad_id='25544'
            ).first()  # .first() gets newest because we order by -timestamp

            if last_position:
                serializer = SatellitePositionSerializer(last_position)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'source': 'cached',
                    'warning': 'Live API unavailable, showing last known position'
                })
            else:
                return Response(
                    {'success': False, 'error': 'Could not fetch ISS location'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        # Save this position to our database (builds the trail)
        save_iss_position(position_data)

        # Validate and serialize the data
        serializer = LiveISSSerializer(data=position_data)
        if serializer.is_valid():
            return Response({
                'success': True,
                'data': serializer.validated_data,
                'source': 'live'
            })
        else:
            # Data came back but in unexpected format — return it raw
            return Response({
                'success': True,
                'data': position_data,
                'source': 'live_raw'
            })


# ─── VIEW 2: ISS POSITION HISTORY ─────────────────────────────────────────────
class ISSHistoryView(APIView):
    """
    GET /api/iss/history/
    GET /api/iss/history/?limit=100

    Returns the last N recorded ISS positions from our database.
    The frontend uses this to draw the orbital trail line.

    Response JSON:
    {
        "success": true,
        "count": 50,
        "data": [
            {"latitude": "28.5", "longitude": "-80.6", "timestamp": "..."},
            ...
        ]
    }
    """

    def get(self, request):
        # ?limit=100 → get up to 100 positions
        # request.query_params is like request.GET in plain Django
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 500)   # Cap at 500 so we don't return millions of rows

        positions = SatellitePosition.objects.filter(
            satellite__norad_id='25544'
        ).order_by('-timestamp')[:limit]   # [:limit] = SQL LIMIT clause

        serializer = SatellitePositionSerializer(positions, many=True)
        # many=True means: serialize a list of objects, not just one

        return Response({
            'success': True,
            'count': positions.count(),
            'data': serializer.data
        })


# ─── VIEW 3: NASA APOD ────────────────────────────────────────────────────────
class APODView(APIView):
    """
    GET /api/apod/              → Today's APOD
    GET /api/apod/?date=2024-01-15 → APOD for specific date

    First checks our database cache. If not found, fetches from NASA API.
    This reduces NASA API calls (important since DEMO_KEY = 30 calls/hour).

    Response JSON:
    {
        "success": true,
        "data": {
            "date": "2024-01-15",
            "title": "The Pillars of Creation",
            "explanation": "...",
            "url": "https://apod.nasa.gov/...",
            "hdurl": "...",
            "media_type": "image",
            "copyright": ""
        },
        "source": "cache"
    }
    """

    def get(self, request):
        # Parse date from query string, default to today
        date_str = request.query_params.get('date', None)

        if date_str:
            try:
                # strptime = string parse time (converts '2024-01-15' to date object)
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = date.today()

        # ── Check our database cache first ────────────────────────────────
        try:
            cached_apod = APODImage.objects.get(date=target_date)
            serializer = APODImageSerializer(cached_apod)
            logger.info(f"Serving APOD from cache for {target_date}")
            return Response({
                'success': True,
                'data': serializer.data,
                'source': 'cache'
            })
        except APODImage.DoesNotExist:
            pass   # Not in cache, need to fetch from NASA

        # ── Fetch from NASA API ───────────────────────────────────────────
        nasa_data = fetch_apod_from_nasa(target_date)

        if nasa_data is None:
            return Response(
                {'success': False, 'error': 'NASA API unavailable and no cached data found'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Save to our database so next request is served from cache
        apod = APODImage.objects.create(
            date=nasa_data.get('date', str(target_date)),
            title=nasa_data.get('title', 'Unknown'),
            explanation=nasa_data.get('explanation', ''),
            url=nasa_data.get('url', ''),
            hdurl=nasa_data.get('hdurl', ''),
            media_type=nasa_data.get('media_type', 'image'),
            copyright=nasa_data.get('copyright', ''),
        )

        serializer = APODImageSerializer(apod)
        logger.info(f"Fetched and cached APOD from NASA for {target_date}")

        return Response({
            'success': True,
            'data': serializer.data,
            'source': 'nasa_api'
        })


# ─── VIEW 4: SATELLITES LIST ──────────────────────────────────────────────────
class SatelliteListView(APIView):
    """
    GET /api/satellites/

    Returns all satellites in our database.

    Response JSON:
    {
        "success": true,
        "count": 1,
        "data": [
            {
                "id": 1,
                "name": "International Space Station",
                "norad_id": "25544",
                ...
            }
        ]
    }
    """

    def get(self, request):
        satellites = Satellite.objects.filter(is_active=True)
        serializer = SatelliteSerializer(satellites, many=True)
        return Response({
            'success': True,
            'count': satellites.count(),
            'data': serializer.data
        })


# ─── VIEW 5: ISS PASSES OVER A LOCATION ──────────────────────────────────────
class ISSPassesView(APIView):
    """
    GET /api/passes/?lat=28.61&lon=77.20&alt=220&n=5

    Fetches upcoming ISS pass times over the given location.
    Uses open-notify.org's ISS pass predictions endpoint.

    Query Parameters:
      lat  - Latitude of observer (required)
      lon  - Longitude of observer (required)
      alt  - Altitude of observer in meters (optional, default 0)
      n    - Number of passes to predict (optional, default 5, max 100)

    Response JSON:
    {
        "success": true,
        "location": { "latitude": 28.61, "longitude": 77.20 },
        "passes": [
            {
                "rise_time": "2024-01-16T03:45:00Z",
                "duration_seconds": 312,
                "duration_minutes": 5.2,
                "max_elevation": 67.4
            }
        ]
    }
    """

    def get(self, request):
        # Validate required parameters
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')

        if not lat or not lon:
            return Response(
                {'success': False, 'error': 'lat and lon query parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lon = float(lon)
            alt = float(request.query_params.get('alt', 0))
            n   = int(request.query_params.get('n', 5))
            n   = min(n, 10)   # API max is 100, but we limit to 10
        except ValueError:
            return Response(
                {'success': False, 'error': 'lat, lon, alt must be numbers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call open-notify ISS pass predictions API
        try:
            response = requests.get(
                f"{settings.ISS_API_BASE_URL}/iss-pass.json",
                params={'lat': lat, 'lon': lon, 'alt': alt, 'n': n},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get('message') != 'success':
                return Response(
                    {'success': False, 'error': 'ISS pass API returned an error'},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # Format the passes from Unix timestamps to readable ISO format
            passes = []
            for p in data.get('response', []):
                # fromtimestamp converts Unix timestamp to datetime
                rise_dt = datetime.fromtimestamp(p['risetime'], tz=timezone.utc)
                passes.append({
                    'rise_time': rise_dt.isoformat(),
                    'duration_seconds': p['duration'],
                    'duration_minutes': round(p['duration'] / 60, 1),
                })

            return Response({
                'success': True,
                'location': {'latitude': lat, 'longitude': lon},
                'passes': passes
            })

        except requests.RequestException as e:
            logger.error(f"ISS pass API error: {e}")
            return Response(
                {'success': False, 'error': 'Could not fetch ISS pass data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# ─── VIEW 6: ASTRONAUTS IN SPACE ──────────────────────────────────────────────
class AstronautsView(APIView):
    """
    GET /api/astronauts/

    Returns the list of people currently in space.
    Uses open-notify.org's astros endpoint.

    Response JSON:
    {
        "success": true,
        "number": 7,
        "people": [
            {"name": "Jasmin Moghbeli", "craft": "ISS"},
            {"name": "Andreas Mogensen", "craft": "ISS"},
            ...
        ]
    }
    """

    # cache_page(300) = Cache this response for 300 seconds (5 minutes)
    # No need to call NASA every single second for astronaut list — it rarely changes
    @method_decorator(cache_page(300))
    def get(self, request):
        try:
            response = requests.get(
                f"{settings.ISS_API_BASE_URL}/astros.json",
                timeout=8
            )
            response.raise_for_status()
            data = response.json()

            return Response({
                'success': True,
                'number': data.get('number', 0),
                'people': data.get('people', [])
            })

        except requests.RequestException as e:
            logger.error(f"Astronauts API error: {e}")
            return Response(
                {'success': False, 'error': 'Could not fetch astronaut data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# ─── VIEW 7: HEALTH CHECK ─────────────────────────────────────────────────────
@api_view(['GET'])
def health_check(request):
    """
    GET /api/health/

    Simple endpoint to verify the API is running.
    Railway and monitoring tools call this to confirm the app is alive.

    Response: { "status": "ok", "timestamp": "2024-01-15T14:32:00Z" }
    """
    return Response({
        'status': 'ok',
        'service': 'Orbit-Edu API',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
    })
