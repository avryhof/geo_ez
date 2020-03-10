import requests

from geo_ez.utility_functions import get_postal_code_by_coords


class IPGeoLocation:
    ip_address = None

    ip = None
    success = False
    type = "IPv4"
    continent = None
    continent_code = ("NA",)
    country = None
    country_code = None
    country_flag = None
    country_capital = None
    country_phone = None
    country_neighbours = None
    region = None
    city = None
    latitude = None
    longitude = None
    asn = None
    org = None
    isp = None
    timezone = None
    timezone_name = None
    timezone_dstOffset = None
    timezone_gmtOffset = None
    timezone_gmt = None
    currency = None
    currency_code = None
    currency_symbol = None
    currency_rates = None
    currency_plural = None
    completed_requests = None
    postal_code = None

    def __init__(self, request):
        self.ip_address = request.META.get("REMOTE_ADDR", False)

        x_real_ip = request.META.get("HTTP_X_REAL_IP", False)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", False)

        if x_real_ip:
            self.ip_address = x_real_ip
        elif x_forwarded_for:
            self.ip_address = x_forwarded_for

        resp = requests.get("http://free.ipwhois.io/json/%s" % self.ip_address)

        if resp.status_code == "200":
            for k, v in resp.json().items():
                setattr(self, k, v)

            if self.success:
                self.postal_code = get_postal_code_by_coords(self.latitude, self.longitude)

    @property
    def state(self):
        return self.region

    @property
    def zip_code(self):
        return self.postal_code.postal_code


class GeoLocation:
    country = None
    country_code = None
    country_flag = None
    region = None
    city = None
    latitude = None
    longitude = None
    postal_code = None

    def __init__(self, request):
        self.latitude = request.COOKIES.get("latitude", False)
        self.longitude = request.COOKIES.get("longitude", False)

        self.postal_code = get_postal_code_by_coords(self.latitude, self.longitude)

        self.country_code = self.postal_code.country_code
        self.country_flag = "https://cdn.ipwhois.io/flags/%s.svg" % self.country_code.lower
        self.region = self.postal_code.admin_code1
        self.city = self.postal_code.place_name

    @property
    def state(self):
        return self.region

    @property
    def zip_code(self):
        return self.postal_code.postal_code
