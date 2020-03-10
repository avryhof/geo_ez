import logging

from django.utils.deprecation import MiddlewareMixin  # noqa: E501 pylint: disable=import-error

from geo_ez.ip_geolocation_class import IPGeoLocation, GeoLocation


class GeolocationMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):  # noqa: D107
        self._geolocation_data = None
        super(GeolocationMiddleware, self).__init__(get_response)

    def process_request(self, request):
        """Process the request."""
        # noinspection PyBroadException
        try:
            self._get_geolocation(request)
            request.geolocation = self._geolocation_data
        except Exception:
            logging.error("Couldn't geolocate ip", exc_info=True)

    def process_response(self, request, response):
        """Process the response."""
        # noinspection PyBroadException
        try:
            if self._geolocation_data is None:
                self._get_geolocation(request)

            response["geolocation"] = self._geolocation_data

        except Exception:
            logging.error("Couldn't geolocate ip", exc_info=True)

        return response

    def _get_geolocation(self, request):
        latitude = request.COOKIES.get("latitude", False)
        longitude = request.COOKIES.get("longitude", False)
        if latitude and longitude:
            self._geolocation_data = GeoLocation(request)
        else:
            self._geolocation_data = IPGeoLocation(request)
