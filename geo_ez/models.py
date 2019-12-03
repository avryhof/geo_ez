from math import radians, cos, sin, asin, sqrt

from django.db import models
from django.db.models import DO_NOTHING, DateTimeField
from iso3166 import countries

from geo_ez.constants import ACCURACY_CHOICES
from geo_ez.us_census_class import USCensus
from geo_ez.usps_class import USPS


class GISPoint(models.Model):
    name = models.CharField(max_length=180, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s,%s" % (str(self.latitude), str(self.longitude))

    def distance_from(self, latitude, longitude, **kwargs):
        use_miles = kwargs.get("use_miles", True)
        distance_unit = float(3959 if use_miles else 6371)

        latitude1 = radians(float(latitude))
        latitude2 = radians(float(self.latitude))

        longitude1 = radians(float(longitude))
        longitude2 = radians(float(self.longitude))

        distance_longitude = longitude2 - longitude1
        distance_latitude = latitude2 - latitude1

        a = sin(distance_latitude / 2) ** 2 + cos(latitude1) * cos(latitude2) * sin(distance_longitude / 2) ** 2
        c = 2 * asin(sqrt(a))

        distance = c * distance_unit

        return distance

    def in_radius(self, latitude, longitude, radius, **kwargs):
        return self.distance_from(latitude, longitude, **kwargs) < radius


class CountryData(models.Model):
    iso = models.CharField(primary_key=True, max_length=2, null=False)  # iso country code, 2 characters
    iso3 = models.CharField(max_length=3, blank=True, null=True)  # iso country code, 3 characters
    iso_numeric = models.CharField(max_length=3, blank=True, null=True)  # iso numeric country code, 3 characters
    fips = models.CharField(max_length=5, blank=True, null=True)  # FIPS Code
    country = models.CharField(max_length=255, blank=True, null=True)
    capital = models.TextField(blank=True, null=True)
    area_km = models.BigIntegerField()
    population = models.BigIntegerField()
    continent = models.CharField(max_length=10, blank=True, null=True)
    tld = models.CharField(max_length=10, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_name = models.CharField(max_length=32, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    postal_code_format = models.CharField(max_length=32, blank=True, null=True)
    postal_code_ex = models.TextField(blank=True, null=True)
    languages = models.TextField(blank=True, null=True)
    geonameid = models.IntegerField()
    neighbors = models.TextField(blank=True, null=True)
    equivalent_fips_code = models.CharField(max_length=5, blank=True, null=True)  # FIPS Code


class PostalCode(GISPoint):
    country_code = models.CharField(max_length=2, blank=True, null=True)  # iso country code, 2 characters
    postal_code = models.CharField(max_length=20, blank=True, null=True)  # varchar(20)
    place_name = models.CharField(max_length=180, blank=True, null=True)  # varchar(180)
    admin_name1 = models.CharField(max_length=100, blank=True, null=True)  # 1. order subdivision (state) varchar(100)
    admin_code1 = models.CharField(max_length=20, blank=True, null=True)  # 1. order subdivision (state) varchar(20)
    admin_name2 = models.CharField(
        max_length=100, blank=True, null=True
    )  # 2. order subdivision (county/province) varchar(100)
    admin_code2 = models.CharField(
        max_length=20, blank=True, null=True
    )  # 2. order subdivision (county/province) varchar(20)
    admin_name3 = models.CharField(
        max_length=100, blank=True, null=True
    )  # 3. order subdivision (community) varchar(100)
    admin_code3 = models.CharField(max_length=20, blank=True, null=True)  # 3. order subdivision (community) varchar(20)
    accuracy = models.IntegerField(
        null=True, choices=ACCURACY_CHOICES
    )  # accuracy of lat/lng from 1=estimated, 4=geonameid, 6=centroid of addresses or shape
    updated = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.place_name

    @property
    def timezone(self):
        try:
            tz = TimeZoneMap.objects.get(zip_code=self.postal_code)
        except TimeZoneMap.DoesNotExist:
            tz = None

        return tz


class AbstractStreetAddress(GISPoint):
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=180, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    plus_four = models.CharField(max_length=20, blank=True, null=True)
    postal_code = models.ForeignKey(PostalCode, blank=True, null=True, on_delete=DO_NOTHING)
    validated = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def address(self):
        addr = self.address1

        if self.address2:
            addr = "%s, %s" % (self.address1, self.address2)

        return addr

    @property
    def timezone(self):
        try:
            tz = TimeZoneMap.objects.get(zip_code=self.zip_code)
        except TimeZoneMap.DoesNotExist:
            tz = None

        return tz

    def dict(self):
        return dict(
            address1=self.address1, address2=self.address2, city=self.city, state=self.state, zip_code=self.zip_code
        )

    def geocode(self, **kwargs):
        retn = False

        if self.latitude and self.longitude:
            retn = True

        else:
            valid_address = self.normalize()

            try:
                verified_address = VerifiedStreetAddress.objects.get(
                    address1__iexact=self.address1,
                    address2__iexact=self.address2,
                    city__iexact=self.city,
                    state__iexact=self.state,
                    zip_code=self.zip_code,
                    postal_code=self.postal_code,
                )

            except VerifiedStreetAddress.DoesNotExist:
                usc = USCensus()

                if valid_address:
                    if valid_address.get("address1") and valid_address.get("city") and valid_address.get("state"):
                        geocoded = usc.geocode(query=valid_address)
                        if geocoded:
                            retn = True
                            self.latitude = geocoded.get("latitude")
                            self.longitude = geocoded.get("longitude")
                            self.save()

            else:
                self.address1 = verified_address.address1
                self.address2 = verified_address.address2
                self.city = verified_address.city
                self.state = verified_address.state
                self.zip_code = verified_address.zip_code
                self.plus_four = verified_address.plus_four
                self.postal_code = verified_address.postal_code
                self.validated = verified_address.validated
                self.save()

        return retn

    def link_postal_code(self):
        retn = False
        try:
            self.postal_code = PostalCode.objects.get(postal_code=self.zip_code)

        except PostalCode.DoesNotExist:
            pass

        else:
            retn = True
            self.save()

        return retn

    def normalize(self):
        valid_address = dict(
            address1=self.address1,
            address2=self.address2,
            city=self.city,
            state=self.state,
            zip_code=self.zip_code,
            plus_four=self.plus_four,
        )

        if not self.validated:
            search_address = self.dict()
            ps = USPS()
            valid_address = ps.address(**search_address)

            if valid_address:
                self.address1 = valid_address.get("address1", self.address1)
                self.address2 = valid_address.get("address2", self.address2)
                self.city = valid_address.get("city", self.city)
                self.state = valid_address.get("state", self.state)
                self.zip_code = valid_address.get("zip_code", self.zip_code)
                self.plus_four = valid_address.get("plus_four", self.plus_four)
                self.validated = True
                self.save()

        return valid_address


class TimeZone(models.Model):
    country_code = models.CharField(max_length=2, blank=True, null=True)  # iso country code, 2 characters
    timezone_id = models.TextField(primary_key=True, null=False)
    gmt_offset_jan = models.FloatField(null=True)
    gmt_offset_jul = models.FloatField(null=True)
    raw_offset = models.FloatField(null=True)

    @property
    def country(self):
        try:
            country = CountryData.objects.get(iso=self.country_code.upper())
        except CountryData.DoesNotExist:
            iso_country = countries.get(self.country_code.lower())
            country = CountryData.objects.create(
                iso=iso_country.alpha2,
                iso3=iso_country.alpha3,
                iso_numeric=iso_country.numeric,
                country=iso_country.name,
            )

        return country


class TimeZoneMap(models.Model):
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    time_zone = models.ForeignKey(TimeZone, null=True, on_delete=DO_NOTHING)


class VerifiedStreetAddress(AbstractStreetAddress):
    updated = DateTimeField(auto_now_add=True)
